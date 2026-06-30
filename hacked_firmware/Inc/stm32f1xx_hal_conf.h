#ifndef STM32F1xx_HAL_CONF_H
#define STM32F1xx_HAL_CONF_H

#define HAL_MODULE_ENABLED
#define HAL_GPIO_MODULE_ENABLED
#define HAL_RCC_MODULE_ENABLED
#define HAL_CORTEX_MODULE_ENABLED
#define HAL_FLASH_MODULE_ENABLED
#define HAL_PWR_MODULE_ENABLED
#define HAL_EXTI_MODULE_ENABLED

#if !defined(HSE_VALUE)
#define HSE_VALUE    8000000U  /* HobbyEagle A3 crystal -- unverified, default F103 bring-up value */
#endif

#if !defined(HSI_VALUE)
#define HSI_VALUE    8000000U
#endif

#if !defined(LSE_VALUE)
#define LSE_VALUE    32768U
#endif

#if !defined(LSI_VALUE)
#define LSI_VALUE    40000U
#endif

#define VDD_VALUE                    3300U
#define TICK_INT_PRIORITY            0x0FU
#define USE_RTOS                     0U
#define PREFETCH_ENABLE              1U
#define HSE_STARTUP_TIMEOUT          100U
#define LSE_STARTUP_TIMEOUT          5000U

#define USE_HAL_GPIO_REGISTER_CALLBACKS 0U

#define assert_param(expr) ((void)0U)

#include "stm32f1xx_hal_rcc.h"
#include "stm32f1xx_hal_gpio.h"
#include "stm32f1xx_hal_cortex.h"
#include "stm32f1xx_hal_flash.h"
#include "stm32f1xx_hal_pwr.h"
#include "stm32f1xx_hal_exti.h"

#endif /* STM32F1xx_HAL_CONF_H */
