#[[
    Copyright 2021 Patrick Paul
    SPDX-License-Identifier: MIT-0
]]

if(NOT DEFINED OSAL_FREERTOS_CONFIG_H_DIR)
    message(FATAL_ERROR "You must set OSAL_FREERTOS_CONFIG_H_DIR to the location of FreeRTOSConfig.h for your BSP in arch_build_custom.cmake")
endif()

# FreeRTOS config
add_definitions(-include FreeRTOSConfig.h)

# FreeRTOS kernel
include_directories(${OSAL_FREERTOS_INC_DIR})
include_directories(${OSAL_FREERTOS_SRC_DIR}/include)
include_directories(${OSAL_FREERTOS_SRC_DIR}/portable/GCC/ARM_CM3)
FILE(GLOB FREERTOS_SOURCES
    ${OSAL_FREERTOS_SRC_DIR}/*.c
)
FILE(GLOB FREERTOS_PORTABLE_SOURCES
    ${OSAL_FREERTOS_SRC_DIR}/portable/GCC/ARM_CM3/*.c
    ${OSAL_FREERTOS_SRC_DIR}/portable/MemMang/heap_4.c
)

# FreeRTOS BSP vendored code
include_directories(
    vendor/FreeRTOS
    vendor/FreeRTOS/CMSIS
    vendor/FreeRTOS/src
)
set(BOOT_CODE
    vendor/FreeRTOS/init/startup.c
)
set(VENDOR_CODE
    vendor/FreeRTOS/src/syscall.c
    vendor/FreeRTOS/src/console.c
)

# CFS BSP code
set(SOURCES
    src/console.c
)

# remove start files for mps2
set(CMAKE_EXE_LINKER_FLAGS "-nostartfiles ${CMAKE_EXE_LINKER_FLAGS}" PARENT_SCOPE)

add_library(bsp-arm-mps2-an385 STATIC
    ${FREERTOS_SOURCES}
    ${FREERTOS_PORTABLE_SOURCES}
    ${BOOT_CODE}
    ${VENDOR_CODE}
    ${SOURCES}
)
