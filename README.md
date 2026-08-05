# cFS Satellite System

本 repository 是可單獨交接的 cFS 衛星系統 monorepo，整合：

- FreeRTOS + cFE + OSAL + PSP 衛星 flight image。
- QEMU `mps2-an385` ARM Cortex-M3 模擬環境。
- `SAT_SAMPLE_APP` mission app。
- cFS GroundSystem command/telemetry GUI。
- Ubuntu ARM64 cFS 比較用虛擬機建立與啟動腳本。
- 架構及交接文件。

所有原本的 Git submodules 都已轉成普通追蹤目錄。完成 clone 後不需要執行 `git submodule update`。

## 目錄

```text
apps/satellite-sample/       FreeRTOS mission app
cfe/                         cFE source snapshot
osal/                        OSAL source，包含 FreeRTOS static loader patch
psp/                         PSP source snapshot
lib/                         FreeRTOS kernel 與 FreeRTOS+FAT
tools/cFS-GroundSystem/      客製地面站
vm/ubuntu-arm64/             Ubuntu ARM64 VM 建立與啟動工具
SATELLITE-SYSTEM-HANDOFF.md  完整交接手冊
THIRD_PARTY_SOURCES.md       上游來源與 commit SHA
```

## 第一次建立環境

```bash
./setup-host.sh
```

此腳本會安裝 QEMU、GroundSystem 所需套件，並下載建置 FreeRTOS image 使用的 Arm GNU Toolchain。需要 `sudo` 及網路連線。

## FreeRTOS 衛星

建置：

```bash
./build-satellite-freertos-poc.sh
```

啟動 QEMU 衛星與 GroundSystem bridge：

```bash
./start-satellite-freertos-poc.sh
```

成功時應看到：

```text
CFE_ES_Main entering OPERATIONAL state
SAT_MISSION_HK,...
```

## 地面站

另一個 terminal 執行：

```bash
./start-ground-system.sh
```

GroundSystem 使用 UDP `1234` 傳送 command，並在 UDP `2234` 接收 telemetry。

## Ubuntu ARM64 比較環境

建立 VM：

```bash
./vm/ubuntu-arm64/create-vm.sh
```

啟動 VM：

```bash
./vm/ubuntu-arm64/start-satellite-system.sh
```

VM image、cloud image、seed image、toolchain 與 build output 都由腳本產生，並由 `.gitignore` 排除。

## 文件

- [完整交接手冊](SATELLITE-SYSTEM-HANDOFF.md)
- [FreeRTOS POC 技術說明](SATELLITE-FREERTOS-POC.md)
- [上游原始碼來源](THIRD_PARTY_SOURCES.md)

## 目前限制

FreeRTOS OSAL socket layer 尚未實作，因此 command/telemetry 目前使用 host-side bridge。GroundSystem command 還沒有真正注入 FreeRTOS cFE Software Bus；詳細狀態與下一步請參考交接手冊。
