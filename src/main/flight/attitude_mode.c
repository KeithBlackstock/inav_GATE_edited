#include "attitude_mode.h"

#include "fc/rc_controls.h"
#include "fc/rc_modes.h"
#include "fc/runtime_config.h"
#include "flight/imu.h"
#include "flight/pid.h"
#include "common/maths.h"
#include "config/parameter_group.h"
#include "config/parameter_group_ids.h"

PG_REGISTER_WITH_RESET_TEMPLATE(attitudeConfig_t, attitudeConfig, PG_ATTITUDE_CONFIG, 0);
PG_RESET_TEMPLATE(attitudeConfig_t, attitudeConfig,
    .rate_roll = 50,   // 50% of max throw
    .rate_pitch = 50,  // 50% of max throw
    .rate_yaw = 50     // 50% of max throw
);

// This function is called from the PID controller when ATTITUDE_MODE is active
// It applies direct attitude control without the cascaded rate loop
void applyAttitudeMode(void)
{
    // This is a placeholder - the actual implementation will be integrated
    // into the PID controller in pid.c where we'll add a new control path
    // for ATTITUDE_MODE that bypasses the rate controller
}

// Made with Bob
