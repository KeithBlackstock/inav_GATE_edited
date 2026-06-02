#pragma once

#include "config/parameter_group.h"
#include <stdint.h>

typedef struct attitudeConfig_s {
    uint8_t rate_roll;      // Roll rate as percentage of max throw [0, 100]
    uint8_t rate_pitch;     // Pitch rate as percentage of max throw [0, 100]
    uint8_t rate_yaw;       // Yaw rate as percentage of max throw [0, 100]
} attitudeConfig_t;

PG_DECLARE(attitudeConfig_t, attitudeConfig);

void applyAttitudeMode(void);

// Made with Bob
