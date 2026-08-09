# Ubuntu ARM64 cFS VM

This directory creates the legacy Ubuntu ARM64 satellite environment used for comparison with the FreeRTOS POC.

## Create

From the repository root:

```bash
./vm/ubuntu-arm64/create-vm.sh
```

The script can be run from any checkout location. It uses the current host user's Ed25519 or RSA public key. If neither exists, it creates `~/.ssh/id_ed25519` automatically. Override the public key with `SSH_PUBLIC_KEY_FILE` or change the guest account with `VM_USER`:

```bash
SSH_PUBLIC_KEY_FILE=/path/to/key.pub VM_USER=cfs ./vm/ubuntu-arm64/create-vm.sh
```

## Start

```bash
./vm/ubuntu-arm64/start-satellite-system.sh
```

Defaults:

- SSH: host `2222` to guest `22`
- cFS command: host UDP `1234` to guest UDP `1234`
- Telemetry destination from guest to host: `10.0.2.2:2234`

The generated images and cloud-init files are intentionally excluded from Git.
