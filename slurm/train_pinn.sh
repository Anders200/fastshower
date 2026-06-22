#!/bin/bash
#SBATCH --account=plgmsc26-gpu
#SBATCH --job-name=fastshower_pinn
#SBATCH --output=/net/afscra/people/plgnaworyta/fastshower/logs/pinn_%j.out
#SBATCH --error=/net/afscra/people/plgnaworyta/fastshower/logs/pinn_%j.err
#SBATCH --partition=plgrid-gpu-v100
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="/net/afscra/people/plgnaworyta"
DATA_DIR="${SCRATCH}/fastshower/processed"

module purge
module load python/3.13.5-gcccore-14.3.0
module load pytorch
source "${REPO_ROOT}/venv/bin/activate"

echo "[pinn] training on data from ${DATA_DIR}"
echo "[pinn] GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unknown')"

python3 -m pinn.train --data-dir "${DATA_DIR}"

echo "[pinn] done"
