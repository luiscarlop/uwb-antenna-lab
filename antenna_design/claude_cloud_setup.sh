#!/bin/bash
# Setup script for the Claude Code cloud environment "TFG antenas CH9".
# Paste this into the environment's "Setup script" field. It runs as root
# before the session starts and its result is cached with the environment.
#
# Builds openEMS/CSXCAD from the same pinned official sources Codex used
# (antenna_design/reports/solver_installation.md), headless, into the same
# prefixes, so `source antenna_design/em/runtime_env.sh` works unchanged.
# Never fails hard: a missing solver is logged and the agents mark EM_NOT_RUN.
set -u
LOG=/workspace/openems-setup.log
mkdir -p /workspace
exec > >(tee -a "$LOG") 2>&1

PROJECT_REV=fc5a90b906af01c4d35797fc95751386c8e2ede5
SRC=/workspace/openems-source
PREFIX=/workspace/openems-install
DEPS=/workspace/openems-deps
REPO_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ ! -d "$REPO_DIR/antenna_design" ]; then
  FOUND=$(find / -maxdepth 4 -type d -name antenna_design -path '*TFG_Beamforming_FBD*' 2>/dev/null | head -1)
  [ -n "$FOUND" ] && REPO_DIR=$(dirname "$FOUND")
fi
echo "repo: $REPO_DIR"
REQ="$REPO_DIR/antenna_design/em/installation_20261103/bootstrap_requirements.txt"

echo "== $(date -u) setup start"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq || true
apt-get install -y -qq --no-install-recommends \
  build-essential cmake git ca-certificates pkg-config \
  libboost-thread-dev libboost-system-dev libboost-date-time-dev \
  libboost-serialization-dev libboost-chrono-dev libboost-program-options-dev \
  libhdf5-dev libtinyxml-dev python3-venv python3-dev \
  || echo "WARN: apt dependencies incomplete"

# runtime_env.sh expects the deps under $DEPS/usr: point it at the system /usr.
mkdir -p "$DEPS" && ln -sfn /usr "$DEPS/usr"

if [ ! -x "$PREFIX/bin/openEMS" ]; then
  echo "== clone openEMS-Project @ $PROJECT_REV"
  [ -d "$SRC/.git" ] || git clone -q https://github.com/thliebig/openEMS-Project.git "$SRC"
  git -C "$SRC" fetch -q origin "$PROJECT_REV" || true
  git -C "$SRC" checkout -q "$PROJECT_REV" \
    && git -C "$SRC" submodule update -q --init --recursive \
    || echo "WARN: could not check out the pinned revision"

  echo "== python venv"
  python3 -m venv "$PREFIX/venv"
  "$PREFIX/venv/bin/python" -m pip install -q --upgrade pip
  "$PREFIX/venv/bin/python" -m pip install -q --only-binary=:all: -r "$REQ" \
    || "$PREFIX/venv/bin/python" -m pip install -q numpy h5py matplotlib Cython setuptools setuptools-scm wheel \
    || echo "WARN: python build dependencies incomplete"

  echo "== build (headless, with Python bindings)"
  (
    source "$PREFIX/venv/bin/activate"
    export CC=gcc CXX=g++
    export HDF5_ROOT=/usr CPATH=/usr/include/hdf5/serial LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/hdf5/serial
    export LD_LIBRARY_PATH="$PREFIX/lib"
    cd "$SRC" && timeout 2400s ./update_openEMS.sh "$PREFIX" --disable-GUI --python \
      --njobs="$(nproc)" --python-venv-mode=disable --python-use-network=disable
  ) || echo "WARN: openEMS build failed (see $LOG)"
fi

echo "== antenna_design requirements"
[ -x "$PREFIX/venv/bin/python" ] && "$PREFIX/venv/bin/python" -m pip install -q -r "$REPO_DIR/antenna_design/requirements.txt"
python3 -m pip install -q -r "$REPO_DIR/antenna_design/requirements.txt" 2>/dev/null \
  || python3 -m pip install -q --break-system-packages -r "$REPO_DIR/antenna_design/requirements.txt" \
  || echo "WARN: pip could not install antenna_design requirements"

echo "== check"
(
  cd "$REPO_DIR" && source antenna_design/em/runtime_env.sh 2>/dev/null
  python -c 'import openEMS, CSXCAD; print("openEMS", openEMS.__version__, "| CSXCAD", CSXCAD.__version__)' \
    || echo "openEMS/CSXCAD NOT importable"
)
ls -l "$PREFIX/bin/openEMS" 2>/dev/null || echo "openEMS binary not found"
nproc; free -m | head -2
echo "== $(date -u) setup end"
exit 0
