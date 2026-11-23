#!/usr/bin/env bash
set -euo pipefail
source /workspace/openems-install/venv/bin/activate
export CMAKE_PREFIX_PATH=/workspace/openems-deps/usr
export HDF5_ROOT=/workspace/openems-deps/usr
export CPATH=/workspace/openems-deps/usr/include:/workspace/openems-deps/usr/include/hdf5/serial
export LIBRARY_PATH=/workspace/openems-deps/usr/lib/x86_64-linux-gnu:/workspace/openems-deps/usr/lib/x86_64-linux-gnu/hdf5/serial
export LD_LIBRARY_PATH=/workspace/openems-install/lib:/workspace/openems-deps/usr/lib/x86_64-linux-gnu
export CMAKE_BUILD_PARALLEL_LEVEL=2
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
cd /workspace/openems-source
exec timeout --signal=TERM --kill-after=15s 1200s taskset -c 0,1 ./update_openEMS.sh /workspace/openems-install --disable-GUI --python --njobs=2 --skip-dep-check --python-venv-mode=disable --python-use-network=disable
