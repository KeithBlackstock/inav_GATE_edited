"""
STM32 F405 Hardware Detection - Main Orchestrator
Coordinates all hardware detection modules and provides unified output
"""

import sys
import gc

# Import detection modules
try:
    import gpio_detect
    import bus_detect
    import uart_detect
    import sensor_detect
    import timer_detect
    import adc_detect
    import system_info
except ImportError as e:
    print(f"Error importing detection modules: {e}")
    print("Ensure all detection scripts are in the same directory")
    sys.exit(1)


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_separator():
    """Print a section separator"""
    print("-" * 60)


def scan_all(verbose=True):
    """
    Run all hardware detection scans
    
    Args:
        verbose: If True, print detailed information
    """
    print("\n" + "=" * 60)
    print("  STM32 F405 HARDWARE DETECTION")
    print("=" * 60)
    
    # System Information
    print_header("SYSTEM INFORMATION")
    try:
        system_info.display_system_info()
    except Exception as e:
        print(f"Error detecting system info: {e}")
    
    # GPIO Detection
    print_header("GPIO PINS")
    try:
        gpio_detect.scan_gpio(verbose)
    except Exception as e:
        print(f"Error detecting GPIO: {e}")
    
    # Bus Detection (I2C/SPI)
    print_header("COMMUNICATION BUSES")
    try:
        bus_detect.scan_buses(verbose)
    except Exception as e:
        print(f"Error detecting buses: {e}")
    
    # UART Detection
    print_header("UART PORTS")
    try:
        uart_detect.scan_uarts(verbose)
    except Exception as e:
        print(f"Error detecting UARTs: {e}")
    
    # Timer Detection
    print_header("TIMERS & PWM")
    try:
        timer_detect.scan_timers(verbose)
    except Exception as e:
        print(f"Error detecting timers: {e}")
    
    # ADC Detection
    print_header("ADC CHANNELS")
    try:
        adc_detect.scan_adc(verbose)
    except Exception as e:
        print(f"Error detecting ADC: {e}")
    
    # Sensor Detection
    print_header("SENSORS")
    try:
        sensor_detect.scan_sensors(verbose)
    except Exception as e:
        print(f"Error detecting sensors: {e}")
    
    # Summary
    print_header("DETECTION COMPLETE")
    gc.collect()
    print(f"Free memory: {gc.mem_free()} bytes")
    print("=" * 60 + "\n")


def scan_quick():
    """Run a quick scan showing only available hardware"""
    print("\n" + "=" * 60)
    print("  STM32 F405 QUICK HARDWARE SCAN")
    print("=" * 60)
    
    results = {
        'system': system_info.get_system_summary(),
        'gpio': gpio_detect.get_gpio_summary(),
        'buses': bus_detect.get_bus_summary(),
        'uarts': uart_detect.get_uart_summary(),
        'timers': timer_detect.get_timer_summary(),
        'adc': adc_detect.get_adc_summary(),
        'sensors': sensor_detect.get_sensor_summary()
    }
    
    for category, data in results.items():
        print(f"\n{category.upper()}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")
    
    print("\n" + "=" * 60 + "\n")
    return results


def export_json():
    """Export detection results as JSON string"""
    try:
        import json
        results = {
            'system': system_info.get_system_summary(),
            'gpio': gpio_detect.get_gpio_summary(),
            'buses': bus_detect.get_bus_summary(),
            'uarts': uart_detect.get_uart_summary(),
            'timers': timer_detect.get_timer_summary(),
            'adc': adc_detect.get_adc_summary(),
            'sensors': sensor_detect.get_sensor_summary()
        }
        return json.dumps(results, indent=2)
    except ImportError:
        print("JSON module not available")
        return None


if __name__ == "__main__":
    # Run full scan when executed directly
    scan_all(verbose=True)

# Made with Bob
