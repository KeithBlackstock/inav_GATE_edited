# SPEED Mode Feature Request

## Overview
Implement a GPS-based cruise speed controller for fixed-wing aircraft that automatically modulates throttle to maintain a target airspeed using GPS ground speed as a virtual airspeed sensor.

## Motivation
- Provides hands-free cruise speed control for long-distance flights
- Useful for aircraft without pitot tube sensors
- Simplifies pilot workload during cruise flight
- Enables consistent speed for FPV racing or waypoint missions

## Technical Design

### Flight Mode Characteristics
- **Type**: Flight mode modifier (like DIVE, GATED)
- **Box ID**: 63
- **Permanent ID**: 73
- **Requirements**: GPS fix required
- **Control Method**: Proportional controller adjusting throttle
- **Feedback**: GPS ground speed (cm/s)

### Controller Algorithm
```
speed_error = target_speed - current_gps_speed
throttle_adjustment = speed_error * proportional_gain * 0.01
throttle_output = constrain(base_throttle + adjustment, idle, max)
```

## Implementation Checklist

### Firmware Changes (inav_GATE_edited/)

#### 1. Header File: `src/main/flight/speed_mode.h`
```c
#pragma once

#include <stdint.h>
#include "config/parameter_group.h"

typedef struct speedConfig_s {
    uint16_t targetSpeed;        // Target speed in cm/s
    uint8_t proportionalGain;    // P-gain scaled by 0.01
} speedConfig_t;

PG_DECLARE(speedConfig_t, speedConfig);

void applySpeedThrottleControl(void);
```

#### 2. Implementation File: `src/main/flight/speed_mode.c`
- Check for BOXSPEED mode active
- Verify GPS fix available
- Read GPS ground speed from `gpsSol.groundSpeed`
- Calculate speed error
- Apply proportional control
- Constrain throttle output
- Modulate `rcCommand[THROTTLE]`

#### 3. Runtime Config: `src/main/fc/runtime_config.h`
Add to `flightModeFlags_e`:
```c
SPEED_MODE = (1 << 30),  // GPS cruise speed controller
```

#### 4. RC Modes: `src/main/fc/rc_modes.h`
Add to `boxId_e`:
```c
BOXSPEED = 63,
```

#### 5. MSP Box Registration: `src/main/fc/fc_msp_box.c`
Add entry:
```c
{ .boxId = BOXSPEED, .boxName = "SPEED", .permanentId = 73 },
```

#### 6. Parameter Group IDs: `src/main/config/parameter_group_ids.h`
```c
#define PG_SPEED_CONFIG 1048
```
Update `PG_INAV_END` to reference `PG_SPEED_CONFIG`

#### 7. Core Integration: `src/main/fc/fc_core.c`
- Include `"flight/speed_mode.h"`
- Call `applySpeedThrottleControl()` in RC command processing path
- Place after DIVE mode, before final output

#### 8. Settings Configuration: `src/main/fc/settings.yaml`
```yaml
- name: PG_SPEED_CONFIG
  headers: ["flight/speed_mode.h"]
  type: speedConfig_t
  members:
    - name: speed_target_speed
      description: "Target cruise speed for SPEED mode in cm/s (1500 = 15 m/s = 54 km/h) [100-5000]"
      default_value: 1500
      field: targetSpeed
      min: 100
      max: 5000
    - name: speed_proportional_gain
      description: "Proportional gain for SPEED mode controller (scaled by 0.01, so 50 = 0.50) [1-200]"
      default_value: 50
      field: proportionalGain
      min: 1
      max: 200
```

#### 9. Build System: `src/main/CMakeLists.txt`
Add files to build:
```cmake
flight/speed_mode.c
flight/speed_mode.h
```

### Configurator Changes (external-configurator_mod/)

#### 1. Flight Modes: `js/flightModes.js`
Add entry:
```javascript
{
    boxId: 63,
    boxName: "SPEED",
    permanentId: 73
}
```

#### 2. Configuration Tab: `tabs/configuration.html`
Add settings section after DIVE mode:
```html
<div class="config-section gui_box grey config-speed">
    <div class="gui_box_titlebar">
        <div class="spacer_box_title" data-i18n="configurationSpeed"></div>
    </div>
    <div class="spacer_box">
        <div class="number">
            <input type="number" id="speed_target_speed" name="speed_target_speed" 
                   step="50" min="100" max="5000" data-setting="speed_target_speed" />
            <label for="speed_target_speed">
                <span data-i18n="configurationSpeedTargetSpeed"></span>
                <span>cm/s</span>
            </label>
            <div for="speed_target_speed" class="helpicon cf_tip" 
                 data-i18n_title="configurationSpeedTargetSpeedHelp"></div>
        </div>
        <div class="number">
            <input type="number" id="speed_proportional_gain" name="speed_proportional_gain" 
                   step="1" min="1" max="200" data-setting="speed_proportional_gain" />
            <label for="speed_proportional_gain">
                <span data-i18n="configurationSpeedProportionalGain"></span>
                <span>×0.01</span>
            </label>
            <div for="speed_proportional_gain" class="helpicon cf_tip" 
                 data-i18n_title="configurationSpeedProportionalGainHelp"></div>
        </div>
    </div>
</div>
```

#### 3. Internationalization: `locale/en/messages.json`
Add strings:
```json
"auxiliaryModeSPEED": {
    "message": "SPEED"
},
"auxiliaryModeSPEEDDescription": {
    "message": "GPS-based cruise speed controller that automatically modulates throttle to maintain target airspeed. Uses GPS ground speed as virtual airspeed. Requires GPS fix."
},
"configurationSpeed": {
    "message": "SPEED Mode Settings"
},
"configurationSpeedTargetSpeed": {
    "message": "Target Speed"
},
"configurationSpeedTargetSpeedHelp": {
    "message": "Target cruise speed in cm/s (100-5000). The controller will adjust throttle to maintain this GPS ground speed. Example: 1500 cm/s = 15 m/s = 54 km/h = 33.5 mph."
},
"configurationSpeedProportionalGain": {
    "message": "Proportional Gain"
},
"configurationSpeedProportionalGainHelp": {
    "message": "Proportional controller gain (1-200, scaled by 0.01). Higher values = more aggressive throttle response to speed errors. Start with 50 (0.50) and adjust based on aircraft response."
}
```

## Configuration

### CLI Commands
```
set speed_target_speed = 1500
set speed_proportional_gain = 50
save
```

### Modes Tab
Enable SPEED mode on an AUX channel switch

## Usage

1. Enable SPEED mode via AUX switch
2. Set desired cruise throttle manually
3. SPEED mode will maintain GPS ground speed by adjusting throttle
4. Disable mode to return to manual throttle control

## Tuning Guide

### Initial Setup
- Start with default gain (50 = 0.50)
- Set target speed to typical cruise speed
- Test in calm conditions

### Gain Adjustment
- **Too low**: Slow response, doesn't maintain speed well
- **Too high**: Oscillating throttle, overshooting
- **Optimal**: Smooth corrections, stable speed

### Speed Selection
- Consider wind conditions (GPS ground speed ≠ true airspeed)
- Account for aircraft capabilities
- Test different speeds to find optimal cruise

## Limitations

1. **GPS Ground Speed**: Not true airspeed, affected by wind
2. **No Integral Term**: Won't eliminate steady-state error
3. **No Derivative Term**: May oscillate with aggressive gains
4. **GPS Dependency**: Requires good GPS fix
5. **Fixed-Wing Only**: Not suitable for multirotor

## Future Enhancements

1. Add integral term for steady-state error elimination
2. Add derivative term for damping
3. Implement anti-windup protection
4. Add configurable deadband around target speed
5. Support pitot tube sensor as alternative to GPS
6. Add telemetry for speed error and throttle adjustment
7. Integrate with navigation modes

## Testing Plan

1. **Ground Testing**: Verify mode activation and parameter loading
2. **Flight Testing**: 
   - Test in calm conditions first
   - Verify throttle modulation
   - Check speed maintenance accuracy
   - Test different gain values
   - Verify GPS dependency
3. **Edge Cases**:
   - GPS signal loss
   - Extreme wind conditions
   - Rapid speed changes
   - Mode transitions

## Documentation

Create user documentation covering:
- Feature description
- Configuration steps
- Tuning guide
- Troubleshooting
- Safety considerations

## Related Modes

- **GATED**: Roll limiting (Box ID 60, Permanent ID 69)
- **DIVE**: Throttle attenuation in dives (Box ID 62, Permanent ID 71)
- **LEVEL**: ANGLE/MANUAL blend (Box ID 61, Permanent ID 72)

## Notes

- SPEED mode is a flight mode modifier, not a primary flight mode
- Can be combined with ANGLE, HORIZON, or MANUAL modes
- Does not interfere with pitch/roll/yaw control
- Only modulates throttle channel