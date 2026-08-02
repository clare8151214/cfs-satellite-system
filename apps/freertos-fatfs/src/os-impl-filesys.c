/*
 * Copyright 2021 Patrick Paul
 * SPDX-License-Identifier: MIT-0
 */

#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include "common_types.h"
#include "osapi.h"
#include "osapi-os-core.h"
#include "osapi-os-filesys.h"
#include "os-shared-globaldefs.h"
#include "os-freertos.h"

// freertos-plus-fat
#include "portable/common/ff_ramdisk.h"
#include "include/ff_stdio.h"
#include "include/ff_headers.h"

// mission files embedded in binary via targets.cmake
extern const char STARTUP_SCR_DATA[];
extern const unsigned long STARTUP_SCR_SIZE;

// defines
#define RAMDISK_SECTOR_SIZE 512
#define RAMDISK_SECTORS 400  // each sector is 512 bytes per ff_ramdisk.h
#define RAMDISK_CACHE_SIZE 2048  // must be multiple of sector size, and at least twice as big

// ramdisk -- ephemeral, will be initialized empty in FF_RAMDiskInit
FF_Disk_t pxDiskRAM;
uint8_t rambuffer[RAMDISK_SECTORS * RAMDISK_SECTOR_SIZE];

typedef struct
{
    const char *data;
    size_t size;
    size_t position;
    bool is_open;
} EmbeddedFile_t;

static EmbeddedFile_t startup_script = {
    .data = STARTUP_SCR_DATA,
    .size = 0,
    .position = 0,
    .is_open = false
};

static bool is_startup_script_path(const char *path)
{
    return path != NULL && strcmp(path, "/cf/cfe_es_startup.scr") == 0;
}

// work in progress
int32 OS_FreeRTOS_FileSysAPI_Impl_Init(void){
    // verify cache size is multiple and at least twice as a big as sector size
    configASSERT( (RAMDISK_CACHE_SIZE % RAMDISK_SECTOR_SIZE) == 0 );
    configASSERT( (RAMDISK_CACHE_SIZE >= (2 * RAMDISK_SECTOR_SIZE)) );

    // impl detail: FF_RAMDiskInit zero-initializes and formats new partition
    // and mounts at "/cf" parameter
    pxDiskRAM = *FF_RAMDiskInit(
        "/cf",
        (uint8_t *) rambuffer,
        RAMDISK_SECTORS,
        RAMDISK_CACHE_SIZE
    );
    configASSERT(&pxDiskRAM);

    // name the volume
    sprintf(
        pxDiskRAM.pxIOManager->xPartition.pcVolumeLabel,
        "ramdisk1"
    );

    FF_RAMDiskShowPartition(&pxDiskRAM);

    return OS_SUCCESS;
}

int32 devel_breakpoint(void){
    return OS_SUCCESS;
}

// @FIXME not implemented and returning OS_SUCCESS
int32 OS_FileAPI_Init(void){
    return devel_breakpoint();
}
int32 OS_FileSysAPI_Init(void){
    return devel_breakpoint();
}
int32 OS_DirAPI_Init(void){
    return devel_breakpoint();
}
int32 OS_FreeRTOS_DirAPI_Impl_Init(void){
    return devel_breakpoint();
}
int32 OS_mkfs(char *address, const char *devname, const char *volname, size_t blocksize, osal_blockcount_t numblocks){
    return devel_breakpoint();
}
int32 OS_initfs(char *address, const char *devname, const char *volname, size_t blocksize, osal_blockcount_t numblocks){
    return devel_breakpoint();
}
int32 OS_mount(const char *devname, const char *mountpoint){
    return devel_breakpoint();
}
int32 OS_rmfs(const char *devname){
    return devel_breakpoint();
}
int32 OS_unmount(const char *mountpoint){
    return devel_breakpoint();
}

// @FIXME not implemented and returning OS_ERROR
int32 OS_DirectoryClose(osal_id_t dir_id){
    return -1;
}
int32 OS_OpenCreate(osal_id_t *filedes, const char *path, int32 flags, int32 access){
    if (filedes == NULL || path == NULL)
    {
        return OS_INVALID_POINTER;
    }

    if (is_startup_script_path(path) && flags == OS_FILE_FLAG_NONE && access == OS_READ_ONLY)
    {
        startup_script.size = STARTUP_SCR_SIZE;
        startup_script.position = 0;
        startup_script.is_open = true;
        *filedes = OS_ObjectIdFromInteger(1);
        return OS_SUCCESS;
    }

    return OS_ERROR;
}
int32 OS_close(osal_id_t filedes){
    if (OS_ObjectIdToInteger(filedes) == 1 && startup_script.is_open)
    {
        startup_script.is_open = false;
        startup_script.position = 0;
        return OS_SUCCESS;
    }

    return OS_ERROR;
}
int32 OS_fsBlocksFree(const char *name){
    return -1;
}
int32 OS_lseek(osal_id_t filedes, int32 offset, uint32 whence){
    size_t new_position;

    if (OS_ObjectIdToInteger(filedes) != 1 || !startup_script.is_open)
    {
        return OS_ERROR;
    }

    if (whence == OS_SEEK_SET)
    {
        new_position = offset;
    }
    else if (whence == OS_SEEK_CUR)
    {
        new_position = startup_script.position + offset;
    }
    else if (whence == OS_SEEK_END)
    {
        new_position = startup_script.size + offset;
    }
    else
    {
        return OS_ERROR;
    }

    if (new_position > startup_script.size)
    {
        return OS_ERROR;
    }

    startup_script.position = new_position;
    return startup_script.position;
}
int32 OS_read(osal_id_t filedes, void *buffer, size_t nbytes){
    size_t bytes_remaining;
    size_t bytes_to_copy;

    if (OS_ObjectIdToInteger(filedes) != 1 || !startup_script.is_open || buffer == NULL)
    {
        return OS_ERROR;
    }

    if (startup_script.position >= startup_script.size)
    {
        return 0;
    }

    bytes_remaining = startup_script.size - startup_script.position;
    bytes_to_copy = nbytes < bytes_remaining ? nbytes : bytes_remaining;
    memcpy(buffer, &startup_script.data[startup_script.position], bytes_to_copy);
    startup_script.position += bytes_to_copy;

    return bytes_to_copy;
}
int32 OS_remove(const char *path){
    return -1;
}
int32 OS_stat(const char *path, os_fstat_t *filestats){
    if (path == NULL || filestats == NULL)
    {
        return OS_INVALID_POINTER;
    }

    if (is_startup_script_path(path))
    {
        memset(filestats, 0, sizeof(*filestats));
        filestats->FileModeBits = OS_FILESTAT_MODE_READ;
        filestats->FileSize = STARTUP_SCR_SIZE;
        return OS_SUCCESS;
    }

    return OS_ERROR;
}
int32 OS_write(osal_id_t filedes, const void *buffer, size_t nbytes){
    return OS_ERR_NOT_IMPLEMENTED;
}
