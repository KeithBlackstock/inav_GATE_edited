#pragma once

#include "config/parameter_group.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct recallConfig_s {
    uint8_t steeringGain;        // Proportional heading-error gain scaled by 0.01 [1, 200]
    uint16_t dropSpeedThreshold; // Descent rate that exits RECALL, in cm/s [500, 5000]
} recallConfig_t;

PG_DECLARE(recallConfig_t, recallConfig);

bool isRecallModeAvailable(void);
void applyRecallSteering(void);
void checkRecallDropSpeedFailsafe(void);
