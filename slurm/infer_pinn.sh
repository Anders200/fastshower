#!/bin/bash
#SBATCH --account=plgmsc26-gpu
#SBATCH --job-name=fastshower_pinn_infer
#SBATCH --output=logs/infer_%j.out
#SBATCH --error=logs/infer_%j.err
#SBATCH --partition=plgrid-gpu-v100
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:05:00

set -euo pipefail

REPO_ROOT="$(cd "${SLURM_SUBMIT_DIR:-$(pwd)}" && pwd)"
DATA_DIR="${SCRATCH}/fastshower/processed"

mkdir -p "${REPO_ROOT}/logs"

module purge
module load pytorch
module load matplotlib/3.0.3-foss-2021a-python-3.9.5

echo "[pinn] training on data from ${DATA_DIR}"
echo "[pinn] GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unknown')"
echo "[pinn] Python: $(python3 -V)"

python3 -m pinn.infer.py --data-dir "${DATA_DIR}" 

echo "[pinn] done"
