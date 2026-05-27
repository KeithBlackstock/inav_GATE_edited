#pragma once

#include "pg/pg.h"
#include <stdint.h>

typedef struct gatedConfig_s {
    uint8_t maxBankAngle;   // degrees [5, 85]
} gatedConfig_t;

PG_DECLARE(gatedConfig_t, gatedConfig);

void applyGatedRollAttenuation(void);
