from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _save_fig(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_loss_components(history: dict, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Total loss (log scale)
    fig, ax = plt.subplots()
    ax.plot(history["epoch"], history["loss_total"], color="black")
    ax.set_yscale("log")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Total Loss")
    ax.set_title("Total Loss over Training")
    _save_fig(fig, output_dir / "loss_total.png")

    # Data loss
    fig, ax = plt.subplots()
    ax.plot(history["epoch"], history["loss_data"], color="blue")
    ax.set_yscale("log")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Data MSE")
    ax.set_title("Data Loss over Training")
    _save_fig(fig, output_dir / "loss_data.png")

    # PDE loss
    fig, ax = plt.subplots()
    ax.plot(history["epoch"], history["loss_pde"], color="red")
    ax.set_yscale("log")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("PDE Residual")
    ax.set_title("Physics (PDE) Loss over Training")
    _save_fig(fig, output_dir / "loss_pde.png")

    # Energy conservation loss
    fig, ax = plt.subplots()
    ax.plot(history["epoch"], history["loss_energy"], color="green")
    ax.set_yscale("log")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Energy Conservation Loss")
    ax.set_title("Energy Conservation Loss over Training")
    _save_fig(fig, output_dir / "loss_energy.png")


def plot_params(history: dict, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots()
    ax.plot(history["epoch"], history["param_a"], label="a", color="purple")
    ax.plot(history["epoch"], history["param_b"], label="b", color="orange")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Parameter Value")
    ax.set_title("Learned Physics Parameters over Training")
    ax.legend()
    _save_fig(fig, output_dir / "params_ab.png")
