#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import torch

from interface import config
from pinn.model import EnergyDepositionPINN


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate the trained PINN on the calorimeter geometry and plot the energy deposition."
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("output/pinn_detector_model.pt"),
        help="Path to the trained model checkpoint.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where the heatmap and raw grid will be written.",
    )
    parser.add_argument(
        "--e0",
        type=float,
        default=100.0,
        help="Primary particle energy in MeV used for the inference grid.",
    )
    parser.add_argument(
        "--r-points",
        type=int,
        default=200,
        help="Number of radial grid points.",
    )
    parser.add_argument(
        "--z-points",
        type=int,
        default=200,
        help="Number of longitudinal grid points.",
    )
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=64,
        help="Hidden layer width used by the trained PINN.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=4,
        help="Number of hidden layers used by the trained PINN.",
    )
    return parser


def load_model(checkpoint: Path, device: torch.device, hidden_dim: int, depth: int) -> EnergyDepositionPINN:
    if not checkpoint.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint}. Train the model first or pass --checkpoint."
        )

    model = EnergyDepositionPINN(hidden_dim=hidden_dim, depth=depth).to(device)
    state_dict = torch.load(checkpoint, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def infer_grid(model: EnergyDepositionPINN, e0: float, r_points: int, z_points: int, device: torch.device):
    r_values = np.linspace(0.0, config.R_MAX, r_points)
    z_values = np.linspace(0.0, config.Z_MAX, z_points)
    r_mesh, z_mesh = np.meshgrid(r_values, z_values)

    r_tensor = torch.tensor(r_mesh.ravel(), dtype=torch.float32, device=device).view(-1, 1)
    z_tensor = torch.tensor(z_mesh.ravel(), dtype=torch.float32, device=device).view(-1, 1)
    e0_tensor = torch.full_like(r_tensor, e0)

    with torch.no_grad():
        predictions = model(r_tensor, z_tensor, e0_tensor)

    return r_values, z_values, predictions.cpu().numpy().reshape(z_points, r_points)


def plot_heatmap(r_values: np.ndarray, z_values: np.ndarray, values: np.ndarray, e0: float, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    positive_values = np.clip(values, 1e-8, None)
    image = ax.imshow(
        positive_values.T,
        origin="lower",
        extent=[z_values.min(), z_values.max(), r_values.min(), r_values.max()],
        aspect="auto",
        cmap="virdis",
        norm=LogNorm(vmin=positive_values.min(), vmax=positive_values.max()),
    )

    ax.set_xlabel("z [X0]")
    ax.set_ylabel("r [cm]")
    ax.set_title(f"Predicted energy deposition in calorimeter geometry at E0 = {e0:.1f} MeV")
    fig.colorbar(image, ax=ax, label="dE/dV")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not (config.E0_MIN <= args.e0 <= config.E0_MAX):
        raise ValueError(
            f"--e0 must be within [{config.E0_MIN}, {config.E0_MAX}] MeV, got {args.e0}."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(args.checkpoint, device=device, hidden_dim=args.hidden_dim, depth=args.depth)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    r_values, z_values, grid = infer_grid(model, args.e0, args.r_points, args.z_points, device)

    heatmap_path = args.output_dir / f"energy_heatmap_E0_{args.e0:.1f}.png"
    plot_heatmap(r_values, z_values, grid, args.e0, heatmap_path)

    print(f"Saved heatmap to {heatmap_path}")


if __name__ == "__main__":
    main()