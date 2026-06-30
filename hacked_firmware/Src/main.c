#include <stddef.h>
#include <stdint.h>
#include "stm32f1xx_hal.h"
#include "pins.h"

/*
 * Realtime RX-signal-detect: PA2 (PIN_RX_INPUT, S.Bus / PPM input) is
 * configured as an EXTI input (both edges).  Each edge increments a counter
 * and records the time since the previous edge on that pin (via the DWT
 * cycle counter, converted to microseconds).
 *
 * Nothing is sent over UART.  The volatile counter is read live over SWD by
 * polling through OpenOCD while the target keeps running (never halted) --
 * see hacked_firmware/monitor_rx.py.  That needs no wiring beyond the
 * ST-Link already in use to flash this board.
 *
 * LED_B blinks once per 50 new edges on the RX input as a signal-activity
 * indicator.  LED_R is the unconditional once-a-second liveness heartbeat
 * (both LEDs flash together at the heartbeat).  If the heartbeat stops, the
 * firmware or board is the problem; if it keeps going but LED_B never fires,
 * the RX line is genuinely silent.
 *
 * Note: LED_B (PB15) shares its physical net with SPI2_MOSI (IMU data line).
 * SPI2 is not initialised in this bringup firmware, so there is no conflict
 * here -- but any future firmware that drives SPI2 will visibly flicker the
 * blue LED at bus speed.
 */

typedef struct {
    volatile uint32_t edge_count;
    volatile uint32_t last_period_us;
    volatile uint32_t last_edge_cycle;
} signal_stats_t;

volatile signal_stats_t g_rx_input_stats;

static void dwt_init(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

static uint32_t cycles_to_us(uint32_t cycles)
{
    return cycles / (HAL_RCC_GetHCLKFreq() / 1000000U);
}

static void record_edge(volatile signal_stats_t *stats)
{
    uint32_t now = DWT->CYCCNT;
    if (stats->edge_count != 0) {
        stats->last_period_us = cycles_to_us(now - stats->last_edge_cycle);
    }
    stats->last_edge_cycle = now;
    stats->edge_count++;
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == PIN_RX_INPUT_PIN) {
        record_edge(&g_rx_input_stats);
    }
}

void EXTI2_IRQHandler(void)
{
    HAL_GPIO_EXTI_IRQHandler(PIN_RX_INPUT_PIN);
}

static void exti_input_init(GPIO_TypeDef *port, uint32_t pin, IRQn_Type irqn)
{
    GPIO_InitTypeDef init = {0};
    init.Pin  = pin;
    init.Mode = GPIO_MODE_IT_RISING_FALLING;
    init.Pull = GPIO_PULLDOWN; /* idle low if floating, so a disconnected pin reads as silent rather than noisy */
    HAL_GPIO_Init(port, &init);

    HAL_NVIC_SetPriority(irqn, 1, 0);
    HAL_NVIC_EnableIRQ(irqn);
}

static void led_gpio_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    GPIO_InitTypeDef init = {0};
    init.Mode  = GPIO_MODE_OUTPUT_PP;
    init.Pull  = GPIO_NOPULL;
    init.Speed = GPIO_SPEED_FREQ_LOW;

    init.Pin = PIN_LED_B_PIN;
    HAL_GPIO_Init(PIN_LED_B_PORT, &init);
    init.Pin = PIN_LED_R_PIN;
    HAL_GPIO_Init(PIN_LED_R_PORT, &init);

    HAL_GPIO_WritePin(PIN_LED_B_PORT, PIN_LED_B_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(PIN_LED_R_PORT, PIN_LED_R_PIN, GPIO_PIN_RESET);
}

static void heartbeat_blink(GPIO_TypeDef *port, uint32_t pin)
{
    HAL_GPIO_WritePin(port, pin, GPIO_PIN_SET);
    HAL_Delay(30);
    HAL_GPIO_WritePin(port, pin, GPIO_PIN_RESET);
}

int main(void)
{
    HAL_Init();
    dwt_init();
    led_gpio_init();

    /* GPIOA/GPIOB clocks already enabled by led_gpio_init() above. */
    exti_input_init(PIN_RX_INPUT_PORT, PIN_RX_INPUT_PIN, EXTI2_IRQn);

    uint32_t last_rx_count = 0;
    uint32_t last_alive_tick = HAL_GetTick();

    while (1) {
        uint32_t rx_count = g_rx_input_stats.edge_count;

        if (rx_count - last_rx_count >= 50) {
            last_rx_count = rx_count;
            heartbeat_blink(PIN_LED_B_PORT, PIN_LED_B_PIN);
        }

        if (HAL_GetTick() - last_alive_tick >= 1000) {
            last_alive_tick = HAL_GetTick();
            HAL_GPIO_WritePin(PIN_LED_B_PORT, PIN_LED_B_PIN, GPIO_PIN_SET);
            HAL_GPIO_WritePin(PIN_LED_R_PORT, PIN_LED_R_PIN, GPIO_PIN_SET);
            HAL_Delay(40);
            HAL_GPIO_WritePin(PIN_LED_B_PORT, PIN_LED_B_PIN, GPIO_PIN_RESET);
            HAL_GPIO_WritePin(PIN_LED_R_PORT, PIN_LED_R_PIN, GPIO_PIN_RESET);
        }

        HAL_Delay(5);
    }
}

void SysTick_Handler(void)
{
    HAL_IncTick();
}

void Error_Handler(void)
{
    __disable_irq();
    while (1) {
    }
}
