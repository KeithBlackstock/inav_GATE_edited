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

PG_REGISTER_WITH_RESET_TEMPLATE(recallConfig_t, recallConfig, PG_RECALL_CONFIG, 1);
PG_RESET_TEMPLATE(recallConfig_t, recallConfig,
    .steeringGain = 50,
    .dropSpeedThreshold = 1500
);

// Latched once an excessive descent rate is detected during RECALL. While
// latched, isRecallModeAvailable() reports false, exiting RECALL and handing
// control back to the pilot's selected mode. Cleared when the pilot
// deactivates the RECALL switch.
static bool dropSpeedFailsafeLatched = false;

bool isRecallModeAvailable(void)
{
    if (dropSpeedFailsafeLatched) {
        return false;
    }

    return IS_RC_MODE_ACTIVE(BOXRECALL) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX);
}

void checkRecallDropSpeedFailsafe(void)
{
    if (!IS_RC_MODE_ACTIVE(BOXRECALL)) {
        dropSpeedFailsafeLatched = false;
        return;
    }

    if (dropSpeedFailsafeLatched || !isRecallModeAvailable()) {
        return;
    }

    const float descentRate = getEstimatedActualVelocity(Z);  // cm/s, negative = down
    if (descentRate < -(float)recallConfig()->dropSpeedThreshold) {
        dropSpeedFailsafeLatched = true;
    }
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

    rcCommand[ROLL] = pidAngleToRcCommand(desiredBankDeciDegrees, pidProfile()->max_angle_inclination[FD_ROLL]);
    rcCommand[PITCH] = 0;
    rcCommand[YAW] = 0;
}
