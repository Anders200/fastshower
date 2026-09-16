#!/bin/bash
# Build the fastshower_g4 binary. Run once before submitting SLURM jobs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j"$(nproc)"
echo ""
echo "Built: $(pwd)/fastshower_g4"
echo "Test: ./fastshower_g4 --config ../config/run_config.json --energy 100 --output /tmp/test.g4bin"
