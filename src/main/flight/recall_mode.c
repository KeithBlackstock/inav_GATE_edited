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

// RECALL's own sequential waypoint cursor. Entirely separate from
// posControl.activeWaypointIndex/posControl.navState (which belong to
// NAV_WP_MODE/RTH) - RECALL never becomes a navigationFSMState_t and never
// touches the shared mission-progression state.
static bool recallEngaged;
static uint8_t recallWaypointIndex;
static int32_t recallLegBearingCentidegrees;
static bool recallRouteActive;

bool isRecallModeAvailable(void)
{
    return IS_RC_MODE_ACTIVE(BOXRECALL) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX);
}

// getWaypointLocalPosition converts waypoint wpNumber's lat/lon to the local
// coordinate frame (altitude ignored, per RECALL's existing behavior).
// Returns false if the conversion fails (e.g. no GPS origin yet).
static bool getWaypointLocalPosition(uint8_t wpNumber, fpVector3_t *localPos)
{
    navWaypoint_t wp;
    getWaypoint(wpNumber, &wp);

    const gpsLocation_t wpLLH = { .lat = wp.lat, .lon = wp.lon, .alt = wp.alt };
    return geoConvertGeodeticToLocalOrigin(localPos, &wpLLH, GEO_ALT_RELATIVE);
}

// updateRecallLegTarget snapshots the initial bearing to recallWaypointIndex
// for the upcoming isWaypointReached() check. Returns false - ending the
// route, RECALL falls back to wings-level-ahead - if recallWaypointIndex is
// not a plain NAV_WP_ACTION_WAYPOINT entry (past the end of the mission, or
// any other action type) or its position can't be resolved.
static bool updateRecallLegTarget(void)
{
    navWaypoint_t wp;
    getWaypoint(recallWaypointIndex, &wp);
    if (wp.action != NAV_WP_ACTION_WAYPOINT) {
        return false;
    }

    fpVector3_t targetPos;
    if (!getWaypointLocalPosition(recallWaypointIndex, &targetPos)) {
        return false;
    }

    recallLegBearingCentidegrees = calculateBearingToDestination(&targetPos);
    return true;
}

void applyRecallSteering(void)
{
    if (!isRecallModeAvailable()) {
        recallEngaged = false;
        return;
    }

    if (!recallEngaged) {
        // Rising edge: (re)start the route from waypoint #1. Matches the
        // existing "no resume-from-last-leg" preference - disengaging and
        // re-engaging RECALL always restarts the sequence.
        recallEngaged = true;
        recallWaypointIndex = 1;
        recallRouteActive = updateRecallLegTarget();
    }

    int16_t headingErrorDegrees = 0;

    if (recallRouteActive) {
        fpVector3_t targetPos;
        if (!getWaypointLocalPosition(recallWaypointIndex, &targetPos)) {
            recallRouteActive = false;
        } else if (isWaypointReached(&targetPos, &recallLegBearingCentidegrees)) {
            recallWaypointIndex++;
            recallRouteActive = updateRecallLegTarget();
            if (recallRouteActive) {
                getWaypointLocalPosition(recallWaypointIndex, &targetPos);
            }
        }

        if (recallRouteActive) {
            const int32_t targetBearingCentidegrees = calculateBearingToDestination(&targetPos);
            const int16_t headingDegrees = DECIDEGREES_TO_DEGREES(attitude.values.yaw);
            const int16_t targetBearingDegrees = targetBearingCentidegrees / 100;
            headingErrorDegrees = wrap_180(targetBearingDegrees - headingDegrees);
        }
    }
    // If the route is inactive (no mission, mission complete, or a
    // non-WAYPOINT action encountered), headingErrorDegrees stays 0: RECALL
    // flies straight ahead (wings level via LEVEL mode).

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
