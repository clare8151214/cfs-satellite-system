# Ubuntu ARM64 cFS VM

This directory creates the legacy Ubuntu ARM64 satellite environment used for comparison with the FreeRTOS POC.

## Create

```bash
./create-vm.sh
```

The script uses the host's `~/.ssh/id_ed25519.pub` by default. Override it with `SSH_PUBLIC_KEY_FILE` or change the guest account with `VM_USER`.

## Start

```bash
./start-satellite-system.sh
```

Defaults:

- SSH: host `2222` to guest `22`
- cFS command: host UDP `1234` to guest UDP `1234`
- Telemetry destination from guest to host: `10.0.2.2:2234`

The generated images and cloud-init files are intentionally excluded from Git.
