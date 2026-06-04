"""
STM32 F405 ADC Detection
Scans for available ADC channels and voltage references
"""

try:
    from machine import ADC, Pin
except ImportError:
    ADC = None
    Pin = None


# STM32F405 ADC channel definitions
# ADC1, ADC2, and ADC3 are available
# Each ADC has multiple channels mapped to specific pins
ADC_CHANNELS = [
    {'adc': 1, 'channel': 0, 'pin': 'A0'},
    {'adc': 1, 'channel': 1, 'pin': 'A1'},
    {'adc': 1, 'channel': 2, 'pin': 'A2'},
    {'adc': 1, 'channel': 3, 'pin': 'A3'},
    {'adc': 1, 'channel': 4, 'pin': 'A4'},
    {'adc': 1, 'channel': 5, 'pin': 'A5'},
    {'adc': 1, 'channel': 6, 'pin': 'A6'},
    {'adc': 1, 'channel': 7, 'pin': 'A7'},
    {'adc': 1, 'channel': 8, 'pin': 'B0'},
    {'adc': 1, 'channel': 9, 'pin': 'B1'},
    {'adc': 1, 'channel': 10, 'pin': 'C0'},
    {'adc': 1, 'channel': 11, 'pin': 'C1'},
    {'adc': 1, 'channel': 12, 'pin': 'C2'},
    {'adc': 1, 'channel': 13, 'pin': 'C3'},
    {'adc': 1, 'channel': 14, 'pin': 'C4'},
    {'adc': 1, 'channel': 15, 'pin': 'C5'},
]

# Common ADC uses on flight controllers
ADC_USES = {
    'VBAT': 'Battery voltage monitoring',
    'CURRENT': 'Current sensor',
    'RSSI': 'Receiver signal strength',
    'AIRSPEED': 'Pitot tube airspeed sensor',
}


def test_adc_channel(pin_name):
    """
    Test if an ADC channel is available
    
    Args:
        pin_name: Pin name (e.g., 'A0')
    
    Returns:
        True if ADC is available, False otherwise
    """
    if ADC is None or Pin is None:
        return False
    
    try:
        adc = ADC(Pin(pin_name))
        # Try to read a value
        value = adc.read_u16()
        return True
    except Exception as e:
        return False


def read_adc_voltage(pin_name, vref=3.3):
    """
    Read voltage from an ADC channel
    
    Args:
        pin_name: Pin name
        vref: Reference voltage (default 3.3V)
    
    Returns:
        Voltage reading or None on error
    """
    if ADC is None or Pin is None:
        return None
    
    try:
        adc = ADC(Pin(pin_name))
        raw = adc.read_u16()
        voltage = (raw / 65535) * vref
        return voltage
    except Exception as e:
        return None


def scan_adc(verbose=True):
    """Scan all ADC channels"""
    if ADC is None:
        print("Error: machine.ADC not available")
        return
    
    print("\nADC Channels:")
    available_channels = []
    
    for channel_info in ADC_CHANNELS:
        adc_num = channel_info['adc']
        channel = channel_info['channel']
        pin = channel_info['pin']
        
        is_available = test_adc_channel(pin)
        
        if is_available:
            available_channels.append({
                'adc': adc_num,
                'channel': channel,
                'pin': f'P{pin}'
            })
            
            if verbose:
                voltage = read_adc_voltage(pin)
                if voltage is not None:
                    print(f"  ADC{adc_num}_CH{channel} (P{pin}): Available - {voltage:.3f}V")
                else:
                    print(f"  ADC{adc_num}_CH{channel} (P{pin}): Available")
        else:
            if verbose:
                print(f"  ADC{adc_num}_CH{channel} (P{pin}): Not available")
    
    return available_channels


def monitor_adc_channel(pin_name, duration=5, interval=0.5):
    """
    Monitor an ADC channel over time
    
    Args:
        pin_name: Pin to monitor
        duration: Duration in seconds
        interval: Sampling interval in seconds
    """
    if ADC is None or Pin is None:
        print("Error: ADC not available")
        return
    
    print(f"\nMonitoring P{pin_name} for {duration} seconds:")
    
    try:
        import time
        adc = ADC(Pin(pin_name))
        
        start_time = time.time()
        samples = []
        
        while time.time() - start_time < duration:
            raw = adc.read_u16()
            voltage = (raw / 65535) * 3.3
            samples.append(voltage)
            print(f"  {time.time() - start_time:.1f}s: {voltage:.3f}V (raw: {raw})")
            time.sleep(interval)
        
        # Statistics
        if samples:
            avg = sum(samples) / len(samples)
            min_v = min(samples)
            max_v = max(samples)
            print(f"\nStatistics:")
            print(f"  Average: {avg:.3f}V")
            print(f"  Min: {min_v:.3f}V")
            print(f"  Max: {max_v:.3f}V")
            print(f"  Range: {max_v - min_v:.3f}V")
    
    except Exception as e:
        print(f"Error: {e}")


def get_adc_summary():
    """Get summary of ADC availability"""
    if ADC is None:
        return {'error': 'ADC module not available'}
    
    available_count = 0
    
    for channel_info in ADC_CHANNELS:
        if test_adc_channel(channel_info['pin']):
            available_count += 1
    
    return {
        'total_channels': len(ADC_CHANNELS),
        'available_channels': available_count
    }


def calibrate_adc_channel(pin_name, known_voltage):
    """
    Calibrate an ADC channel against a known voltage
    
    Args:
        pin_name: Pin to calibrate
        known_voltage: Known reference voltage
    
    Returns:
        Calibration factor
    """
    if ADC is None or Pin is None:
        print("Error: ADC not available")
        return None
    
    try:
        adc = ADC(Pin(pin_name))
        raw = adc.read_u16()
        measured_voltage = (raw / 65535) * 3.3
        
        calibration_factor = known_voltage / measured_voltage
        
        print(f"\nADC Calibration for P{pin_name}:")
        print(f"  Raw value: {raw}")
        print(f"  Measured voltage: {measured_voltage:.3f}V")
        print(f"  Known voltage: {known_voltage:.3f}V")
        print(f"  Calibration factor: {calibration_factor:.4f}")
        
        return calibration_factor
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def scan_adc_common_uses(verbose=True):
    """Display common ADC uses on flight controllers"""
    if verbose:
        print("\nCommon ADC Uses on Flight Controllers:")
        for use, description in ADC_USES.items():
            print(f"  {use}: {description}")
        
        print("\nTypical pin assignments (board-specific):")
        print("  VBAT: Often on PA0 or PA1 with voltage divider")
        print("  CURRENT: Often on PA2 or PA3")
        print("  RSSI: Often on PA4 or PA5")


if __name__ == "__main__":
    scan_adc(verbose=True)
    scan_adc_common_uses(verbose=True)

# Made with Bob
