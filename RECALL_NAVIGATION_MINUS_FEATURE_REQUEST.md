# RECALL Sequential Waypoint Steering ("Navigation-minus")

## Status
Design sketch only. No code changes. Hold for implementation until the
pilot-pitch/yaw-authority redesign (`RECALL_PILOT_PITCH_YAW_FEATURE_REQUEST.md`)
has been field-verified.

## Overview
Extend RECALL's existing pure-pursuit heading-error steering so it walks a
*sequence* of mission waypoints (multi-leg path home) instead of always
steering directly at waypoint #1. RECALL otherwise stays exactly what it is
today: a roll-only autonomous layer, with pitch/yaw/throttle left to the
pilot.

This is "navigation minus" in the sense that RECALL borrows only the
**waypoint capture/advance bookkeeping** used by `NAV_WP_MODE`
(`isWaypointReached()`, sequential index advance), and deliberately leaves out
the actual **position/altitude controllers** (`NAV_CTL_POS` /
`applyFixedWingPositionController()` / `applyFixedWingAltitudeAndThrottleController()`
/ `applyFixedWingPitchRollThrottleController()`). RECALL does not become a
`navigationFSMState_t` and does not touch `posControl.navState`.

## Why not just adopt `NAV_CTL_POS`?
Looked at making RECALL a real NAV FSM state with `NAV_CTL_POS` (proper
position controller) but without `NAV_CTL_ALT` (so altitude/throttle stay
manual, consistent with the pitch/yaw-passthrough redesign). That path has a
real problem:

`applyFixedWingPitchRollThrottleController()` ties `NAV_CTL_POS` to **both**
roll *and* yaw output (`isYawAdjustmentValid` / heading controller). Adopting
the standard FW position controller would silently re-claim the yaw axis from
the pilot - directly undoing the pitch/yaw-passthrough change we just shipped.
Disentangling that would mean forking/patching the shared FW nav controller,
which is a lot of surface area and risk for what RECALL actually needs (just
"point roughly at the next point and let the pilot fly the rest").

Sequential pure-pursuit avoids all of this: it's a self-contained extension of
the bearing math RECALL already does, with zero interaction with the NAV FSM
or the shared FW controllers.

## Current behavior (baseline)
`applyRecallSteering()` (`recall_mode.c`) already:
- Looks up waypoint #1 of the loaded mission via `getWaypoint(1, &wp)`.
- Converts it to local frame with `geoConvertGeodeticToLocalOrigin()`.
- Computes bearing to it with `calculateBearingToDestination()`.
- Computes heading error vs. current yaw, converts to a clamped bank angle,
  and writes only `rcCommand[ROLL]`.
- If no mission is loaded, flies wings-level straight ahead instead.

Waypoint #1 is currently a fixed, single "aim point" - effectively just
"home" or whatever the pilot placed first.

## Proposed behavior
RECALL maintains its own **independent** waypoint cursor (separate from
`posControl.activeWaypointIndex`, which belongs to `NAV_WP_MODE`/RTH and must
not be disturbed):

1. **On RECALL engage** (rising edge of `isRecallModeAvailable()`):
   - If a valid mission is loaded (`isWaypointListValid()`,
     `getWaypointCount() >= 1`), set RECALL's cursor to waypoint #1 and snapshot
     the initial bearing to it (same value `isWaypointReached()` compares
     against for the "missed" check).
   - If no mission is loaded, fall back to today's wings-level-ahead behavior
     (unchanged).

2. **Each loop while engaged**:
   - Compute bearing/distance to the current cursor waypoint as today.
   - Steer roll toward that bearing (unchanged math).
   - Call `isWaypointReached(&targetPosLocal, &snapshotBearing)` using the
     same arrival/miss test `NAV_WP_MODE` uses
     (`waypoint_radius` distance, or >100°/60° bearing divergence for a
     missed waypoint).
   - If reached (arrived *or* missed), advance the cursor to the next
     waypoint index and re-snapshot the bearing for the new leg.

3. **Waypoint action handling**: RECALL only understands plain
   `NAV_WP_ACTION_WAYPOINT` entries as "fly toward this point, then advance."
   No other action type is supported - if the cursor ever lands on a
   non-`WAYPOINT` entry (`RTH`, `JUMP`, `HOLD_TIME`, `LAND`, `SET_POI`,
   `SET_HEAD`, etc.), including as the very first entry, RECALL treats this
   exactly like "end of route" (see below). RECALL never attempts to
   interpret mission semantics that only make sense to the full NAV FSM.

4. **End of route**: once the cursor's waypoint is reached and there is no
   further `WAYPOINT`-action entry to advance to (last waypoint of the
   mission, or a non-`WAYPOINT` action encountered), RECALL stops steering
   toward a target altogether and falls back to today's no-mission behavior:
   wings-level-ahead. RECALL keeps providing roll stabilization, but the
   heading-error term goes to zero - the aircraft simply continues on
   whatever heading it was already flying when the route ended. RECALL does
   not try to hold position or loiter at the final point; it's left to the
   pilot to disengage RECALL and resume manual flight or set up a landing
   from there.

5. **Re-engage behavior**: disengaging and re-engaging RECALL resets the
   cursor back to waypoint #1 (matches existing "no special re-activation
   clauses" preference - keep state minimal, no resume-from-last-leg logic).

## State additions (`recall_mode.c`)
A small amount of new state, local to `recall_mode.c` (not part of
`posControl`):

```c
static uint8_t recallWaypointIndex;     // absolute index into posControl.waypointList
static int32_t recallLegBearing;        // bearing snapshot for isWaypointReached()
static bool recallRouteActive;          // false => wings-level-ahead fallback
```

Reset on each rising edge of `isRecallModeAvailable()`.

## What stays unchanged
- RECALL still manages **only roll**; pitch/yaw/throttle remain pilot
  passthrough (per `RECALL_PILOT_PITCH_YAW_FEATURE_REQUEST.md`).
- No new NAV FSM states, no `NAV_CTL_POS`/`NAV_CTL_ALT`, no interaction with
  `applyFixedWingPositionController()` / `applyFixedWingPitchRollThrottleController()`.
- No changes to `posControl.activeWaypointIndex`, `posControl.navState`, or
  any state consumed by `NAV_WP_MODE`/RTH - RECALL's cursor is entirely
  separate bookkeeping.
- `recall_steering_gain` and the existing bank-angle clamp logic are
  unchanged.
