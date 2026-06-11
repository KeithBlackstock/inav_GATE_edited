# RECALL Drop Speed Failsafe Feature Request

## Overview
Add automatic LEVEL mode activation to RECALL when barometer detects excessive descent rate, preventing uncontrolled descents during GPS-guided return.

## Motivation
- Prevents stall-induced crashes during RECALL operation
- Automatic recovery from excessive sink rates
- Safety layer for GPS-assisted flight

## Technical Design

### Detection Logic
```c
void checkRecallDropSpeedFailsafe(void)
{
    if (!isRecallModeAvailable()) return;
    
    float descentRate = getEstimatedActualVelocity(Z);  // cm/s, negative = down
    
    if (descentRate < -recallConfig()->dropSpeedThreshold) {
        enableFlightMode(LEVEL_MODE);  // Activate failsafe
    }
}
```

### Configuration
- **Setting**: `recall_drop_speed_threshold`
- **Default**: 1500 cm/s (15 m/s / 49 ft/s)
- **Range**: 500-5000 cm/s
- **Tuning**: Lower = more sensitive, Higher = less sensitive

## Implementation

### Firmware (`src/main/flight/recall_mode.h`)
```c
typedef struct recallConfig_s {
    uint8_t steeringGain;
    uint16_t dropSpeedThreshold;  // New: descent rate threshold in cm/s
} recallConfig_t;

void checkRecallDropSpeedFailsafe(void);  // New function
```

### Settings (`src/main/fc/settings.yaml`)
```yaml
- name: recall_drop_speed_threshold
  description: "Descent rate failsafe threshold in cm/s [500-5000]"
  default_value: 1500
  min: 500
  max: 5000
```

### Integration (`src/main/fc/fc_core.c`)
```c
applyRecallSteering();
checkRecallDropSpeedFailsafe();  // Add after RECALL steering
```

### Configurator (`tabs/configuration.html`)
```html
<input type="number" id="recall_drop_speed_threshold" 
       step="100" min="500" max="5000" data-setting="recall_drop_speed_threshold" />
<label>Drop Speed Threshold (cm/s)</label>
```

## Usage
1. Set threshold via CLI: `set recall_drop_speed_threshold = 1500`
2. Enable RECALL mode during flight
3. Failsafe activates automatically if descent exceeds threshold
4. Pilot retains throttle control throughout

## Tuning Guide
- **Conservative (500-1000)**: Earlier intervention, may trigger in turbulence
- **Balanced (1500)**: Default, good for most aircraft
- **Aggressive (2000-5000)**: Only severe descents

## Limitations
- Requires functioning barometer
- Barometer lag may delay detection
- Turbulence may cause false triggers
- Pilot must still manage throttle

## Future Enhancements
- Hysteresis (separate exit threshold)
- Time delay before triggering
- Automatic pitch correction
- Telemetry/blackbox logging

---
**Status**: Feature Request  
**Priority**: Medium  
**Complexity**: Low-Medium  
**Estimated Time**: 4-8 hours