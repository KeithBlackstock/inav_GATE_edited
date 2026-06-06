#include "recall_mode.h"

#include "common/axis.h"
#include "common/maths.h"

#include "config/parameter_group.h"
#include "config/parameter_group_ids.h"

#include "fc/rc_controls.h"
#include "fc/rc_modes.h"
#include "fc/runtime_config.h"

#include "flight/imu.h"
#include "flight/pid.h"

#include "navigation/navigation.h"

#include "sensors/sensors.h"

PG_REGISTER_WITH_RESET_TEMPLATE(recallConfig_t, recallConfig, PG_RECALL_CONFIG, 0);
PG_RESET_TEMPLATE(recallConfig_t, recallConfig,
    .steeringGain = 50
);

bool isRecallModeAvailable(void)
{
    return IS_RC_MODE_ACTIVE(BOXRECALL) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX) &&
           STATE(GPS_FIX_HOME);
}

void applyRecallSteering(void)
{
    if (!isRecallModeAvailable()) {
        return;
    }

    const int16_t headingDegrees = DECIDEGREES_TO_DEGREES(attitude.values.yaw);
    const int16_t headingErrorDegrees = wrap_180(GPS_directionToHome - headingDegrees);
    const float gain = (float)recallConfig()->steeringGain * 0.01f;

    const float maxBankDeciDegrees = pidProfile()->max_angle_inclination[FD_ROLL];
    const float desiredBankDeciDegrees = constrainf(
        DEGREES_TO_DECIDEGREES((float)headingErrorDegrees) * gain,
        -maxBankDeciDegrees,
        maxBankDeciDegrees
    );

    rcCommand[ROLL] = pidAngleToRcCommand(desiredBankDeciDegrees, pidProfile()->max_angle_inclination[FD_ROLL]);
    rcCommand[PITCH] = 0;
    rcCommand[YAW] = 0;
}
