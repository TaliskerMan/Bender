#!/usr/bin/env bash
# run.sh — Development launcher for Bender
# Author: Chuck Talk, <chuck@nordheim.online>
# Runs the app directly from source without installing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
cd "${SCRIPT_DIR}"

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

echo "Launching Bender from source..."
python3 -m bender "$@"
