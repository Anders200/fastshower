"""
simulation/scripts/convert_to_npz.py

Converts G4's raw .g4bin output into the project's .npz schema
(interface/io.py). This is the ONLY place raw G4 numbers become
official project units:

    r    : cm          (unchanged, G4 native)
    z    : X0 units    (divided by X0_cm here -- matches interface/io.py contract)
    dEdV : MeV/cm^3    (edep_sum / bin_volume_cm3 / n_events)

Do not change any of the above without updating interface/io.py at the same
time, and telling your colleague.
"""

import argparse
import struct
import json
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
from interface.io import save_run


def read_g4bin(path: Path) -> dict:
    with open(path, "rb") as f:
        nR, nZ = struct.unpack("<ii", f.read(8))
        radius_cm, depth_cm, E0_MeV = struct.unpack("<ddd", f.read(24))
        (n_events,) = struct.unpack("<q", f.read(8))
        r_edges = np.frombuffer(f.read(8*(nR+1)), dtype="<f8").copy()
        z_edges = np.frombuffer(f.read(8*(nZ+1)), dtype="<f8").copy()
        edep_sum = np.frombuffer(f.read(8*nR*nZ), dtype="<f8").copy().reshape(nR, nZ)
        particle = f.read(64).rstrip(b"\x00").decode()
        material = f.read(64).rstrip(b"\x00").decode()
    return dict(nR=nR, nZ=nZ, radius_cm=radius_cm, depth_cm=depth_cm,
                E0_MeV=E0_MeV, n_events=n_events,
                r_edges=r_edges, z_edges=z_edges, edep_sum=edep_sum,
                particle=particle, material=material)


def bin_centers_and_volumes(r_edges, z_edges):
    """
    Area-weighted r centers and physical bin volumes (cm^3).
    z_edges must be in cm here -- volume must use physical units.
    """
    r0, r1 = r_edges[:-1], r_edges[1:]
    r_centers = (2/3) * (r1**3 - r0**3) / (r1**2 - r0**2)

    z0, z1 = z_edges[:-1], z_edges[1:]
    z_centers_cm = 0.5 * (z0 + z1)
    dz = z1 - z0

    volume = np.pi * (r1**2 - r0**2)[:, None] * dz[None, :]  # (nR, nZ), cm^3
    return r_centers, z_centers_cm, volume


def convert(input_path: Path, output_path: Path, x0_cm: float):
    raw = read_g4bin(input_path)

    r_centers, z_centers_cm, volume = bin_centers_and_volumes(
        raw["r_edges"], raw["z_edges"])

    dEdV = raw["edep_sum"] / volume / raw["n_events"]  # MeV/cm^3

    # Sanity check: containment
    total = raw["edep_sum"].sum() / raw["n_events"]
    containment = total / raw["E0_MeV"]
    print(f"[convert] E0={raw['E0_MeV']} MeV  deposited={total:.2f} MeV  "
          f"containment={containment:.1%}  n_events={raw['n_events']}")
    if containment > 1.05:
        print("  WARNING: deposited > E0 by >5% -- check binning/units")
    if containment < 0.5:
        print("  WARNING: containment <50% -- consider larger detector")

    # z: cm -> radiation lengths (X0) to match interface/io.py contract
    z_centers_X0 = z_centers_cm / x0_cm

    # Use save_run from interface/io.py -- never call np.savez directly
    save_run(output_path, r_centers, z_centers_X0, dEdV, raw["E0_MeV"])
    print(f"[convert] wrote {output_path}  (z in X0 units, X0={x0_cm} cm)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",   required=True, type=Path)
    parser.add_argument("--output",  required=True, type=Path)
    parser.add_argument("--config",  required=True, type=Path,
                         help="Path to run_config.json (reads geometry.X0_cm)")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)
    x0_cm = cfg["geometry"]["X0_cm"]

    convert(args.input, args.output, x0_cm)
