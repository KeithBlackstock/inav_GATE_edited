#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

TOOLCHAIN_BIN="/c/Program Files (x86)/GNU Arm Embedded Toolchain/10 2021.10/bin"
CC="$TOOLCHAIN_BIN/arm-none-eabi-gcc"
OBJCOPY="$TOOLCHAIN_BIN/arm-none-eabi-objcopy"
SIZE="$TOOLCHAIN_BIN/arm-none-eabi-size"

BUILD_DIR=build
TARGET=hacked_firmware
DEVICE_DIR=Drivers/CMSIS/Device/ST/STM32F1xx
HAL_DIR=Drivers/STM32F1xx_HAL_Driver

CPU="-mcpu=cortex-m3 -mthumb"
DEFS="-DSTM32F103xB -DUSE_HAL_DRIVER"
INCLUDES="-IInc -IDrivers/CMSIS/Include -I$DEVICE_DIR/Include -I$HAL_DIR/Inc"
CFLAGS="$CPU $DEFS $INCLUDES -Os -ffunction-sections -fdata-sections -Wall -g -std=c11"
LDFLAGS="$CPU -specs=nano.specs -TSTM32F103xB_FLASH.ld -Wl,--gc-sections -Wl,-Map=$BUILD_DIR/$TARGET.map"

C_SOURCES=(
  Src/main.c
  "$DEVICE_DIR/Source/Templates/system_stm32f1xx.c"
  "$HAL_DIR/Src/stm32f1xx_hal.c"
  "$HAL_DIR/Src/stm32f1xx_hal_rcc.c"
  "$HAL_DIR/Src/stm32f1xx_hal_rcc_ex.c"
  "$HAL_DIR/Src/stm32f1xx_hal_cortex.c"
  "$HAL_DIR/Src/stm32f1xx_hal_gpio.c"
  "$HAL_DIR/Src/stm32f1xx_hal_flash.c"
  "$HAL_DIR/Src/stm32f1xx_hal_flash_ex.c"
  "$HAL_DIR/Src/stm32f1xx_hal_pwr.c"
  "$HAL_DIR/Src/stm32f1xx_hal_exti.c"
)
ASM_SOURCES=("$DEVICE_DIR/Source/Templates/gcc/startup_stm32f103xb.s")

mkdir -p "$BUILD_DIR"

OBJECTS=()
for src in "${C_SOURCES[@]}"; do
  obj="$BUILD_DIR/$(basename "${src%.c}").o"
  "$CC" -c $CFLAGS "$src" -o "$obj"
  OBJECTS+=("$obj")
done
for src in "${ASM_SOURCES[@]}"; do
  obj="$BUILD_DIR/$(basename "${src%.s}").o"
  "$CC" -c $CPU -g "$src" -o "$obj"
  OBJECTS+=("$obj")
done

"$CC" "${OBJECTS[@]}" $LDFLAGS -o "$BUILD_DIR/$TARGET.elf"
"$OBJCOPY" -O ihex "$BUILD_DIR/$TARGET.elf" "$BUILD_DIR/$TARGET.hex"
"$OBJCOPY" -O binary "$BUILD_DIR/$TARGET.elf" "$BUILD_DIR/$TARGET.bin"
"$SIZE" "$BUILD_DIR/$TARGET.elf"
