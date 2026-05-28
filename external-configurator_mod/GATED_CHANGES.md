# INAV Configurator - GATED Mode Support

## Overview
This document describes the changes made to the INAV Configurator to support the GATED flight mode feature added to INAV firmware version 9.0.1.

## GATED Mode Description
GATED is an AUX-selectable roll limiting mode that progressively attenuates pilot roll input as the aircraft approaches a configured maximum bank angle. Key characteristics:
- **Progressive attenuation**: Roll input is reduced linearly from 0% at level to 100% at max bank angle
- **Asymmetric behavior**: Only attenuates roll input in the same direction as current bank angle
- **Always escapable**: Opposite-direction roll input remains unaffected
- **Non-invasive**: Does not auto-level or create a primary flight mode
- **Requires accelerometer**: Needs ACC sensor to measure bank angle

## Files Modified

### 1. `/js/flightModes.js`
**Purpose**: Define GATED mode for the configurator

**Changes**:
```javascript
{
    boxId: 60,
    boxName: "GATED",
    permanentId: 69
}
```

**Details**:
- Added GATED mode entry to the FLIGHT_MODES array
- `boxId: 60` matches BOXGATED enum value in firmware
- `permanentId: 69` matches MSP permanent ID in firmware
- `boxName: "GATED"` is the display name

### 2. `/locale/en/messages.json`
**Purpose**: Add English translations for GATED mode

**Changes**:
```json
"auxiliaryModeGATED": {
    "message": "GATED"
},
"auxiliaryModeGATEDDescription": {
    "message": "Roll limiting mode that progressively attenuates roll input as bank angle approaches the configured maximum. Does not auto-level. Requires accelerometer."
},
"configurationGated": {
    "message": "GATED Mode Settings"
},
"configurationGatedMaxBankAngle": {
    "message": "GATED Max Bank Angle"
},
"configurationGatedMaxBankAngleHelp": {
    "message": "Maximum bank angle (5-85°) allowed in GATED mode. Roll input is progressively reduced as this angle is approached, but opposite direction input remains available."
}
```

**Details**:
- `auxiliaryModeGATED`: Mode name in Modes tab
- `auxiliaryModeGATEDDescription`: Tooltip/description for the mode
- `configurationGated`: Section title in Configuration tab
- `configurationGatedMaxBankAngle`: Setting label
- `configurationGatedMaxBankAngleHelp`: Help tooltip for the setting

### 3. `/tabs/configuration.html`
**Purpose**: Add UI controls for GATED configuration

**Changes**:
Added new configuration section after the headtracker section:
```html
<div class="config-section gui_box grey config-gated">
    <div class="gui_box_titlebar">
        <div class="spacer_box_title" data-i18n="configurationGated"></div>
    </div>
    <div class="spacer_box">
        <div class="number">
            <input type="number" id="gated_max_bank_angle" name="gated_max_bank_angle" 
                   step="1" min="5" max="85" data-setting="gated_max_bank_angle" />
            <label for="gated_max_bank_angle">
                <span data-i18n="configurationGatedMaxBankAngle"></span>
                <span>°</span>
            </label>
            <div for="gated_max_bank_angle" class="helpicon cf_tip" 
                 data-i18n_title="configurationGatedMaxBankAngleHelp"></div>
        </div>
    </div>
</div>
```

**Details**:
- Input field for `gated_max_bank_angle` setting
- Range: 5-85 degrees (matches firmware constraints)
- Uses `data-setting` attribute for automatic CLI integration
- Includes help icon with tooltip
- Follows existing configurator UI patterns

### 4. `/tabs/configuration.js`
**Purpose**: Handle GATED configuration logic

**Changes**: None required

**Details**:
- The Settings framework automatically handles inputs with `data-setting` attributes
- No additional JavaScript code needed
- Settings are read/written via CLI protocol automatically

### 5. `/tabs/auxiliary.js`
**Purpose**: Add GATED to mode display categories

**Changes**:
```javascript
modeSections["Flight Mode Modifiers"] = [
    "NAV ALTHOLD", "HEADING HOLD", "AIR MODE", "SOARING", 
    "SURFACE", "TURN ASSIST", "GATED"
];
```

**Details**:
- Added GATED to "Flight Mode Modifiers" category
- This controls the display order and grouping in the Modes tab
- GATED appears at the end of the Flight Mode Modifiers section

## Firmware Integration

### MSP Protocol
The configurator communicates with the firmware using:
- **MSP_BOXIDS**: Retrieves list of available modes (includes BOXGATED = 60)
- **MSP_BOXNAMES**: Retrieves mode names (includes "GATED")
- **CLI Protocol**: Reads/writes `gated_max_bank_angle` setting

### Setting Details
- **CLI Command**: `gated_max_bank_angle`
- **Type**: uint8_t (integer)
- **Range**: 5-85 degrees
- **Default**: 30 degrees
- **Parameter Group**: PG_GATED_CONFIG (ID: 1045)

## User Workflow

### Enabling GATED Mode
1. Open INAV Configurator
2. Connect to flight controller with GATED firmware
3. Navigate to **Modes** tab
4. Find "GATED" in the "Flight Mode Modifiers" section
5. Assign GATED to an AUX channel
6. Configure range (typically full switch range)
7. Save settings

### Configuring GATED Settings
1. Navigate to **Configuration** tab
2. Scroll to "GATED Mode Settings" section
3. Adjust "GATED Max Bank Angle" (5-85°)
4. Click "Save and Reboot"

### Using GATED Mode
1. Arm the aircraft
2. Toggle the assigned AUX switch to enable GATED
3. Roll input will be progressively limited as bank angle increases
4. Toggle switch off to disable GATED and return to normal control

## Testing Checklist

- [ ] GATED appears in Modes tab under "Flight Mode Modifiers"
- [ ] Can assign GATED to an AUX channel
- [ ] GATED mode indicator shows active when switch is enabled
- [ ] Configuration tab shows "GATED Mode Settings" section
- [ ] Can adjust `gated_max_bank_angle` value (5-85 range enforced)
- [ ] Setting persists after save and reboot
- [ ] CLI command `get gated_max_bank_angle` works
- [ ] CLI command `set gated_max_bank_angle = 45` works
- [ ] Mode is grayed out if no accelerometer detected (firmware-side check)
- [ ] Help tooltips display correctly

## Compatibility

### Backward Compatibility
- **With GATED firmware**: Full functionality
- **With non-GATED firmware**: Mode won't appear (not in MSP_BOXNAMES response)
- **Setting compatibility**: CLI will return error if firmware doesn't support the setting

### Forward Compatibility
- Permanent ID 69 ensures mode is recognized across firmware versions
- Mode definition follows standard INAV patterns

## Translation Notes

Currently only English translations are provided. To add support for other languages:

1. Copy the translation keys from `/locale/en/messages.json`
2. Add to other language files:
   - `/locale/ja/messages.json` (Japanese)
   - `/locale/ru/messages.json` (Russian)
   - `/locale/uk/messages.json` (Ukrainian)
   - `/locale/zh_CN/messages.json` (Chinese)

Translation keys to add:
- `auxiliaryModeGATED`
- `auxiliaryModeGATEDDescription`
- `configurationGated`
- `configurationGatedMaxBankAngle`
- `configurationGatedMaxBankAngleHelp`

## Build and Deployment

### Building the Configurator
```bash
cd inav-configurator_GATE_edited
npm install
npm start
```

### Testing with Firmware
1. Flash INAV firmware with GATED support to flight controller
2. Run modified configurator
3. Connect to flight controller
4. Verify GATED mode appears and functions correctly

## Summary of Changes

| File | Lines Changed | Type |
|------|---------------|------|
| js/flightModes.js | +5 | Addition |
| locale/en/messages.json | +15 | Addition |
| tabs/configuration.html | +15 | Addition |
| tabs/auxiliary.js | +1 | Modification |
| **Total** | **~36 lines** | **4 files** |

## Notes

- All changes follow existing INAV Configurator patterns and conventions
- No breaking changes to existing functionality
- Settings framework handles all CLI communication automatically
- Mode will only appear if firmware supports it (graceful degradation)
- UI follows existing styling and layout conventions

## Version Information

- **INAV Firmware Version**: 9.0.1 (with GATED support)
- **Configurator Base**: Latest INAV Configurator from GitHub
- **Modification Date**: 2026-05-28
- **GATED Mode**: Box ID 60, Permanent ID 69

## Contact

For questions about GATED mode implementation:
- Firmware changes: See `/inav_GATE_edited/README.md`
- Configurator changes: This document