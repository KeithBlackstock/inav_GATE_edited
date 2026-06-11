# RECALL Pilot Pitch/Yaw Authority

## Overview
RECALL now manages only roll (heading-error steering). Pitch and yaw remain
under direct pilot control throughout RECALL, the same as in plain
LEVEL/ANGLE mode.

## Background
A separate drop-speed failsafe (latching `isRecallModeAvailable()` to false
on excessive descent rate, exiting RECALL back to the pilot's selected mode)
was designed and implemented, but was superseded by this approach before
release.

The failsafe had a real gap: its effect depended on what else was active on
the transmitter. If RECALL was engaged from an ACRO/MANUAL switch position
(relying on RECALL's own override of `MANUAL_MODE` to provide self-leveling),
tripping the failsafe removed that override and dropped the aircraft straight
into ACRO passthrough - the opposite of the intended recovery - during a
high sink-rate event.

## New Approach
Rather than reactively detecting and exiting a developing dive, give the
pilot pitch authority for the entire duration of RECALL so they can manage
airspeed/AoA themselves and prevent the dive from developing in the first
place. RECALL becomes purely a roll-steering aid layered on top of whatever
pitch/yaw the pilot is already flying.

### Behavior
- **Roll**: autonomously computed by RECALL's heading-error steering,
  clamped to `max_angle_inclination[FD_ROLL]` (unchanged).
- **Pitch**: pilot's stick input passes through unmodified, interpreted as a
  pitch angle by LEVEL_MODE (which RECALL still forces on).
- **Yaw**: pilot's stick input passes through unmodified (rate-based rudder).
- **Throttle**: unchanged, manual.

### Implementation (`src/main/flight/recall_mode.c`)
`applyRecallSteering()` no longer zeroes `rcCommand[PITCH]` or
`rcCommand[YAW]`; only `rcCommand[ROLL]` is set.

```c
rcCommand[ROLL] = pidAngleToRcCommand(desiredBankDeciDegrees, pidProfile()->max_angle_inclination[FD_ROLL]);
```

No new settings, configurator changes, or PG fields are required beyond the
existing `recall_steering_gain`. (`PG_RECALL_CONFIG` was bumped to version 2
to account for the now-reverted drop-speed-threshold field added and removed
during development.)
