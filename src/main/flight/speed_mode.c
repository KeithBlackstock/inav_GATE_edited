/*
 * This file is part of INAV.
 *
 * INAV is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * INAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with INAV.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "speed_mode.h"

#include "fc/rc_controls.h"
#include "fc/rc_modes.h"
#include "fc/runtime_config.h"
#include "io/gps.h"
#include "flight/mixer.h"
#include "common/maths.h"
#include "config/parameter_group.h"
#include "config/parameter_group_ids.h"

PG_REGISTER_WITH_RESET_TEMPLATE(speedConfig_t, speedConfig, PG_SPEED_CONFIG, 0);
PG_RESET_TEMPLATE(speedConfig_t, speedConfig,
    .targetSpeed = 1500,        // 15 m/s = 54 km/h
    .proportionalGain = 50      // 0.50 gain
);

void applySpeedThrottleControl(void)
{
    // Check if SPEED mode is active
    if (!IS_RC_MODE_ACTIVE(BOXSPEED)) {
        return;
    }

    // Require GPS fix - bail out silently if not available
    if (!STATE(GPS_FIX)) {
        return;
    }

    // Get current GPS ground speed (cm/s)
    const int16_t currentSpeed = gpsSol.groundSpeed;
    
    // Calculate speed error (target - current)
    const int16_t targetSpeed = (int16_t)speedConfig()->targetSpeed;
    const int16_t speedError = targetSpeed - currentSpeed;
    
    // Apply proportional control
    // proportionalGain is scaled by 0.01, so divide by 100
    const float gain = (float)speedConfig()->proportionalGain * 0.01f;
    const int16_t throttleAdjustment = (int16_t)((float)speedError * gain);
    
    // Get throttle limits
    const int16_t idleThrottle = (int16_t)getThrottleIdleValue();
    const int16_t maxThrottle = (int16_t)getMaxThrottle();
    
    // Apply adjustment and constrain to valid range
    rcCommand[THROTTLE] = constrain(rcCommand[THROTTLE] + throttleAdjustment, idleThrottle, maxThrottle);
}
