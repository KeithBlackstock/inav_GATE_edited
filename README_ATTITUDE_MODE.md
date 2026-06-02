# ATTITUDE Mode Implementation

This branch (`feature/attitude-mode`) adds a new flight mode called **ATTITUDE** to INAV. ATTITUDE mode provides direct attitude control without the cascaded rate loop used by ANGLE mode.

## What is ATTITUDE Mode?

ATTITUDE mode functions similarly to ANGLE mode in terms of setting attitude targets from stick inputs, but uses a fundamentally different control approach:

- **ANGLE mode**: Uses cascaded control (Attitude → Rate → Motors)
- **ATTITUDE mode**: Uses direct control (Attitude → Motors)

### Key Differences from ANGLE Mode:

1. **Non-cascaded PID**: Applies PID directly to attitude error without an intermediate rate controller
2. **Classic PID only**: Uses P, I, and D terms (no feedforward)
3. **Throw percentage rates**: Uses 0-100% scaling instead of deg/s for more intuitive tuning
4. **Direct response**: More immediate attitude correction without rate loop dynamics

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

## Technical Implementation

### Direct Attitude PID Controller (`pidAttitude()`)

Located in `src/main/flight/pid.c`, this function implements classic PID control:

**P-term**: Proportional to attitude error
```c
pTerm = angleErrorDeg * (P_GAIN * MULTIPLIER)
```

**I-term**: Integral of attitude error with limiting
```c
integral += angleErrorDeg * (I_GAIN * MULTIPLIER) * dT
integral = constrain(integral, -50% of max, +50% of max)
```

**D-term**: Uses gyro rate as derivative (opposes rotation)
```c
dTerm = -gyroRate * (D_GAIN * MULTIPLIER)
```

**Output**: Combined and scaled by throw percentage
```c
output = constrain(P + I + D, -maxOutput, +maxOutput)
```

### Control Flow

1. User activates ATTITUDE mode via AUX switch
2. `fc_core.c` enables ATTITUDE_MODE flag
3. `pidController()` detects ATTITUDE_MODE at line ~1330
4. Calls `pidAttitude()` instead of `pidLevel()`
5. Direct PID output goes to motors (bypasses rate controller)

## Mode Behavior

- **Mutually exclusive** with ANGLE, HORIZON, and ANGLEHOLD modes
- **Compatible** with navigation modes (ALTHOLD, POSHOLD, RTH, etc.)
- **LED indicator**: LED1 turns on when active (same as ANGLE/HORIZON)
- **Stick input**: Same as ANGLE mode - stick position = desired attitude

## Usage

1. Configure an AUX channel to activate ATTITUDE mode
2. Adjust `attitude_rate_*` settings via CLI for desired responsiveness
3. Tune using existing LEVEL PID gains (P, I, D)
4. Test in safe environment before normal flight

## Building

This branch is ready for GitHub Actions build. The firmware will include ATTITUDE mode alongside existing flight modes.

## Commits

1. `386e6693f` - Add ATTITUDE mode infrastructure and configuration
2. `7df15bd76` - Implement direct attitude PID controller

## Related Configurator Changes

The configurator branch `feature/configurator-gated-support` includes:
- ATTITUDE mode in flight modes list
- Transpiler support for programming framework
- Mode selection in auxiliary configuration

---

**Note**: This is an experimental flight mode. Test thoroughly in a safe environment before regular use.