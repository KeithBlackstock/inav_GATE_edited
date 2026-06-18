#pragma once

#include "config/parameter_group.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct pathConfig_s {
    uint8_t  steeringGain;    // Proportional heading-error gain scaled by 0.01 [1, 200]
    uint16_t calmDropSpeed;   // Descent rate (cm/s) that triggers CALM wings-level hold [0, 1000]
} pathConfig_t;

PG_DECLARE(pathConfig_t, pathConfig);

bool isPathModeAvailable(void);
void applyPathSteering(void);
