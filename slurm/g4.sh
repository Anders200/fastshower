#!/bin/bash
#SBATCH --account=plgmsc26-cpu
#SBATCH --job-name=fastshower_g4
#SBATCH --output=logs/g4_%j.out
#SBATCH --error=logs/g4_%j.err
#SBATCH --partition=plgrid-now
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00

# This script runs the full energy sweep serially inside one batch job.

set -euo pipefail

# ---- Repo root (robust for SLURM batch jobs) ----
REPO_ROOT="$(cd "${SLURM_SUBMIT_DIR:-$(pwd)}" && pwd)"

# ---- Paths ----
CONFIG="${REPO_ROOT}/simulation/geant4/config/run_config.json"
BINARY="${REPO_ROOT}/simulation/geant4/build/fastshower_g4"

RAWDIR="${SCRATCH}/fastshower/raw"
OUTDIR="${SCRATCH}/fastshower/processed"
LOGDIR="${REPO_ROOT}/logs"

mkdir -p "${RAWDIR}" "${OUTDIR}" "${LOGDIR}"

# ---- Modules ----
module purge
module load geant4/11.2.0-gcc-11.3.0
module load python/3.13.5-gcccore-14.3.0

# ---- venv ----
source "${REPO_ROOT}/venv/bin/activate"

# ---- Get energies from config ----
mapfile -t ENERGIES < <(python3 - <<EOF
import json
with open("${CONFIG}") as f:
    cfg = json.load(f)
for energy in cfg["energies_MeV"]:
    print(energy)
EOF
)

echo "[g4_batch] running ${#ENERGIES[@]} energies serially"

for index in "${!ENERGIES[@]}"; do
    ENERGY="${ENERGIES[$index]}"
    echo "[g4_batch] run $((index + 1))/${#ENERGIES[@]} -> E0=${ENERGY} MeV"

    python3 "${REPO_ROOT}/simulation/scripts/run_batch.py" \
        --energy "${ENERGY}" \
        --config  "${CONFIG}" \
        --binary  "${BINARY}" \
        --rawdir  "${RAWDIR}" \
        --outdir  "${OUTDIR}"
done

echo "[g4_batch] done"
