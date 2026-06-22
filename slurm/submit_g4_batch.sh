#!/bin/bash
# THE ONE COMMAND TO RUN for a full sweep.
# Reads energies_MeV from run_config.json, sizes the SLURM array automatically.
# Add/remove energies in run_config.json -> re-run this script -> done.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${REPO_ROOT}/simulation/geant4/config/run_config.json"

N=$(python3 -c "import json; cfg=json.load(open('${CONFIG}')); print(len(cfg['energies_MeV']))")
echo "[submit] ${N} energies -> array 0-$((N-1))"

mkdir -p "${REPO_ROOT}/slurm/logs"
sbatch --array="0-$((N-1))" "${REPO_ROOT}/slurm/g4.sh"
