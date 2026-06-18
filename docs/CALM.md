# CALM — Course Abort for Leveling Motion

CALM is a built-in safeguard for PATH mode. When the position estimator detects a descent rate exceeding `path_calm_drop_speed`, PATH temporarily suspends waypoint pursuit and drives the aircraft wings-level until the descent rate falls back below the threshold.

## Motivation

PATH steers by commanding bank angle proportional to heading error. At high `path_steering_gain` values, or when the bank-angle pitch compensation in LEVEL mode is insufficient to fully offset the altitude loss of a banked turn, the aircraft can lose altitude while pursuing waypoints. CALM is the "chill out" response: rather than continuing to bank into a worsening descent, PATH levels the wings until the aircraft recovers.

## Behavior

While CALM is active:

- PATH remains engaged — the mode does not exit and the waypoint cursor is not reset.
- `rcCommand[ROLL]` is driven toward wings-level (the same zero-heading-error path that PATH uses at end-of-route).
- LEVEL_MODE remains active, including bank-angle pitch compensation.
- SAFE (pilot pitch, yaw, and throttle passthrough) remains fully active — the pilot can pitch out of the descent at any time.
- Waypoint advancement is frozen; PATH resumes pursuit of the same waypoint once the descent rate recovers.

CALM clears immediately when `getEstimatedActualVelocity(Z)` rises back above `-path_calm_drop_speed`. There is no hysteresis — the check is binary each loop.

Setting `path_calm_drop_speed = 0` disables CALM entirely.

## Configuration

```
set path_calm_drop_speed = 200  # cm/s descent rate trigger; 0 = disabled (default 200, range 0-1000)
```

## Implementation

CALM is implemented entirely within `src/main/flight/path_mode.c`, with no changes to `pid.c`, `fc_core.c`, or the configurator beyond the new parameter.

In `applyPathSteering()`, after the engagement rising-edge block:

```c
const bool pathCalmActive = (pathConfig()->calmDropSpeed > 0) &&
                            (getEstimatedActualVelocity(Z) < -(float)pathConfig()->calmDropSpeed);
```

The existing waypoint pursuit block is then guarded by `!pathCalmActive`. When calm, `headingErrorDegrees` stays 0, which the downstream gain/constrain/rcCommand path already treats as a wings-level command — no additional control logic is required.
