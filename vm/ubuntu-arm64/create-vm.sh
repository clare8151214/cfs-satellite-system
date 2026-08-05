#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_USER="${VM_USER:-cfs}"
SSH_PUBLIC_KEY_FILE="${SSH_PUBLIC_KEY_FILE:-${HOME}/.ssh/id_ed25519.pub}"
CLOUD_IMAGE="${SCRIPT_DIR}/noble-server-cloudimg-arm64.img"
VM_IMAGE="${SCRIPT_DIR}/ubuntu-arm64.img"
SEED_IMAGE="${SCRIPT_DIR}/seed.img"
USER_DATA="${SCRIPT_DIR}/user-data"
META_DATA="${SCRIPT_DIR}/meta-data"
CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img"

for command_name in cloud-localds qemu-img wget; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "Missing command: ${command_name}. Run ../../setup-host.sh first." >&2
        exit 1
    fi
done

if [[ ! -f "${SSH_PUBLIC_KEY_FILE}" ]]; then
    echo "Missing SSH public key: ${SSH_PUBLIC_KEY_FILE}" >&2
    echo "Create one with: ssh-keygen -t ed25519" >&2
    exit 1
fi

if [[ ! -f "${CLOUD_IMAGE}" ]]; then
    wget -O "${CLOUD_IMAGE}.download" "${CLOUD_IMAGE_URL}"
    mv "${CLOUD_IMAGE}.download" "${CLOUD_IMAGE}"
fi

if [[ ! -f "${VM_IMAGE}" ]]; then
    cp "${CLOUD_IMAGE}" "${VM_IMAGE}"
    qemu-img resize "${VM_IMAGE}" 20G
fi

PUBLIC_KEY="$(<"${SSH_PUBLIC_KEY_FILE}")"

cat >"${USER_DATA}" <<EOF
#cloud-config
users:
  - name: ${VM_USER}
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ${PUBLIC_KEY}
package_update: true
packages:
  - build-essential
  - cmake
  - git
  - net-tools
  - ninja-build
  - openssh-server
  - python3
  - python3-pip
EOF

cat >"${META_DATA}" <<EOF
instance-id: qemu-arm64-cfs-${VM_USER}
local-hostname: qemu-arm64
EOF

rm -f "${SEED_IMAGE}"
cloud-localds "${SEED_IMAGE}" "${USER_DATA}" "${META_DATA}"

echo "Created Ubuntu ARM64 VM for user ${VM_USER}."
echo "Start it with: ./start-satellite-system.sh"
