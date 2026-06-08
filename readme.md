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

Key modified files:

src/main/fc/rc_modes.h: adds BOXLEVEL (Box ID 61).
src/main/fc/fc_msp_box.c: exposes LEVEL as an MSP/AUX mode with permanent ID 71.
src/main/fc/runtime_config.h: adds LEVEL_MODE flag (bit 20).
src/main/fc/runtime_config.c: activates LEVEL_MODE when BOXLEVEL is selected.
src/main/flight/pid.c: routes LEVEL through pidLevel() with horizonRateMagnitude blend; extends ANGLE/HORIZON checks to include LEVEL throughout pidController().
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

# RECALL Mode Implementation

RECALL is an AUX-selectable proportional 2D GPS steering mode that banks the aircraft toward the home waypoint using LEVEL mode's attitude control. Unlike NAV RTH, it is a minimalist steering-only mode — no altitude, energy, or navigation management. It computes the bearing and heading error to home, commands a bank angle proportional to that error (scaled by `recall_steering_gain` and constrained to LEVEL's `max_angle_inclination_rll`), and zeroes pitch and yaw. The pilot retains throttle authority only.

Requires GPS fix, home position, and accelerometer. Auto-enables LEVEL_MODE and punches through the MANUAL_MODE exclusion while active; HEADFREE is blocked when RECALL is active.

## Configuration

```
set recall_steering_gain = 50    # Gain applied to heading error to produce bank angle, scaled by 0.01 (1-200, default 50)
```

## Key Files

- `src/main/flight/recall_mode.c` / `.h` — proportional heading-error steering logic and PG_RECALL_CONFIG registration
- `src/main/fc/fc_core.c` — calls `applyRecallSteering()` in the RC command path
- `src/main/fc/rc_modes.h` — adds BOXRECALL (ID 64)
- `src/main/fc/fc_msp_box.c` — exposes RECALL as an MSP/AUX mode with permanent ID 74
- `src/main/config/parameter_group_ids.h` — adds PG_RECALL_CONFIG (1049)
- `src/main/fc/settings.yaml` — adds `recall_steering_gain`
