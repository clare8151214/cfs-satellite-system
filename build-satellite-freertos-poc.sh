#!/usr/bin/env bash
set -euo pipefail

# Build the cFS Satellite System FreeRTOS proof of concept.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLCHAIN_DIR="${SCRIPT_DIR}/toolchain/gcc-arm-none-eabi-9-2019-q4-major"
BUILD_DIR="${BUILD_DIR:-build-mps2}"

if [[ ! -x "${TOOLCHAIN_DIR}/bin/arm-none-eabi-gcc" ]]; then
    echo "Missing ARM toolchain: ${TOOLCHAIN_DIR}" >&2
    echo "Expected arm-none-eabi-gcc at ${TOOLCHAIN_DIR}/bin/arm-none-eabi-gcc" >&2
    exit 1
fi

export PATH="${TOOLCHAIN_DIR}/bin:${PATH}"
export DOCKER_HOST_PROJECT_DIR="${SCRIPT_DIR}"
export DOCKER_CONTAINER_PROJECT_DIR="${SCRIPT_DIR}"
export LINKER_SCRIPT="${SCRIPT_DIR}/apps/bsp-arm-mps2-an385/scripts/ld/mps2_m3.ld"

echo "Building cFS Satellite System FreeRTOS POC"
echo "Workspace: ${SCRIPT_DIR}"
echo "Build dir: ${BUILD_DIR}"
echo

make -C "${SCRIPT_DIR}" \
    O="${BUILD_DIR}" \
    SIMULATION=cortex-m3 \
    BUILDTYPE=debug \
    OMIT_DEPRECATED=true \
    MISSIONCONFIG=mps2 \
    -j"$(nproc)"

echo
echo "Built: ${SCRIPT_DIR}/${BUILD_DIR}/cortex-m3/default_mps2/mps2/core-mps2"
