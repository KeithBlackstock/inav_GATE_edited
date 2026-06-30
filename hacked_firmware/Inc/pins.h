#ifndef PINS_H
#define PINS_H

/*
 * HobbyEagle A3 LQFP48 pin mapping – Revision 4 (discovered architecture).
 *
 * This revision replaces the NAZE32 cross-reference guesses (Rev 3) with pins
 * traced directly from the A3 hardware.  The IMU is an ICM-42688-P on SPI2,
 * not I2C as previously assumed.  PB15 (SPI2_MOSI) is shared with LED_B —
 * both functions sit on the same physical net.
 *
 * Confidence tags:
 *   [CONFIRMED] – driven in firmware, result observed on real hardware.
 *   [TRACED]    – traced from the board; not yet exercised in firmware.
 *   [INFERRED]  – follows necessarily from a CONFIRMED/TRACED pin (e.g. the
 *                 remaining SPI2 bus lines once PB15=SPI2_MOSI was confirmed).
 *   [OPEN]      – tested, result ambiguous; see inline note.
 *   [GUESS]     – untested hypothesis.
 *
 * Confirmed observations carried forward from prior firmware tests:
 *   PB15 = clean blue, PA9 = clean red – both distinct from the dim violet
 *   leakage glow present on this LED package when no channel is driven.
 *
 * PA8 (LED_G) remains [OPEN]: round-robin drove it for its full window with
 * no visible change from baseline.  Green has a higher forward voltage than
 * red/blue, so the die may simply stay dark under leakage-level current and
 * only light at a full GPIO drive.  Needs an isolated retest before any
 * confidence tag is added.
 */

/* ── LEDs ───────────────────────────────────────────────────────────────── */

#define PIN_LED_B_PORT          GPIOB
#define PIN_LED_B_PIN           GPIO_PIN_15  /* PB15 - SPI2_MOSI / TIM1_CH3N    -- [CONFIRMED] clean blue. Shares physical net with IMU SPI2_MOSI. */

#define PIN_LED_G_PORT          GPIOA
#define PIN_LED_G_PIN           GPIO_PIN_8   /* PA8  - TIM1_CH1 / MCO             -- [OPEN] no visible response during round-robin; needs isolated full-drive retest. */

#define PIN_LED_R_PORT          GPIOA
#define PIN_LED_R_PIN           GPIO_PIN_9   /* PA9  - USART1_TX / TIM1_CH2       -- [CONFIRMED] clean red. */

/* ── IMU – ICM-42688-P on SPI2 ──────────────────────────────────────────── */
/*
 * PB15 (SPI2_MOSI) confirmed as LED_B anchors SPI2 as the IMU bus.
 * PB13 and PB14 are the only SPI2_SCK / SPI2_MISO lines available on the
 * LQFP48 package and follow by necessity.  PB5 is traced as the dedicated
 * GPIO chip-select.  IMU_INT is not yet located and is omitted.
 *
 * Note: PB15 driving the blue LED during SPI2 transactions is expected —
 * every MOSI byte will flicker the LED at bus speed.  Account for this in
 * any LED-state logic.
 */

#define PIN_IMU_SCK_PORT        GPIOB
#define PIN_IMU_SCK_PIN         GPIO_PIN_13  /* PB13 - SPI2_SCK                   -- [INFERRED] only SPI2_SCK on this package */

#define PIN_IMU_MISO_PORT       GPIOB
#define PIN_IMU_MISO_PIN        GPIO_PIN_14  /* PB14 - SPI2_MISO                  -- [INFERRED] only SPI2_MISO on this package */

#define PIN_IMU_MOSI_PORT       GPIOB
#define PIN_IMU_MOSI_PIN        GPIO_PIN_15  /* PB15 - SPI2_MOSI                  -- [CONFIRMED] shared physical net with LED_B */

#define PIN_IMU_CS_PORT         GPIOB
#define PIN_IMU_CS_PIN          GPIO_PIN_5   /* PB5  - I2C1_SMBA / TIM3_CH2       -- [TRACED] GPIO output, dedicated IMU chip select */

/* ── Servo outputs ──────────────────────────────────────────────────────── */

#define PIN_OUT1_PORT           GPIOA
#define PIN_OUT1_PIN            GPIO_PIN_5   /* PA5  - SPI1_SCK / TIM2_CH1_ETR / ADC12_IN5 -- [TRACED] Servo Output 1 */

#define PIN_OUT2_PORT           GPIOA
#define PIN_OUT2_PIN            GPIO_PIN_6   /* PA6  - TIM3_CH1 / SPI1_MISO       -- [TRACED] Servo Output 2 */

#define PIN_OUT3_PORT           GPIOB
#define PIN_OUT3_PIN            GPIO_PIN_0   /* PB0  - TIM3_CH3 / ADC12_IN8       -- [TRACED] Servo Output 3 */

/* ── RC inputs ──────────────────────────────────────────────────────────── */
/*
 * PA2 is electrically USART2_TX.  As the board's S.Bus/PPM input it is most
 * naturally used as TIM2_CH3 (PPM capture) or via software bit-bang; S.Bus
 * on a TX-side UART pin would require external inversion.
 */

#define PIN_RX_INPUT_PORT       GPIOA
#define PIN_RX_INPUT_PIN        GPIO_PIN_2   /* PA2  - USART2_TX / TIM2_CH3       -- [TRACED] S.Bus / PPM input */

#define PIN_AIL_THR_PORT        GPIOA
#define PIN_AIL_THR_PIN         GPIO_PIN_3   /* PA3  - USART2_RX / TIM2_CH4       -- [TRACED] physical 3-pin servo input rail (AIL / Throttle) */

#define PIN_RUD_PORT            GPIOA
#define PIN_RUD_PIN             GPIO_PIN_11  /* PA11 - TIM1_CH4                   -- [TRACED] physical servo input (Rudder) */

#define PIN_MODE_PORT           GPIOA
#define PIN_MODE_PIN            GPIO_PIN_10  /* PA10 - TIM1_CH3 / USART1_RX       -- [TRACED] physical servo input (Mode Switch) */

/* ── Controls ───────────────────────────────────────────────────────────── */
/*
 * PB12 is traced as the SET button (input pull-up).  It also sits on
 * SPI2_NSS, so it could double as a hardware CS if IMU CS is not separately
 * routed — but PB5 is traced as the dedicated IMU CS, so PB12 is a button.
 */

#define PIN_SET_BUTTON_PORT     GPIOB
#define PIN_SET_BUTTON_PIN      GPIO_PIN_12  /* PB12 - SPI2_NSS                   -- [TRACED] SET button, input pull-up */

/* ── SWD debug ──────────────────────────────────────────────────────────── */

#define PIN_SWDIO_PORT          GPIOA
#define PIN_SWDIO_PIN           GPIO_PIN_13  /* PA13 - SWDIO */

#define PIN_SWCLK_PORT          GPIOA
#define PIN_SWCLK_PIN           GPIO_PIN_14  /* PA14 - SWCLK */

#endif /* PINS_H */
