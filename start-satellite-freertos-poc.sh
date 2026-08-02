#!/usr/bin/env bash
set -euo pipefail

# Start the cFS Satellite System FreeRTOS proof of concept in QEMU.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${BUILD_DIR:-build-mps2}"
KERNEL="${SCRIPT_DIR}/${BUILD_DIR}/cortex-m3/default_mps2/mps2/core-mps2"

if [[ ! -x "${KERNEL}" ]]; then
    echo "FreeRTOS cFS image not found. Building it first."
    "${SCRIPT_DIR}/build-satellite-freertos-poc.sh"
fi

echo "Starting cFS Satellite System FreeRTOS POC"
echo "Target: QEMU ARM Cortex-M3 mps2-an385"
echo "Kernel: ${KERNEL}"
echo "Ground bridge: ${SATELLITE_BRIDGE:-1} (UDP cmd 1234, UDP tlm 2234)"
if [[ "${SATELLITE_BRIDGE:-1}" != "0" ]]; then
    echo "Exit: Ctrl-C"
else
    echo "Console exit: Ctrl-a x"
fi
echo

if [[ "${SATELLITE_BRIDGE:-1}" != "0" ]]; then
    exec python3 "${SCRIPT_DIR}/satellite-ground-bridge.py" \
        --kernel "${KERNEL}" \
        --cmd-host "${SATELLITE_CMD_HOST:-127.0.0.1}" \
        --cmd-port "${SATELLITE_CMD_PORT:-1234}" \
        --tlm-host "${SATELLITE_TLM_HOST:-127.0.0.1}" \
        --tlm-port "${SATELLITE_TLM_PORT:-2234}"
fi

exec qemu-system-arm \
    -machine mps2-an385 \
    -monitor null \
    -semihosting \
    --semihosting-config enable=on,target=native \
    -kernel "${KERNEL}" \
    -serial stdio \
    -nographic
