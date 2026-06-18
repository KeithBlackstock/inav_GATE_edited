#include "path_mode.h"

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

PG_REGISTER_WITH_RESET_TEMPLATE(pathConfig_t, pathConfig, PG_PATH_CONFIG, 3);
PG_RESET_TEMPLATE(pathConfig_t, pathConfig,
    .steeringGain  = 50,
    .calmDropSpeed = 200
);

// PATH's own sequential waypoint cursor. Entirely separate from
// posControl.activeWaypointIndex/posControl.navState (which belong to
// NAV_WP_MODE/RTH) - PATH never becomes a navigationFSMState_t and never
// touches the shared mission-progression state.
static bool pathEngaged;
static uint8_t pathWaypointIndex;
static int32_t pathLegBearingCentidegrees;
static bool pathRouteActive;
static bool pathCalmActive;

bool isPathModeAvailable(void)
{
    return IS_RC_MODE_ACTIVE(BOXPATH) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX);
}

// getWaypointLocalPosition converts waypoint wpNumber's lat/lon to the local
// coordinate frame (altitude ignored, per PATH's existing behavior).
// Returns false if the conversion fails (e.g. no GPS origin yet).
static bool getWaypointLocalPosition(uint8_t wpNumber, fpVector3_t *localPos)
{
    navWaypoint_t wp;
    getWaypoint(wpNumber, &wp);

    const gpsLocation_t wpLLH = { .lat = wp.lat, .lon = wp.lon, .alt = wp.alt };
    return geoConvertGeodeticToLocalOrigin(localPos, &wpLLH, GEO_ALT_RELATIVE);
}

// updatePathLegTarget snapshots the initial bearing to pathWaypointIndex
// for the upcoming isWaypointReached() check. Returns false - ending the
// route, PATH falls back to wings-level-ahead - if pathWaypointIndex is
// not a plain NAV_WP_ACTION_WAYPOINT entry (past the end of the mission, or
// any other action type) or its position can't be resolved.
static bool updatePathLegTarget(void)
{
    navWaypoint_t wp;
    getWaypoint(pathWaypointIndex, &wp);
    if (wp.action != NAV_WP_ACTION_WAYPOINT) {
        return false;
    }

    fpVector3_t targetPos;
    if (!getWaypointLocalPosition(pathWaypointIndex, &targetPos)) {
        return false;
    }

    pathLegBearingCentidegrees = calculateBearingToDestination(&targetPos);
    return true;
}

void applyPathSteering(void)
{
    if (!isPathModeAvailable()) {
        pathEngaged = false;
        return;
    }

    if (!pathEngaged) {
        // Rising edge: (re)start the route from waypoint #1. Matches the
        // existing "no resume-from-last-leg" preference - disengaging and
        // re-engaging PATH always restarts the sequence.
        pathEngaged = true;
        pathWaypointIndex = 1;
        pathRouteActive = updatePathLegTarget();
        pathCalmActive = false;
    }

    // CALM: if descent rate exceeds threshold, hold wings-level until recovery.
    // Hysteresis of 50 cm/s prevents rapid toggling at the boundary.
    if (pathConfig()->calmDropSpeed > 0) {
        const float vertVelocity = getEstimatedActualVelocity(Z);
        if (!pathCalmActive && vertVelocity < -(float)pathConfig()->calmDropSpeed) {
            pathCalmActive = true;
        } else if (pathCalmActive && vertVelocity > -(float)(pathConfig()->calmDropSpeed - 50)) {
            pathCalmActive = false;
        }
    }

    int16_t headingErrorDegrees = 0;

    if (!pathCalmActive && pathRouteActive) {
        fpVector3_t targetPos;
        if (!getWaypointLocalPosition(pathWaypointIndex, &targetPos)) {
            pathRouteActive = false;
        } else if (isWaypointReached(&targetPos, &pathLegBearingCentidegrees)) {
            pathWaypointIndex++;
            pathRouteActive = updatePathLegTarget();
            if (pathRouteActive) {
                getWaypointLocalPosition(pathWaypointIndex, &targetPos);
            }
        }

        if (pathRouteActive) {
            const int32_t targetBearingCentidegrees = calculateBearingToDestination(&targetPos);
            const int16_t headingDegrees = DECIDEGREES_TO_DEGREES(attitude.values.yaw);
            const int16_t targetBearingDegrees = targetBearingCentidegrees / 100;
            headingErrorDegrees = wrap_180(targetBearingDegrees - headingDegrees);
        }
    }
    // headingErrorDegrees stays 0 when the route is inactive (no mission,
    // mission complete, or non-WAYPOINT action) OR when CALM is active:
    // both cases command wings-level via LEVEL mode.

    const float gain = (float)pathConfig()->steeringGain * 0.01f;

    const float maxBankDeciDegrees = pidProfile()->max_angle_inclination[FD_ROLL];
    const float desiredBankDeciDegrees = constrainf(
        DEGREES_TO_DECIDEGREES((float)headingErrorDegrees) * gain,
        -maxBankDeciDegrees,
        maxBankDeciDegrees
    );

    // Roll is the only axis PATH manages autonomously. Pitch and yaw are
    // left as the pilot's stick inputs (interpreted as pitch angle by
    // LEVEL_MODE and as rate-based rudder, respectively), so the pilot can
    // manage airspeed/AoA throughout PATH and is less likely to be
    // surprised by a wild departure.
    rcCommand[ROLL] = pidAngleToRcCommand(desiredBankDeciDegrees, pidProfile()->max_angle_inclination[FD_ROLL]);
}
