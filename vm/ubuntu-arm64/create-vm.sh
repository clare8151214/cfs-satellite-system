#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VM_USER="${VM_USER:-cfs}"
CLOUD_IMAGE="${SCRIPT_DIR}/noble-server-cloudimg-arm64.img"
VM_IMAGE="${SCRIPT_DIR}/ubuntu-arm64.img"
SEED_IMAGE="${SCRIPT_DIR}/seed.img"
USER_DATA="${SCRIPT_DIR}/user-data"
META_DATA="${SCRIPT_DIR}/meta-data"
CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img"

for command_name in cloud-localds qemu-img ssh-keygen wget; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "Missing command: ${command_name}. Run ${REPO_ROOT}/setup-host.sh first." >&2
        exit 1
    fi
done

if [[ -z "${SSH_PUBLIC_KEY_FILE:-}" ]]; then
    if [[ -f "${HOME}/.ssh/id_ed25519.pub" ]]; then
        SSH_PUBLIC_KEY_FILE="${HOME}/.ssh/id_ed25519.pub"
    elif [[ -f "${HOME}/.ssh/id_rsa.pub" ]]; then
        SSH_PUBLIC_KEY_FILE="${HOME}/.ssh/id_rsa.pub"
    else
        SSH_PRIVATE_KEY_FILE="${HOME}/.ssh/id_ed25519"
        SSH_PUBLIC_KEY_FILE="${SSH_PRIVATE_KEY_FILE}.pub"
        mkdir -p "${HOME}/.ssh"
        chmod 700 "${HOME}/.ssh"

        if [[ -f "${SSH_PRIVATE_KEY_FILE}" ]]; then
            echo "Creating missing public key from ${SSH_PRIVATE_KEY_FILE}."
            ssh-keygen -y -f "${SSH_PRIVATE_KEY_FILE}" >"${SSH_PUBLIC_KEY_FILE}"
        else
            echo "No host SSH key found; creating ${SSH_PRIVATE_KEY_FILE}."
            ssh-keygen -q -t ed25519 -N "" -f "${SSH_PRIVATE_KEY_FILE}"
        fi
    fi
fi

if [[ ! -f "${SSH_PUBLIC_KEY_FILE}" ]]; then
    echo "Missing SSH public key: ${SSH_PUBLIC_KEY_FILE}" >&2
    echo "Provide an existing key with SSH_PUBLIC_KEY_FILE=/path/to/key.pub." >&2
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
echo "SSH public key: ${SSH_PUBLIC_KEY_FILE}"
echo "Start it with: ${SCRIPT_DIR}/start-satellite-system.sh"
