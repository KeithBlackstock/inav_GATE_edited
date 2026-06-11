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

PG_REGISTER_WITH_RESET_TEMPLATE(recallConfig_t, recallConfig, PG_RECALL_CONFIG, 2);
PG_RESET_TEMPLATE(recallConfig_t, recallConfig,
    .steeringGain = 50
);

bool isRecallModeAvailable(void)
{
    return IS_RC_MODE_ACTIVE(BOXRECALL) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX);
}

// getRecallTargetBearing looks up waypoint #1 of the loaded mission and, if
// present, returns the bearing toward it (centidegrees, [0, 36000)). Waypoint
// #1 is treated as RECALL's "home" - the altitude component is ignored.
// Returns false if no mission is loaded, leaving *bearingCentidegrees
// untouched.
static bool getRecallTargetBearing(int32_t *bearingCentidegrees)
{
    if (!isWaypointListValid() || getWaypointCount() < 1) {
        return false;
    }

    navWaypoint_t wp;
    getWaypoint(1, &wp);

    const gpsLocation_t wpLLH = { .lat = wp.lat, .lon = wp.lon, .alt = wp.alt };
    fpVector3_t wpLocalPos;
    if (!geoConvertGeodeticToLocalOrigin(&wpLocalPos, &wpLLH, GEO_ALT_RELATIVE)) {
        return false;
    }

    *bearingCentidegrees = calculateBearingToDestination(&wpLocalPos);
    return true;
}

void applyRecallSteering(void)
{
    if (!isRecallModeAvailable()) {
        return;
    }

    int32_t targetBearingCentidegrees;
    int16_t headingErrorDegrees = 0;
    if (getRecallTargetBearing(&targetBearingCentidegrees)) {
        const int16_t headingDegrees = DECIDEGREES_TO_DEGREES(attitude.values.yaw);
        const int16_t targetBearingDegrees = targetBearingCentidegrees / 100;
        headingErrorDegrees = wrap_180(targetBearingDegrees - headingDegrees);
    }
    // If no waypoint #1 is loaded, headingErrorDegrees stays 0: RECALL flies
    // straight ahead (wings level via LEVEL mode) rather than falling back
    // to the old home-position logic.

    const float gain = (float)recallConfig()->steeringGain * 0.01f;

    const float maxBankDeciDegrees = pidProfile()->max_angle_inclination[FD_ROLL];
    const float desiredBankDeciDegrees = constrainf(
        DEGREES_TO_DECIDEGREES((float)headingErrorDegrees) * gain,
        -maxBankDeciDegrees,
        maxBankDeciDegrees
    );

    // Roll is the only axis RECALL manages autonomously. Pitch and yaw are
    // left as the pilot's stick inputs (interpreted as pitch angle by
    // LEVEL_MODE and as rate-based rudder, respectively), so the pilot can
    // manage airspeed/AoA throughout RECALL and is less likely to be
    // surprised by a wild departure.
    rcCommand[ROLL] = pidAngleToRcCommand(desiredBankDeciDegrees, pidProfile()->max_angle_inclination[FD_ROLL]);
}
