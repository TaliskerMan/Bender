#!/bin/bash
# run.sh — Development launcher for Bender
# Runs the app directly from source without installing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

echo "Launching Bender from source..."
python3 -m bender "$@"
