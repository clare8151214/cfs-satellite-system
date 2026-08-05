/*
 * Copyright 2021 Patrick Paul
 * SPDX-License-Identifier: MIT-0
 */

#include <stdlib.h>

#include "osapi.h"
#include "os-shared-common.h"

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

char debugBuffer[100];

volatile unsigned int * const UART0 = (unsigned int *) 0x40004000;

int32 PSP_Console_Init(void){
    return 0;
}

void PSP_Console_Write(char *buffer){
    while(*buffer != '\0'){
        *UART0 = (unsigned int)(*buffer);
        buffer++;
    }
}

void OS_DebugPrintf(uint32 Level, const char *Func, uint32 Line, const char *Format, ...){
    va_list va;
    if(OS_SharedGlobalVars.DebugLevel >= Level){
        va_start(va, Format);
        vsprintf(debugBuffer, Format, va);
        va_end(va);
        PSP_Console_Write(debugBuffer);
    }
}