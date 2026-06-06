# RECALL Mode Feature Request

## Overview
RECALL is a proportional 2D GPS steering mode that steers the aircraft toward the home waypoint using LEVEL mode's attitude control settings. Unlike NAV RTH, RECALL is a minimalist steering-only mode with no altitude management, energy management, throttle management, or complex navigation logic.

## Motivation
- **Simplicity**: Predictable, emergent trajectory instead of complex navigation kinematics
- **Manual Control**: Pilot retains full throttle authority for energy management
- **Predictable Behavior**: Uses familiar LEVEL mode attitude limits, not separate NAV tuning

## Core Functionality

### Proportional Heading-Error Steering
- Calculates bearing from current position to home waypoint using GPS
- Calculates 2D heading error between current heading and bearing to home
- Commands bank angle proportional to heading error
- Uses LEVEL mode's `max_angle_inclination_rll` setting for maximum bank angle
- Zeroes pitch and yaw commands; only throttle remains under pilot control

### Requirements
- GPS fix required (mode inactive without GPS)
- Home position must be set
- LEVEL mode must be functional (uses same attitude control)
- Accelerometer required (for LEVEL mode attitude control)

## Configuration Parameters

### `recall_steering_gain`
- **Type**: uint8_t
- **Range**: 0-200
- **Default**: 50
- **Description**: Gain applied to heading error to produce desired bank angle, scaled by 0.01

### Reuses Existing Settings
- `max_angle_inclination_rll` from LEVEL mode - Maximum bank angle for steering
- Home position from GPS/NAV system

## Implementation Details

### Mode Activation
- Box ID: 64 (BOXRECALL)
- Permanent ID: 74
- Requires: GPS fix, home position set, accelerometer
- Appears in configurator Modes tab when GPS sensor detected

### Control Flow
```
1. Check if RECALL mode active via IS_RC_MODE_ACTIVE(BOXRECALL)
2. Verify GPS fix and home position available
3. Calculate bearing to home
4. Calculate desired bank angle from 2D heading error and recall_steering_gain
5. Constrain bank angle to LEVEL mode's max_angle_inclination_rll
6. Convert desired bank angle to rcCommand[ROLL]
7. Zero rcCommand[PITCH] and rcCommand[YAW] — pilot controls throttle only
```

### Proportional Heading-Error Algorithm
```c
// Calculate bearing error in degrees
float bearingToHome = calculateBearing(currentPos, homePos);
float currentHeading = attitude.values.yaw / 10.0f;
float bearingError = bearingToHome - currentHeading;

// Normalize to [-180, 180]
while (bearingError > 180.0f) bearingError -= 360.0f;
while (bearingError < -180.0f) bearingError += 360.0f;

// Calculate desired bank angle (proportional to bearing error)
float gain = recallConfig()->steeringGain * 0.01f;
float desiredBank = bearingError * gain;

// Constrain to LEVEL mode limits
float maxBank = pidProfile()->max_angle_inclination[FD_ROLL] / 10.0f;
desiredBank = constrainf(desiredBank, -maxBank, maxBank);

// Apply via normal LEVEL-mode attitude control path
rcCommand[ROLL] = pidAngleToRcCommand(desiredBank * 10.0f, pidProfile()->max_angle_inclination[FD_ROLL]);
```

## User Interface

### Configurator - Modes Tab
- RECALL appears in mode list when GPS sensor detected
- Can be assigned to AUX channel like other modes
- Active indicator shows when mode is engaged

### Configurator - Configuration Tab
- RECALL steering gain field


## Implementation Files

### Firmware
- `src/main/flight/recall_mode.h` - Header with recallConfig_t structure
- `src/main/flight/recall_mode.c` - Implementation with proportional heading-error steering
- `src/main/fc/rc_modes.h` - Add BOXRECALL = 64
- `src/main/fc/fc_msp_box.c` - Add BOXRECALL entry with permanentId 74
- `src/main/config/parameter_group_ids.h` - Add PG_RECALL_CONFIG
- `src/main/fc/fc_core.c` - Integrate applyRecallSteering() call
- `src/main/fc/settings.yaml` - Add recall_steering_gain setting
- `src/main/CMakeLists.txt` - Add recall_mode.c/h files

### Configurator
- `js/flightModes.js` - Add RECALL mode entry (boxId: 64, permanentId: 74)
- `tabs/configuration.html` - Add RECALL mode settings UI
- `locale/en/messages.json` - Add RECALL mode strings

