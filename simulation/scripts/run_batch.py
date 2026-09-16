"""
simulation/scripts/run_batch.py

Runs ONE G4 simulation (one E0) end-to-end:
  1. invoke fastshower_g4 binary
  2. convert .g4bin -> .npz via convert_to_npz.py (z converted to X0 units)
  3. delete raw .g4bin to save scratch space

Called by slurm/g4_batch.sbatch once per SLURM array task.
Can also be run manually: python run_batch.py --energy 100 [...]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# allow importing from repo root (for convert_to_npz -> interface.io)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from simulation.scripts.convert_to_npz import convert


def _x0_cm(config_path: Path) -> float:
    with open(config_path) as f:
        return json.load(f)["geometry"]["X0_cm"]


def run_one_energy(energy_mev: float, config_path: Path, binary_path: Path,
                    rawdir: Path, outdir: Path,
                    keep_raw: bool = False, seed: int = None) -> Path:
    rawdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    raw_path = rawdir / f"shower_E{energy_mev:g}.g4bin"
    npz_path = outdir / f"shower_E{energy_mev:g}.npz"

    cmd = [str(binary_path), "--config", str(config_path),
           "--energy", str(energy_mev), "--output", str(raw_path)]
    if seed is not None:
        cmd += ["--seed", str(seed)]

    print(f"[run_batch] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"fastshower_g4 failed for E0={energy_mev} (exit {result.returncode})")

    convert(raw_path, npz_path, _x0_cm(config_path))

    if not keep_raw:
        raw_path.unlink()

    return npz_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--energy",   required=True, type=float)
    parser.add_argument("--config",   required=True, type=Path)
    parser.add_argument("--binary",   required=True, type=Path)
    parser.add_argument("--rawdir",   required=True, type=Path)
    parser.add_argument("--outdir",   required=True, type=Path)
    parser.add_argument("--keep-raw", action="store_true")
    parser.add_argument("--seed",     type=int, default=None)
    args = parser.parse_args()

    run_one_energy(args.energy, args.config, args.binary,
                    args.rawdir, args.outdir, args.keep_raw, args.seed)
