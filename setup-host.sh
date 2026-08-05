#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLCHAIN_ROOT="${SCRIPT_DIR}/toolchain"
TOOLCHAIN_NAME="gcc-arm-none-eabi-9-2019-q4-major"
TOOLCHAIN_DIR="${TOOLCHAIN_ROOT}/${TOOLCHAIN_NAME}"
TOOLCHAIN_ARCHIVE="${TOOLCHAIN_ROOT}/${TOOLCHAIN_NAME}-x86_64-linux.tar.bz2.download"
TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2019q4/gcc-arm-none-eabi-9-2019-q4-major-x86_64-linux.tar.bz2"

sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cloud-image-utils \
    cmake \
    git \
    libcanberra-gtk-module \
    python3 \
    python3-pyqt5 \
    python3-zmq \
    qemu-efi-aarch64 \
    qemu-system-arm \
    qemu-utils \
    wget

if [[ ! -x "${TOOLCHAIN_DIR}/bin/arm-none-eabi-gcc" ]]; then
    mkdir -p "${TOOLCHAIN_ROOT}"
    wget -O "${TOOLCHAIN_ARCHIVE}" "${TOOLCHAIN_URL}"
    tar -xjf "${TOOLCHAIN_ARCHIVE}" -C "${TOOLCHAIN_ROOT}"
    rm -f "${TOOLCHAIN_ARCHIVE}"
fi

make -C "${SCRIPT_DIR}/tools/cFS-GroundSystem/Subsystems/cmdUtil"

echo
echo "Host setup complete."
echo "Build flight image: ./build-satellite-freertos-poc.sh"
echo "Start ground system: ./start-ground-system.sh"
