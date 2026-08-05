#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GROUND_DIR="${SCRIPT_DIR}/tools/cFS-GroundSystem"

make -C "${GROUND_DIR}/Subsystems/cmdUtil"
cd "${GROUND_DIR}"
exec python3 GroundSystem.py
