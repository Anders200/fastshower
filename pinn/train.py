# pinn/train.py
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np

from interface.g4_surrogate import G4Surrogate
from interface import config
from pinn.model import EnergyDepositionPINN
from pinn.physics import PhysicsLossEvaluator
from pinn.plotting import plot_loss_components, plot_params

def train(data_dir: Path, output_dir: Path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Starting training on: {device}")

    # 1. Inicjalizacja modeli
    model = EnergyDepositionPINN(hidden_dim=64, depth=4).to(device)
    physics_evaluator = PhysicsLossEvaluator().to(device)
    
    # Podpięcie PINNa pod interfejs surogatu G4
    surrogate = G4Surrogate(model=model)
    
    # 2. Load training data from Geant4 (Data Loss)
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError("Create the 'data' directory and place .npz simulation files there.")

    g4_data = surrogate.get_training_points(data_dir)
    
    # Konwersja danych Geant4 na tensory PyTorch
    r_data = torch.tensor(g4_data["r"], dtype=torch.float32, device=device).view(-1, 1)
    z_data = torch.tensor(g4_data["z"], dtype=torch.float32, device=device).view(-1, 1)
    E0_data = torch.tensor(g4_data["E0"], dtype=torch.float32, device=device).view(-1, 1)
    dedv_data = torch.tensor(g4_data["dEdV"], dtype=torch.float32, device=device).view(-1, 1)

    # 3. Definicja optymalizatora
    optimizer = torch.optim.Adam(
        list(model.parameters()) + list(physics_evaluator.parameters()), 
        lr=1e-3
    )

    epochs = 5000
    w_data = 1.0
    w_energy = 0.1
    w_pde = 1e-4

    # --- HISTORIA TRENINGU (Tablice na wzór notatnika z zajęć) ---
    history = {
        "epoch": [],
        "loss_total": [],
        "loss_data": [],
        "loss_pde": [],
        "loss_energy": [],
        "param_a": [],
        "param_b": []
    }

    print("Starting training with physics regularization...")
    
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()

        # ---- A. LOSS Z DANYCH ----
        pred_dedv = model(r_data, z_data, E0_data)
        loss_data = torch.mean((pred_dedv - dedv_data) ** 2)

        # ---- B. LOSS Z PDE ----
        # PDE residual is evaluated on COLLOCATION POINTS sampled across the
        # domain -- NOT on the G4 data points. This is the whole point of a
        # PINN: enforce physics between the data points, not only where we
        # already have ground truth. Gaussian-biased sampling concentrates
        # points near the shower core where gradients are steepest.
        n_coll = 2000
        r_coll_np = np.abs(np.random.normal(0, config.R_MAX * 0.15, n_coll))
        r_coll_np = np.clip(r_coll_np, 0, config.R_MAX)
        z_coll_np = np.random.normal(config.Z_MAX * 0.4, config.Z_MAX * 0.25, n_coll)
        z_coll_np = np.clip(z_coll_np, 1e-3, config.Z_MAX)
        E0_coll_np = np.random.uniform(config.E0_MIN, config.E0_MAX, n_coll)

        r_coll = torch.tensor(r_coll_np, dtype=torch.float32, device=device).view(-1, 1).requires_grad_(True)
        z_coll = torch.tensor(z_coll_np, dtype=torch.float32, device=device).view(-1, 1).requires_grad_(True)
        E0_coll = torch.tensor(E0_coll_np, dtype=torch.float32, device=device).view(-1, 1)

        pde_res = physics_evaluator.compute_pde_residual(model, r_coll, z_coll, E0_coll)
        loss_pde = torch.mean(pde_res ** 2)

        # ---- C. LOSS Z ZACHOWANIA ENERGII ----
        sample_E0_val = np.random.uniform(config.E0_MIN, config.E0_MAX)
        
        num_r, num_z = 50, 50
        r_lin = np.linspace(0, config.R_MAX, num_r)
        z_lin = np.linspace(0, config.Z_MAX, num_z)
        dr = config.R_MAX / num_r
        dz = config.Z_MAX / num_z
        
        r_mesh, z_mesh = np.meshgrid(r_lin, z_lin)
        r_flat = torch.tensor(r_mesh.ravel(), dtype=torch.float32, device=device).view(-1, 1)
        z_flat = torch.tensor(z_mesh.ravel(), dtype=torch.float32, device=device).view(-1, 1)
        E0_flat = torch.full_like(r_flat, sample_E0_val)
        
        u_mesh = model(r_flat, z_flat, E0_flat)
        integral_elements = u_mesh * (2 * np.pi * r_flat) * dr * dz
        total_predicted_energy = torch.sum(integral_elements)
        
        loss_energy = (total_predicted_energy - sample_E0_val) ** 2

        # ---- TOTAL LOSS ----
        total_loss = w_data * loss_data + w_pde * loss_pde + w_energy * loss_energy

        total_loss.backward()
        optimizer.step()

        # Zapisywanie historii co epokę (lub co kilka, dla oszczędności pamięci - tu robimy co epokę)
        history["epoch"].append(epoch)
        history["loss_total"].append(total_loss.item())
        history["loss_data"].append(loss_data.item())
        history["loss_pde"].append(loss_pde.item())
        history["loss_energy"].append(loss_energy.item())
        history["param_a"].append(physics_evaluator.param_a.item())
        history["param_b"].append(physics_evaluator.param_b.item())

        # Logging progress to console
        if epoch % 200 == 0 or epoch == 1:
            print(
                f"Epoch {epoch:4d}/{epochs} | "
                f"Loss: {total_loss.item():.4e} | "
                f"Data MSE: {loss_data.item():.4e} | "
                f"PDE Res: {loss_pde.item():.4e} | "
                f"Energy Res: {loss_energy.item():.4e} | "
                f"a: {physics_evaluator.param_a.item():.3f} b: {physics_evaluator.param_b.item():.3f}"
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Save trained model
    torch.save(model.state_dict(), output_dir / "pinn_detector_model.pt")
    print("Training finished. Model saved.")

    # --- Generate diagnostic plots ---
    print("Generating diagnostic plots...")
    plot_loss_components(history, output_dir)
    plot_params(history, output_dir)

def _build_argparser():
    p = argparse.ArgumentParser(description="Train the PINN model")
    p.add_argument("--data-dir", type=Path, default=Path("data"), help="Directory with .npz training runs")
    p.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory to write models and plots")
    return p


if __name__ == "__main__":
    parser = _build_argparser()
    args = parser.parse_args()
    train(args.data_dir, args.output_dir)