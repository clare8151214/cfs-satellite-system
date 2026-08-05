#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${SCRIPT_DIR}/ubuntu-arm64.img"
SEED_IMAGE="${SCRIPT_DIR}/seed.img"
BIOS="/usr/share/AAVMF/AAVMF_CODE.fd"

VM_USER="${VM_USER:-cfs}"
SSH_PORT="${SSH_PORT:-2222}"
CFS_CMD_PORT="${CFS_CMD_PORT:-1234}"
MEMORY="${MEMORY:-4096}"
CPUS="${CPUS:-4}"

for required_file in "${IMAGE}" "${SEED_IMAGE}" "${BIOS}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "Missing required file: ${required_file}" >&2
        echo "Run ./create-vm.sh first." >&2
        exit 1
    fi
done

echo "Starting cFS Satellite System ARM64 QEMU VM"
echo "Image: ${IMAGE}"
echo "SSH: ssh -p ${SSH_PORT} ${VM_USER}@127.0.0.1"
echo "cFS command UDP: host ${CFS_CMD_PORT} -> guest ${CFS_CMD_PORT}"
echo "Console exit: Ctrl-a x"
echo

exec qemu-system-aarch64 \
    -machine virt \
    -cpu cortex-a72 \
    -smp "${CPUS}" \
    -m "${MEMORY}" \
    -bios "${BIOS}" \
    -drive "if=virtio,format=qcow2,file=${IMAGE}" \
    -drive "if=virtio,format=raw,file=${SEED_IMAGE}" \
    -netdev "user,id=net0,hostfwd=tcp::${SSH_PORT}-:22,hostfwd=udp::${CFS_CMD_PORT}-:${CFS_CMD_PORT}" \
    -device virtio-net-pci,netdev=net0 \
    -nographic
