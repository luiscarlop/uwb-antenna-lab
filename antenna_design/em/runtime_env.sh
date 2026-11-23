#!/usr/bin/env bash
# Source this file; the prefix is outside the research repository.
OPENEMS_USER_PREFIX=${OPENEMS_USER_PREFIX:-/workspace/openems-install}
OPENEMS_DEPS_PREFIX=${OPENEMS_DEPS_PREFIX:-/workspace/openems-deps}
source "$OPENEMS_USER_PREFIX/venv/bin/activate"
export LD_LIBRARY_PATH="$OPENEMS_USER_PREFIX/lib:$OPENEMS_DEPS_PREFIX/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export MPLBACKEND=Agg
