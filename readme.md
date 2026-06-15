GATED is an AUX-selectable roll limiting mode. When active, it reduces pilot roll input only when the command would increase the current bank angle. As roll approaches gated_max_bank_angle, same-direction roll input is attenuated toward zero; opposite-direction roll input remains available so the pilot can always roll back toward level. It does not auto-level, hold attitude, or create a primary FLIGHT_MODE(...) state.

Key modified files:

src/main/flight/gated_mode.c: core roll attenuation logic and parameter group registration.
src/main/flight/gated_mode.h: GATED config struct and function declaration.
src/main/fc/fc_core.c: calls applyGatedRollAttenuation() in the RC command path.
src/main/fc/rc_modes.h: adds BOXGATED.
src/main/fc/fc_msp_box.c: exposes GATED as an MSP/AUX mode with permanent ID 69.
src/main/config/parameter_group_ids.h: adds PG_GATED_CONFIG.
src/main/fc/settings.yaml: adds gated_max_bank_angle.
docs/Settings.md: documents the CLI setting.
docs/development/msp/inav_enums.json and inav_enums_ref.md: update MSP enum docs.

---

LEVEL is an AUX-selectable flight mode that blends ANGLE (self-leveling) with MANUAL (direct passthrough — no PID) based on stick deflection. At center stick the aircraft fully self-levels; at full stick control passes through directly with no stabilization. This is distinct from HORIZON, which blends ANGLE with ACRO (rate-controlled) — at full stick HORIZON still applies rate PID, whereas LEVEL is intended to hand off to completely unassisted manual control.

LEVEL includes bank-angle pitch compensation: the pitch `angleTarget` is scaled so that the vertical lift contribution remains constant as the aircraft banks, preserving altitude maintenance through turns. The formula applied in `computePidLevelTarget()` is `arcsin(sin(base_pitch) / cos(bank_angle))`, where `base_pitch` is the pilot's commanded pitch plus `fixedWingLevelTrim`. At wings level this has no effect; at 30° bank a 5° trim becomes ~5.8°, at 45° ~7.1°, at 60° ~10°. Bank angles beyond ~84° are clamped to avoid overflow.

The `bank_angle` used is the *commanded roll target* for this loop, not the aircraft's current attitude - `computePidLevelTarget(FD_ROLL)` runs first and caches its result for the pitch axis's compensation, so the compensation reacts proactively as soon as a bank is commanded rather than lagging behind the airframe's roll response. The compensation is also active under PATH, which auto-enables LEVEL_MODE - it reacts to PATH's autonomous roll-steering output the same way it would to a pilot's roll stick input.

Key modified files:

src/main/fc/rc_modes.h: adds BOXLEVEL (Box ID 61).
src/main/fc/fc_msp_box.c: exposes LEVEL as an MSP/AUX mode with permanent ID 71.
src/main/fc/runtime_config.h: adds LEVEL_MODE flag (bit 20).
src/main/fc/runtime_config.c: activates LEVEL_MODE when BOXLEVEL is selected.
src/main/flight/pid.c: routes LEVEL through pidLevel() with horizonRateMagnitude blend; extends ANGLE/HORIZON checks to include LEVEL throughout pidController(); adds bank-angle pitch compensation in computePidLevelTarget().
external-configurator_mod/js/flightModes.js: adds LEVEL to the configurator AUX mode list.

---

# DIVE Mode Implementation

DIVE is an AUX-selectable throttle-limiting mode for fixed-wing aircraft. When active, it asymmetrically attenuates throttle as a function of nose-down pitch angle, leaving throttle untouched during level or nose-up flight. At `dive_max_dive_angle` degrees nose-down, throttle is reduced to idle; between 0° and that threshold, attenuation is proportional. This allows the motor to spool back automatically during dives while still being available the moment the nose comes up.

Requires accelerometer. Mutually exclusive with nothing — it stacks on top of whatever flight mode is active.

## Configuration

```
set dive_max_dive_angle = 30    # Nose-down angle at which throttle hits idle (0-90°, default 30)
```

Setting `dive_max_dive_angle = 0` cuts throttle to idle at any nose-down pitch.

## Key Files

- `src/main/flight/dive_mode.c` — throttle attenuation logic and parameter group registration
- `src/main/flight/dive_mode.h` — DIVE config struct and function declaration
- `src/main/fc/fc_core.c` — calls `applyDiveThrottleAttenuation()` in the RC command path
- `src/main/fc/rc_modes.h` — adds BOXDIVE (ID 62)
- `src/main/fc/fc_msp_box.c` — exposes DIVE as an MSP/AUX mode with permanent ID 71
- `src/main/config/parameter_group_ids.h` — adds PG_DIVE_CONFIG (1047)
- `src/main/fc/settings.yaml` — adds `dive_max_dive_angle`

---

# PATH Mode Implementation

PATH (Pilot Assisted Target Heading) is an AUX-selectable, pilot-supervised roll-steering mode: it autonomously banks the aircraft along a sequential pure-pursuit route through the loaded mission's waypoints (starting at WP1), using LEVEL mode's attitude control, while the pilot retains full pitch, yaw, and throttle authority throughout (SAFE — Supervised Altitude Failsafe Extension). Pitch always passes directly from the stick, letting the pilot manage airspeed, AoA, and altitude without constraint; the pilot can correct airspeed/AoA, adjust heading via rudder, or simply disengage at any time - PATH only ever takes the roll axis.

Unlike NAV RTH/NAV_WP_MODE, PATH is not a navigation FSM state - it has no altitude, energy, or mission-action handling, and never touches `posControl.navState` or `posControl.activeWaypointIndex`. Each loop it computes the bearing and heading error to its current target waypoint (ignoring altitude), commands a bank angle proportional to that error (scaled by `recall_steering_gain` and constrained to LEVEL's `max_angle_inclination_rll`), and writes only `rcCommand[ROLL]`.

PATH maintains its own waypoint cursor, independent of `NAV_WP_MODE`/RTH state. On engagement it starts at WP1 and advances to the next waypoint once the current one is reached (or missed, by the same distance/bearing-divergence test `NAV_WP_MODE` uses). Only plain `NAV_WP_ACTION_WAYPOINT` entries are understood; reaching the end of the route, or encountering any other action type, ends route-following - PATH continues providing roll stabilization (wings-level, zero heading-error target) but stops steering toward a point. Disengaging and re-engaging PATH always restarts the route from WP1.

If no mission is loaded (or it's invalid), PATH has no route and behaves the same as "end of route": wings-level via LEVEL mode, with no heading correction. This is not advisable for actual recovery, but it's apparent in flight when PATH isn't steering anywhere, so the pilot can verify a mission is loaded before relying on it.

Requires GPS fix and accelerometer. Auto-enables LEVEL_MODE (whose bank-angle pitch compensation reacts proactively to PATH's commanded roll target) and punches through the MANUAL_MODE exclusion while active; HEADFREE is blocked when PATH is active.

## Configuration

```
set recall_steering_gain = 50    # Gain applied to heading error to produce bank angle, scaled by 0.01 (1-200, default 50)
```

## Key Files

- `src/main/flight/recall_mode.c` / `.h` — sequential pure-pursuit steering logic, PATH's own waypoint cursor, and PG_RECALL_CONFIG registration
- `src/main/flight/pid.c` — `computePidLevelTarget()`'s LEVEL-mode bank-angle pitch compensation, which PATH relies on while banking
- `src/main/fc/fc_core.c` — calls `applyRecallSteering()` in the RC command path
- `src/main/fc/rc_modes.h` — adds BOXRECALL (ID 64)
- `src/main/fc/fc_msp_box.c` — exposes PATH as an MSP/AUX mode with permanent ID 74
- `src/main/config/parameter_group_ids.h` — adds PG_RECALL_CONFIG (1049)
- `src/main/fc/settings.yaml` — adds `recall_steering_gain`
