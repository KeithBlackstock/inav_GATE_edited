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

# ATTITUDE Mode Implementation

This branch (`feature/attitude-mode`) adds a new flight mode called **ATTITUDE** to INAV. ATTITUDE mode provides direct attitude control without the cascaded rate loop used by ANGLE mode.

## What is ATTITUDE Mode?

ATTITUDE mode functions similarly to ANGLE mode in terms of setting attitude targets from stick inputs, but uses a fundamentally different control approach:

- **ANGLE mode**: Uses cascaded control (Attitude → Rate → Motors)
- **ATTITUDE mode**: Uses direct control (Attitude → Motors)

### Key Differences from ANGLE Mode:

1. **Non-cascaded PID**: Applies PID directly to attitude error without an intermediate rate controller
2. **Throw percentage rates**: Uses 0-100% scaling instead of deg/s for more intuitive tuning
3. **Direct response**: More immediate attitude correction without rate loop dynamics

## Configuration

Three new CLI settings control the mode's responsiveness:

```
attitude_rate_roll = 50    # Roll rate as percentage (0-100, default 50)
attitude_rate_pitch = 50   # Pitch rate as percentage (0-100, default 50)
attitude_rate_yaw = 50     # Yaw rate as percentage (0-100, default 50)
```

Higher percentages = more aggressive response to attitude errors.

## Files Modified

### Core Flight Mode Infrastructure:
- `src/main/fc/runtime_config.h` - Added ATTITUDE_MODE flag (bit 20)
- `src/main/fc/rc_modes.h` - Added BOXATTITUDE (ID 61)
- `src/main/fc/fc_msp_box.c` - Registered mode with permanent ID 70
- `src/main/fc/fc_core.c` - Added mode activation logic

### ATTITUDE Mode Implementation:
- `src/main/flight/attitude_mode.h` - Configuration structure
- `src/main/flight/attitude_mode.c` - Parameter group registration
- `src/main/flight/pid.c` - Direct attitude PID controller (`pidAttitude()` function)

### Configuration & Settings:
- `src/main/config/parameter_group_ids.h` - Added PG_ATTITUDE_CONFIG (1046)
- `src/main/fc/settings.yaml` - Added three rate settings
- `docs/Settings.md` - Documented CLI settings
- `docs/development/msp/inav_enums.json` - Updated MSP enums


---

**Note**: This is an experimental flight mode. Test thoroughly in a safe environment before regular use.
