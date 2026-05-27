#include "gated_mode.h"

#include "fc/rc_controls.h"
#include "fc/rc_modes.h"
#include "flight/imu.h"
#include "common/maths.h"
#include "pg/pg.h"
#include "config/parameter_group_ids.h"

PG_REGISTER_WITH_RESET_TEMPLATE(gatedConfig_t, gatedConfig, PG_GATED_CONFIG, 0,
    .maxBankAngle = 30
);

void applyGatedRollAttenuation(void)
{
    if (!IS_RC_MODE_ACTIVE(BOXGATED)) {
        return;
    }

    const float maxAngle = (float)gatedConfig()->maxBankAngle;
    if (maxAngle <= 0.0f) {
        return;
    }

    const float rollAngle = (float)attitude.values.roll / 10.0f;
    const float rollInput = rcCommand[ROLL];

    float scale = 1.0f;

    if (rollAngle > 0.0f && rollInput > 0.0f) {
        scale = 1.0f - constrainf(rollAngle / maxAngle, 0.0f, 1.0f);
    } else if (rollAngle < 0.0f && rollInput < 0.0f) {
        scale = 1.0f - constrainf(-rollAngle / maxAngle, 0.0f, 1.0f);
    }

    rcCommand[ROLL] *= scale;
}
