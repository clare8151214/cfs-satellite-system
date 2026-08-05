# Bundled Source Provenance

This monorepo vendors source snapshots that were previously Git submodules. Licenses remain in their original directories.

| Path | Upstream | Imported commit |
| --- | --- | --- |
| `apps/bsp-arm-mps2-an385` | `https://github.com/pztrick/cfs-bsp-arm-mps2-an385.git` | `74f8d98c878c9fedb9fe3efa07993cb91428cde5` |
| `cfe` | `https://github.com/pztrick/cfe.git` | `88b99db67a5ad33cee1872ff39e07255907245de` |
| `lib/freertos` | `https://github.com/FreeRTOS/FreeRTOS-Kernel.git` | `ac2c383bc14b2577101cad238c8779f4d9c14d6c` |
| `lib/freertos-plus-fat` | `https://github.com/FreeRTOS/Lab-Project-FreeRTOS-FAT.git` | `97e608cca689c702fb51e386d4df9e9ea0ee88a6` |
| `osal` | `https://github.com/pztrick/osal.git` | `e3739d9ce08c8c86b61b9abe45feef64632135df` |
| `psp` | `https://github.com/pztrick/psp.git` | `ad325745230cf3a71a415f0740fbc6c57411c399` |
| `tools/cFS-GroundSystem` | `https://github.com/nasa/cFS-GroundSystem.git` | `fe53126710b460f90df436e79dd17bf950fcb559` |
| `tools/elf2cfetbl` | `https://github.com/nasa/elf2cfetbl` | `858a176f05db108bc985613309481214df076e95` |
| `tools/tblCRCTool` | `https://github.com/nasa/tblCRCTool` | `9761ab51264ee6bff859a2e3a7adace67fa27328` |

The OSAL and GroundSystem commits contain this project's local integration changes. Their source snapshots are committed directly here, so a new clone does not need access to those local branches.
