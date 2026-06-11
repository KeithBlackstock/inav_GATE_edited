# RECALL Drop Speed Failsafe Feature Request

## Overview
Add an automatic RECALL exit when the barometer/INS detects an excessive
descent rate, handing control back to the pilot under their selected manual
mode (e.g. BOXLEVEL/BOXANGLE) instead of RECALL's autonomous steering. This
prevents uncontrolled descents during GPS-guided return by returning the
aircraft to pilot-flown self-leveling rather than continuing to run RECALL's
own (already-LEVEL_MODE) steering logic.

## Motivation
- Prevents stall/dive-induced crashes during RECALL operation
- Gives the pilot control back under self-leveling assistance the moment
  RECALL appears to be losing the aircraft
- Safety layer for GPS-assisted flight

## Why not just enable LEVEL_MODE?
RECALL already forces `LEVEL_MODE` on for its entire duration
(`fc_core.c`, `isRecallModeAvailable()` is OR'd into the BOXLEVEL check), and
`applyRecallSteering()` overwrites `rcCommand[ROLL]/[PITCH]` every loop
regardless of that flag. `LEVEL_MODE` is a single bitflag consumed identically
by the PID controller no matter who/what enabled it — calling
`enableFlightMode(LEVEL_MODE)` again during RECALL would be a no-op.

To actually return the aircraft to pilot-controlled self-leveling, RECALL
itself must be exited so `applyRecallSteering()` stops overriding
`rcCommand`. With RECALL no longer "available", `fc_core.c`'s existing
mode-priority block falls through to whatever the pilot has selected
(BOXANGLE/BOXLEVEL/BOXANGLEHOLD/manual), restoring real stick control.

## Technical Design

### Detection & Exit Logic
A latch inside `recall_mode.c` causes `isRecallModeAvailable()` to report
`false` once an excessive descent rate is detected, exiting RECALL until the
pilot cycles the RECALL switch off and back on.

```c
static bool dropSpeedFailsafeLatched = false;

bool isRecallModeAvailable(void)
{
    if (dropSpeedFailsafeLatched) {
        return false;
    }

    return IS_RC_MODE_ACTIVE(BOXRECALL) &&
           sensors(SENSOR_ACC) &&
           STATE(GPS_FIX);
}

void checkRecallDropSpeedFailsafe(void)
{
    if (!IS_RC_MODE_ACTIVE(BOXRECALL)) {
        dropSpeedFailsafeLatched = false;  // reset when pilot deactivates RECALL
        return;
    }

    if (dropSpeedFailsafeLatched || !isRecallModeAvailable()) {
        return;
    }

    float descentRate = getEstimatedActualVelocity(Z);  // cm/s, negative = down

    if (descentRate < -recallConfig()->dropSpeedThreshold) {
        dropSpeedFailsafeLatched = true;
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
    uint16_t dropSpeedThreshold;  // New: descent rate exit threshold in cm/s
} recallConfig_t;

void checkRecallDropSpeedFailsafe(void);  // New function
```

### Settings (`src/main/fc/settings.yaml`)
```yaml
- name: recall_drop_speed_threshold
  description: "Descent rate exit threshold for RECALL in cm/s [500-5000]"
  default_value: 1500
  min: 500
  max: 5000
```

### Integration (`src/main/fc/fc_core.c`)
`checkRecallDropSpeedFailsafe()` must run *before* the flight-mode
priority block that calls `isRecallModeAvailable()` (the block enabling
ANGLE/HORIZON/LEVEL/ANGLEHOLD), so a trigger this loop already causes RECALL
to be reported unavailable and the fallthrough to the pilot's selected mode
to take effect immediately:

```c
checkRecallDropSpeedFailsafe();  // Add before the ANGLE/HORIZON/LEVEL/ANGLEHOLD priority block

DISABLE_FLIGHT_MODE(ANGLE_MODE);
DISABLE_FLIGHT_MODE(HORIZON_MODE);
DISABLE_FLIGHT_MODE(LEVEL_MODE);
DISABLE_FLIGHT_MODE(ANGLEHOLD_MODE);
...
```

### Configurator (`tabs/configuration.html`)
```html
<input type="number" id="recall_drop_speed_threshold"
       step="100" min="500" max="5000" data-setting="recall_drop_speed_threshold" />
<label>Drop Speed Threshold (cm/s)</label>
```
