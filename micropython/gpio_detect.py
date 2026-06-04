"""
STM32 F405 GPIO Detection
Enumerates available GPIO pins and their current states
"""

try:
    from machine import Pin
except ImportError:
    Pin = None


# STM32F405 GPIO port definitions
# Each port has 16 pins (0-15)
GPIO_PORTS = ['A', 'B', 'C', 'D', 'E']

# Common flight controller pin assignments (typical F405 boards)
COMMON_PINS = {
    'LED': ['B4', 'B5'],  # Status LEDs
    'BEEPER': ['C15'],
    'USB': ['A11', 'A12'],  # USB D-/D+
    'SWD': ['A13', 'A14'],  # Debug interface
    'MOTOR': ['A0', 'A1', 'A2', 'A3', 'B0', 'B1'],  # PWM outputs
    'UART1': ['A9', 'A10'],  # TX/RX
    'UART2': ['A2', 'A3'],
    'UART3': ['B10', 'B11'],
    'UART4': ['A0', 'A1'],
    'UART5': ['C12', 'D2'],
    'UART6': ['C6', 'C7'],
    'I2C1': ['B6', 'B7'],  # SCL/SDA
    'I2C2': ['B10', 'B11'],
    'SPI1': ['A5', 'A6', 'A7'],  # SCK/MISO/MOSI
    'SPI2': ['B13', 'B14', 'B15'],
    'SPI3': ['C10', 'C11', 'C12'],
}


def get_pin_name(port, num):
    """Convert port and pin number to pin name (e.g., 'A', 5 -> 'PA5')"""
    return f"P{port}{num}"


def scan_gpio(verbose=True):
    """
    Scan all GPIO pins and report their availability
    
    Args:
        verbose: If True, print detailed information for each pin
    """
    if Pin is None:
        print("Error: machine.Pin not available")
        return
    
    available_pins = []
    
    for port in GPIO_PORTS:
        if verbose:
            print(f"\nPort {port}:")
        
        port_pins = []
        for pin_num in range(16):
            pin_name = get_pin_name(port, pin_num)
            
            try:
                # Try to create a Pin object
                pin = Pin(pin_name, Pin.IN)
                available_pins.append(pin_name)
                port_pins.append(pin_name)
                
                if verbose:
                    # Try to read the pin value
                    try:
                        value = pin.value()
                        print(f"  {pin_name}: Available (value={value})")
                    except:
                        print(f"  {pin_name}: Available (cannot read)")
                
            except (ValueError, OSError) as e:
                if verbose:
                    print(f"  {pin_name}: Not available ({e})")
    
    if not verbose:
        print(f"\nTotal available GPIO pins: {len(available_pins)}")
        print(f"Ports: {', '.join(GPIO_PORTS)}")
    
    return available_pins


def scan_common_pins():
    """Scan commonly used pins on flight controllers"""
    if Pin is None:
        print("Error: machine.Pin not available")
        return
    
    print("\nCommon Flight Controller Pins:")
    
    for function, pins in COMMON_PINS.items():
        print(f"\n{function}:")
        for pin_name in pins:
            try:
                pin = Pin(pin_name, Pin.IN)
                value = pin.value()
                print(f"  {pin_name}: Available (value={value})")
            except Exception as e:
                print(f"  {pin_name}: Not available")


def get_gpio_summary():
    """Get summary of GPIO availability"""
    if Pin is None:
        return {'error': 'Pin module not available'}
    
    available_count = 0
    port_counts = {}
    
    for port in GPIO_PORTS:
        count = 0
        for pin_num in range(16):
            pin_name = get_pin_name(port, pin_num)
            try:
                pin = Pin(pin_name, Pin.IN)
                count += 1
                available_count += 1
            except:
                pass
        port_counts[f"Port_{port}"] = count
    
    summary = {
        'total_available': available_count,
        'ports': len(GPIO_PORTS),
        **port_counts
    }
    
    return summary


def test_pin_modes(pin_name):
    """Test different modes for a specific pin"""
    if Pin is None:
        print("Error: machine.Pin not available")
        return
    
    print(f"\nTesting pin {pin_name}:")
    
    modes = [
        ('IN', Pin.IN),
        ('OUT', Pin.OUT),
        ('OPEN_DRAIN', Pin.OPEN_DRAIN),
    ]
    
    pulls = [
        ('PULL_UP', Pin.PULL_UP),
        ('PULL_DOWN', Pin.PULL_DOWN),
    ]
    
    for mode_name, mode in modes:
        try:
            pin = Pin(pin_name, mode)
            print(f"  {mode_name}: Supported")
            
            # Test pulls for input mode
            if mode == Pin.IN:
                for pull_name, pull in pulls:
                    try:
                        pin = Pin(pin_name, mode, pull)
                        print(f"    {pull_name}: Supported")
                    except:
                        print(f"    {pull_name}: Not supported")
        except Exception as e:
            print(f"  {mode_name}: Not supported ({e})")


if __name__ == "__main__":
    scan_gpio(verbose=True)
    scan_common_pins()

# Made with Bob
