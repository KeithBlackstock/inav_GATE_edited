# RECALL Mode Feature Request

## Overview
RECALL is a pure-pursuit GPS steering mode that autonomously flies the aircraft back to the home waypoint using LEVEL mode's attitude control settings. Unlike NAV RTH, RECALL is a minimalist steering-only mode with no altitude management, energy management, or complex navigation logic.

## Motivation
- **Simplicity**: Predictable, emergent trajectoy instead of a complex kinematics
- **Manual Control**: Pilot retains full throttle authority for energy management
- **Predictable Behavior**: Uses familiar LEVEL mode attitude limits, not separate NAV tuning
- **Coast Feature**: Automatic throttle cut when approaching home prevents overshooting

## Core Functionality

### Pure-Pursuit Steering
- Calculates bearing from current position to home waypoint using GPS
- Commands bank angle to steer toward home using pure-pursuit algorithm
- Uses LEVEL mode's `max_angle_inclination_rll` setting for maximum bank angle
- Pilot retains full pitch authority (no altitude control)
- Pilot retains full throttle authority (no speed control)

### Coast Radius
- Configurable proximity radius to home waypoint (e.g., 10-100 meters)
- When aircraft enters coast radius, throttle is automatically cut to idle
- Allows aircraft to glide/coast to landing without overshooting home

### Requirements
- GPS fix required (mode inactive without GPS)
- Home position must be set
- LEVEL mode must be functional (uses same attitude control)
- Accelerometer required (for LEVEL mode attitude control)

## Configuration Parameters

### `recall_coast_radius`
- **Type**: uint16_t
- **Range**: 10-100 meters
- **Default**: 10 meters
- **Description**: Distance from home at which throttle is cut to idle for coasting approach

### Reuses Existing Settings
- `max_angle_inclination_rll` from LEVEL mode - Maximum bank angle for steering
- Home position from GPS/NAV system
- Throttle idle value from motor configuration

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
3. Calculate distance and bearing to home
4. If distance > coast_radius:
   - Calculate desired bank angle using pure-pursuit
   - Constrain to LEVEL mode's max_angle_inclination_rll
   - Apply bank angle via LEVEL mode attitude controller
   - Pilot controls throttle and pitch
5. If distance <= coast_radius:
   - Cut throttle to idle (getThrottleIdleValue())
   - Continue steering to home
   - Pilot can override by disabling RECALL
```

### Pure-Pursuit Algorithm
```c
// Calculate bearing error
float bearingToHome = calculateBearing(currentPos, homePos);
float currentHeading = attitude.values.yaw / 10.0f;
float bearingError = bearingToHome - currentHeading;

// Normalize to [-180, 180]
while (bearingError > 180.0f) bearingError -= 360.0f;
while (bearingError < -180.0f) bearingError += 360.0f;

// Calculate desired bank angle (proportional to bearing error)
float desiredBank = bearingError * RECALL_PURSUIT_GAIN;

// Constrain to LEVEL mode limits
float maxBank = levelModeConfig()->max_angle_inclination_rll / 10.0f;
desiredBank = constrainf(desiredBank, -maxBank, maxBank);

// Apply via LEVEL mode attitude controller
applyLevelModeAttitude(desiredBank, pilotPitchInput);
```

### Throttle Coast Logic
```c
float distanceToHome = calculateDistance(currentPos, homePos);

if (distanceToHome <= recallConfig()->coastRadius) {
    // Cut throttle to idle
    rcCommand[THROTTLE] = getThrottleIdleValue();
}
// Otherwise pilot controls throttle normally
```

## User Interface

### Configurator - Modes Tab
- RECALL appears in mode list when GPS sensor detected
- Can be assigned to AUX channel like other modes
- Active indicator shows when mode is engaged

### Configurator - Configuration Tab
New "RECALL Mode Settings" section:
- **Coast Radius**: Input field, 10-100 meters, unit: m
- Help text: "Distance from home at which throttle cuts to idle for coasting approach"

### OSD Elements (Optional Future Enhancement)
- Distance to home
- Bearing to home arrow
- "COAST" indicator when in coast radius


## Implementation Files

### Firmware
- `src/main/flight/recall_mode.h` - Header with recallConfig_t structure
- `src/main/flight/recall_mode.c` - Implementation with pure-pursuit and coast logic
- `src/main/fc/rc_modes.h` - Add BOXRECALL = 64
- `src/main/fc/fc_msp_box.c` - Add BOXRECALL entry with permanentId 74
- `src/main/config/parameter_group_ids.h` - Add PG_RECALL_CONFIG
- `src/main/fc/fc_core.c` - Integrate applyRecallSteering() call
- `src/main/fc/settings.yaml` - Add recall_coast_radius setting
- `src/main/CMakeLists.txt` - Add recall_mode.c/h files

### Configurator
- `js/flightModes.js` - Add RECALL mode entry (boxId: 64, permanentId: 74)
- `tabs/configuration.html` - Add RECALL mode settings UI
- `locale/en/messages.json` - Add RECALL mode strings

