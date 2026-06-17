#pragma once

#include "config/parameter_group.h"
#include <stdint.h>

typedef struct diveConfig_s {
    uint8_t maxDiveAngle;   // degrees [0, 90]
} diveConfig_t;

PG_DECLARE(diveConfig_t, diveConfig);

void applyDiveThrottleAttenuation(void);
