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

Known issues / future patches:

1. Box ID conflict: BOXLEVEL is assigned ID 61 on this branch. On the main branch, BOXATTITUDE also uses ID 61. These will collide if this branch is merged into main without renumbering one of them. Resolution: reassign BOXLEVEL to the next available ID (currently 62) and update its permanent ID accordingly.

2. pidLevel() blend is identical to HORIZON: the current implementation blends rateTarget using the same formula as HORIZON mode. This means LEVEL and HORIZON behave identically at runtime — the "manual passthrough" intent is not yet realized. To achieve true passthrough at full stick, the rate PID step that follows pidLevel() must be bypassed (or its output zeroed/passthrough-mapped) when LEVEL_MODE is active and horizonRateMagnitude approaches 1.0. The blend in pidLevel() itself is correct; the missing piece is suppressing the downstream rate controller.
