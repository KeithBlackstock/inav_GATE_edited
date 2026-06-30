TARGET = hacked_firmware
BUILD_DIR = build

TOOLCHAIN = arm-none-eabi-
CC = $(TOOLCHAIN)gcc
AS = $(TOOLCHAIN)gcc
OBJCOPY = $(TOOLCHAIN)objcopy
SIZE = $(TOOLCHAIN)size

CPU = -mcpu=cortex-m3 -mthumb

DEVICE_DIR = Drivers/CMSIS/Device/ST/STM32F1xx
HAL_DIR    = Drivers/STM32F1xx_HAL_Driver

C_SOURCES = \
  Src/main.c \
  $(DEVICE_DIR)/Source/Templates/system_stm32f1xx.c \
  $(HAL_DIR)/Src/stm32f1xx_hal.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_rcc.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_rcc_ex.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_cortex.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_gpio.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_flash.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_flash_ex.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_pwr.c \
  $(HAL_DIR)/Src/stm32f1xx_hal_exti.c

ASM_SOURCES = $(DEVICE_DIR)/Source/Templates/gcc/startup_stm32f103xb.s

INCLUDES = \
  -IInc \
  -IDrivers/CMSIS/Include \
  -I$(DEVICE_DIR)/Include \
  -I$(HAL_DIR)/Inc

DEFS = -DSTM32F103xB -DUSE_HAL_DRIVER

CFLAGS  = $(CPU) $(DEFS) $(INCLUDES) -Os -ffunction-sections -fdata-sections -Wall -g -std=c11
ASFLAGS = $(CPU) -g
LDSCRIPT = STM32F103xB_FLASH.ld
LDFLAGS = $(CPU) -specs=nano.specs -T$(LDSCRIPT) -Wl,--gc-sections -Wl,-Map=$(BUILD_DIR)/$(TARGET).map

OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.s=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))
vpath %.s $(sort $(dir $(ASM_SOURCES)))

.PHONY: all clean

all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

$(BUILD_DIR)/%.o: %.c | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.o: %.s | $(BUILD_DIR)
	$(AS) -c $(ASFLAGS) $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SIZE) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf
	$(OBJCOPY) -O ihex $< $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf
	$(OBJCOPY) -O binary $< $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
