# pinn/train.py
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from interface.g4_surrogate import G4Surrogate
from interface import config
from pinn.model import EnergyDepositionPINN
from pinn.physics import PhysicsLossEvaluator

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Uruchamianie treningu na: {device}")

    # 1. Inicjalizacja modeli
    model = EnergyDepositionPINN(hidden_dim=128, depth=4).to(device)
    physics_evaluator = PhysicsLossEvaluator().to(device)
    
    # Podpięcie PINNa pod interfejs surogatu G4
    surrogate = G4Surrogate(model=model)
    
    # 2. Ładowanie danych treningowych z Geant4 (Data Loss)
    data_dir = Path("data")
    if not data_dir.exists():
        raise FileNotFoundError("Utwórz katalog 'data' i umieść w nim pliki .npz z symulacji!")
        
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

    print("Rozpoczęcie asymilacji danych z regularyzacją fizyczną...")
    
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()

        # ---- A. LOSS Z DANYCH ----
        r_data.requires_grad_(True)
        z_data.requires_grad_(True)
        
        pred_dedv = model(r_data, z_data, E0_data)
        loss_data = torch.mean((pred_dedv - dedv_data) ** 2)

        # ---- B. LOSS Z PDE ----
        pde_res = physics_evaluator.compute_pde_residual(model, r_data, z_data, E0_data)
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
        history["history_pde" if "history_pde" in history else "loss_pde"].append(loss_pde.item())
        history["loss_energy"].append(loss_energy.item())
        history["param_a"].append(physics_evaluator.param_a.item())
        history["param_b"].append(physics_evaluator.param_b.item())

        # Logowanie postępów w konsoli
        if epoch % 200 == 0 or epoch == 1:
            print(
                f"Epoka {epoch:4d}/{epochs} | "
                f"Loss: {total_loss.item():.4e} | "
                f"Data MSE: {loss_data.item():.4e} | "
                f"PDE Res: {loss_pde.item():.4e} | "
                f"Energy Res: {loss_energy.item():.4e} | "
                f"a: {physics_evaluator.param_a.item():.3f} b: {physics_evaluator.param_b.item():.3f}"
            )

    # Zapisz wytrenowany model
    torch.save(model.state_dict(), "pinn_detector_model.pt")
    print("Trening zakończony! Model zapisano.")

    # --- GENEROWANIE WYKRESÓW (Dokładnie tak jak w przesłanym notatniku) ---
    print("Generowanie wykresów diagnostycznych...")
    
    plt.figure(figsize=(14, 5))

    # Wykres 1: Historia Funkcji Strat (w skali logarytmicznej)
    plt.subplot(1, 2, 1)
    plt.plot(history["epoch"], history["loss_total"], label="Total Loss", color="black", alpha=0.7)
    plt.plot(history["epoch"], history["loss_data"], label="Data Loss (G4 MSE)", color="blue", linestyle="--")
    plt.plot(history["epoch"], history["loss_pde"], label="Physics Loss (PDE)", color="red", linestyle=":")
    plt.plot(history["epoch"], history["loss_energy"], label="Energy Conservation Loss", color="green", linestyle="-.")
    plt.yscale("log")
    plt.xlabel("Epoka")
    plt.ylabel("Wartość Loss")
    plt.title("Historia zbieżności funkcji strat (Inverse PINN)")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend()

    # Wykres 2: Ewolucja uczonych parametrów fizycznych kaskady (a, b)
    plt.subplot(1, 2, 2)
    plt.plot(history["epoch"], history["param_a"], label="Wyestymowane 'a'", color="purple")
    plt.plot(history["epoch"], history["param_b"], label="Wyestymowane 'b'", color="orange")
    # Linia odniesienia dla teoretycznego b ~ 0.5
    plt.axhline(y=0.5, color="gray", linestyle="--", label="Teoretyczne b (Rossi)")
    plt.xlabel("Epoka")
    plt.ylabel("Wartość parametru")
    plt.title("Ewolucja parametrów kaskady Rossiego w czasie")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    plt.tight_layout()
    
    # Zapisujemy wykres do pliku graficznego, ponieważ uruchamiamy to jako skrypt .py
    plt.savefig("pinn_training_history.png", dpi=300)
    print("Wykresy zostały zapisane do pliku: pinn_training_history.png")
    plt.show()

if __name__ == "__main__":
    train()