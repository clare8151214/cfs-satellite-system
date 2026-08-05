#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include "common_types.h"
#include "osapi.h"
#include "osapi-os-core.h"
#include "osapi-os-loader.h"
#include "os-shared-globaldefs.h"
#include "os-freertos.h"

extern OS_static_symbol_record_t OS_STATIC_SYMBOL_TABLE[];

static int32 OS_FreeRTOS_StaticModuleLookup(const char *module_name)
{
    OS_static_symbol_record_t *symbol;

    for (symbol = OS_STATIC_SYMBOL_TABLE; symbol->Name != NULL; ++symbol)
    {
        if (symbol->Module != NULL && strcmp(symbol->Module, module_name) == 0)
        {
            return OS_SUCCESS;
        }
    }

    return OS_ERR_NAME_NOT_FOUND;
}

static int32 OS_FreeRTOS_StaticSymbolLookup(cpuaddr *symbol_address, const char *symbol_name)
{
    OS_static_symbol_record_t *symbol;

    for (symbol = OS_STATIC_SYMBOL_TABLE; symbol->Name != NULL; ++symbol)
    {
        if (strcmp(symbol->Name, symbol_name) == 0)
        {
            *symbol_address = (cpuaddr)symbol->Address;
            return OS_SUCCESS;
        }
    }

    return OS_ERROR;
}

int32 OS_FreeRTOS_ModuleAPI_Impl_Init(void){
    return OS_SUCCESS;  // @FIXME
}

int32 OS_ModuleAPI_Init(void){
    return OS_SUCCESS;  // @FIXME
}

int32 OS_ModuleLoad(osal_id_t *module_id, const char *module_name, const char *filename, uint32 flags){
    (void)filename;
    (void)flags;

    if (module_id == NULL || module_name == NULL)
    {
        return OS_INVALID_POINTER;
    }

    if (strlen(module_name) >= OS_MAX_API_NAME)
    {
        return OS_ERR_NAME_TOO_LONG;
    }

    if (OS_FreeRTOS_StaticModuleLookup(module_name) != OS_SUCCESS)
    {
        return OS_ERR_NOT_IMPLEMENTED;
    }

    *module_id = OS_ObjectIdFromInteger(1);
    return OS_SUCCESS;
}

int32 OS_ModuleUnload(osal_id_t module_id){
    if (!OS_ObjectIdDefined(module_id))
    {
        return OS_ERR_INVALID_ID;
    }

    return OS_SUCCESS;
}

int32 OS_ModuleGetInfo(void){
    return OS_ERROR;  // @FIXME
}

int32 OS_ModuleInfo(osal_id_t module_id, OS_module_prop_t *module_info){
    (void)module_id;
    (void)module_info;

    return OS_ERROR;  // @FIXME
}

int32 OS_SymbolLookup(cpuaddr *symbol_address, const char *symbol_name){
    if (symbol_address == NULL || symbol_name == NULL)
    {
        return OS_INVALID_POINTER;
    }

    return OS_FreeRTOS_StaticSymbolLookup(symbol_address, symbol_name);
}
