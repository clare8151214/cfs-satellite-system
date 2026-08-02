#include "cfe.h"

#define SATELLITE_SAMPLE_STARTUP_EID 1
#define SATELLITE_SAMPLE_MODE_EID 2

#define SATELLITE_MODE_BOOT 0
#define SATELLITE_MODE_SAFE 1
#define SATELLITE_MODE_NOMINAL 2

#define SATELLITE_STATUS_OK 0
#define SATELLITE_STATUS_LOW_BATTERY 1

typedef struct
{
    uint32 Sequence;
    uint32 CommandCounter;
    uint32 ErrorCounter;
    uint32 Mode;
    uint32 Status;
    uint32 UptimeSeconds;
    uint32 PayloadSamples;
    uint32 BatteryPercent;
} SatelliteMission_State_t;

static void SatelliteMission_UpdateState(SatelliteMission_State_t *State)
{
    ++State->Sequence;
    ++State->UptimeSeconds;

    if (State->UptimeSeconds < 4)
    {
        State->Mode = SATELLITE_MODE_SAFE;
    }
    else
    {
        State->Mode = SATELLITE_MODE_NOMINAL;
    }

    if (State->Mode == SATELLITE_MODE_NOMINAL)
    {
        ++State->PayloadSamples;
        if (State->BatteryPercent > 20)
        {
            --State->BatteryPercent;
        }
    }
    else if (State->BatteryPercent < 100)
    {
        ++State->BatteryPercent;
    }

    State->Status = State->BatteryPercent < 30 ?
                    SATELLITE_STATUS_LOW_BATTERY :
                    SATELLITE_STATUS_OK;
}

static void SatelliteMission_PrintTelemetry(const SatelliteMission_State_t *State)
{
    OS_printf("SAT_MISSION_HK,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu\n",
              (unsigned long)State->Sequence,
              (unsigned long)State->CommandCounter,
              (unsigned long)State->ErrorCounter,
              (unsigned long)State->Mode,
              (unsigned long)State->Status,
              (unsigned long)State->UptimeSeconds,
              (unsigned long)State->PayloadSamples,
              (unsigned long)State->BatteryPercent);
}

void SatSample_AppMain(void)
{
    uint32 run_status = CFE_ES_RunStatus_APP_RUN;
    uint32 previous_mode = SATELLITE_MODE_BOOT;
    int32 register_status;
    SatelliteMission_State_t state = {
        .Sequence = 0,
        .CommandCounter = 0,
        .ErrorCounter = 0,
        .Mode = SATELLITE_MODE_BOOT,
        .Status = SATELLITE_STATUS_OK,
        .UptimeSeconds = 0,
        .PayloadSamples = 0,
        .BatteryPercent = 96
    };

    OS_printf("SatSample_AppMain entered\n");

    register_status = CFE_ES_RegisterApp();
    if (register_status != CFE_SUCCESS)
    {
        CFE_ES_WriteToSysLog("SatelliteSample: CFE_ES_RegisterApp failed: 0x%08lx\n",
                             (unsigned long)register_status);
        OS_printf("SatelliteSample register failed: 0x%08lx\n",
                  (unsigned long)register_status);
        return;
    }

    OS_printf("SatelliteSample registered with cFE\n");
    CFE_EVS_Register(NULL, 0, CFE_EVS_EventFilter_BINARY);
    CFE_EVS_SendEvent(SATELLITE_SAMPLE_STARTUP_EID,
                      CFE_EVS_EventType_INFORMATION,
                      "Satellite mission app started on FreeRTOS");

    while (CFE_ES_RunLoop(&run_status))
    {
        SatelliteMission_UpdateState(&state);

        if (state.Mode != previous_mode)
        {
            CFE_EVS_SendEvent(SATELLITE_SAMPLE_MODE_EID,
                              CFE_EVS_EventType_INFORMATION,
                              "Satellite mission mode changed to %lu",
                              (unsigned long)state.Mode);
            previous_mode = state.Mode;
        }

        SatelliteMission_PrintTelemetry(&state);
        OS_TaskDelay(1000);
    }

    CFE_ES_ExitApp(run_status);
}
