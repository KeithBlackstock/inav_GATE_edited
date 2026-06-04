# STM32 F405 Hardware Detection Scripts

This directory contains MicroPython scripts for detecting and enumerating hardware capabilities on STM32 F405 flight controllers.

## Purpose

These scripts provide a standalone hardware detection utility that can:
- Enumerate available GPIO pins and their current states
- Detect I2C and SPI buses
- List UART ports and their configurations
- Identify available timers and PWM channels
- Scan for connected sensors (IMU, magnetometer, barometer, etc.)
- Report ADC channels and voltage references
- Display memory and flash information

## Requirements

- STM32 F405 flight controller
- MicroPython firmware installed on the board
- USB connection for serial communication

## Usage

1. Connect your F405 board via USB
2. Access the MicroPython REPL
3. Run the main detection script:
   ```python
   import hardware_detect
   hardware_detect.scan_all()
   ```

## Scripts

- `hardware_detect.py` - Main detection orchestrator
- `gpio_detect.py` - GPIO pin enumeration
- `bus_detect.py` - I2C/SPI bus detection
- `uart_detect.py` - UART port detection
- `sensor_detect.py` - Sensor scanning (IMU, mag, baro, etc.)
- `timer_detect.py` - Timer and PWM channel detection
- `adc_detect.py` - ADC channel detection
- `system_info.py` - System memory and flash information

## Output Format

Detection results are printed to the console in a structured format showing:
- Hardware component type
- Available instances
- Current configuration/state
- Detected devices (for buses and sensors)