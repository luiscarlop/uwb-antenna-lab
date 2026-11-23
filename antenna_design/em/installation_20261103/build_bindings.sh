#!/usr/bin/env bash
set -euo pipefail
source /workspace/openems-install/venv/bin/activate
export CC=gcc
export CXX=g++
export CPATH=/workspace/openems-deps/usr/include:/workspace/openems-deps/usr/include/hdf5/serial
export LIBRARY_PATH=/workspace/openems-deps/usr/lib/x86_64-linux-gnu:/workspace/openems-deps/usr/lib/x86_64-linux-gnu/hdf5/serial
export LD_LIBRARY_PATH=/workspace/openems-install/lib:/workspace/openems-deps/usr/lib/x86_64-linux-gnu
export CMAKE_BUILD_PARALLEL_LEVEL=2
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
cd /workspace/openems-source
exec timeout --signal=TERM --kill-after=15s 900s taskset -c 0,1 ./scripts/build_python.sh --cpp-install-dir /workspace/openems-install --python-venv-mode=disable --python-use-network=disable
