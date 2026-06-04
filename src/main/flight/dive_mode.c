#include "dive_mode.h"

#include "fc/rc_controls.h"
#include "fc/rc_modes.h"
#include "flight/imu.h"
#include "flight/mixer.h"
#include "common/maths.h"
#include "config/parameter_group.h"
#include "config/parameter_group_ids.h"

PG_REGISTER_WITH_RESET_TEMPLATE(diveConfig_t, diveConfig, PG_DIVE_CONFIG, 0);
PG_RESET_TEMPLATE(diveConfig_t, diveConfig,
    .maxDiveAngle = 30
);

void applyDiveThrottleAttenuation(void)
{
    if (!IS_RC_MODE_ACTIVE(BOXDIVE)) {
        return;
    }

    // Positive pitch = nose down in INAV convention. Nose-up or level gets full throttle passthrough.
    const float pitchAngle = (float)attitude.values.pitch / 10.0f;
    if (pitchAngle <= 0.0f) {
        return;
    }

    const float maxAngle = (float)diveConfig()->maxDiveAngle;
    const float scale = (maxAngle <= 0.0f) ? 0.0f : 1.0f - constrainf(pitchAngle / maxAngle, 0.0f, 1.0f);

    // Attenuate only the throttle above idle; at scale=0 throttle falls to idle
    const int16_t idleThrottle = (int16_t)getThrottleIdleValue();
    const int16_t throttleAbove = rcCommand[THROTTLE] - idleThrottle;
    if (throttleAbove > 0) {
        rcCommand[THROTTLE] = idleThrottle + (int16_t)((float)throttleAbove * scale);
    }
}
