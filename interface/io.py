# interface/io.py
"""
I/O contract between simulation/ and pinn/.

Conventions:
    r     : cm, bin centers, r >= 0
    z     : radiation lengths (X0), bin centers, z >= 0
    E0    : MeV, incident particle energy
    dEdV  : MeV/cm^3, mean energy deposition averaged over n_events showers

Both sides import ONLY from here — never touch np.savez directly.
"""

import numpy as np
from pathlib import Path


def save_run(path: Path, r: np.ndarray, z: np.ndarray, dEdV: np.ndarray, E0: float):
    """
    Save one G4 run (single E0) to disk.

    r     : (Nr,)        bin centers, cm
    z     : (Nz,)        bin centers, radiation lengths
    dEdV  : (Nr, Nz)     mean energy deposition, MeV/cm^3
    E0    : scalar       incident energy, MeV
    """
    np.savez(path, r=r, z=z, dEdV=dEdV, E0=E0)


def load_dataset(data_dir: Path) -> dict:
    """
    Load and concatenate all runs in a directory into flat training arrays.

    Returns dict of flat (N,) arrays:
        r, z, E0, dEdV
    """
    files = sorted(Path(data_dir).glob("*.npz"))
    r_list, z_list, E0_list, dEdV_list = [], [], [], []

    for f in files:
        d = np.load(f)
        r_grid, z_grid = np.meshgrid(d["r"], d["z"], indexing="ij")

        r_list.append(r_grid.ravel())
        z_list.append(z_grid.ravel())
        dEdV_list.append(d["dEdV"].ravel())
        E0_list.append(np.full(r_grid.size, d["E0"]))

    return {
        "r":    np.concatenate(r_list),
        "z":    np.concatenate(z_list),
        "E0":   np.concatenate(E0_list),
        "dEdV": np.concatenate(dEdV_list),
    }
