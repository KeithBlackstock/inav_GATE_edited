"""
STM32 F405 Sensor Detection
Scans for common flight controller sensors (IMU, magnetometer, barometer, etc.)
"""

try:
    from machine import I2C, SPI, Pin
except ImportError:
    I2C = None
    SPI = None
    Pin = None


# Common sensor I2C addresses and their WHO_AM_I registers
I2C_SENSORS = {
    'MPU6000': {'addr': 0x68, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x68, 'type': 'IMU'},
    'MPU6050': {'addr': 0x68, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x68, 'type': 'IMU'},
    'MPU6000_ALT': {'addr': 0x69, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x68, 'type': 'IMU'},
    'MPU9250': {'addr': 0x68, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x71, 'type': 'IMU'},
    'ICM20602': {'addr': 0x68, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x12, 'type': 'IMU'},
    'ICM20689': {'addr': 0x68, 'who_am_i_reg': 0x75, 'who_am_i_val': 0x98, 'type': 'IMU'},
    'BMI160': {'addr': 0x68, 'who_am_i_reg': 0x00, 'who_am_i_val': 0xD1, 'type': 'IMU'},
    'HMC5883L': {'addr': 0x1E, 'who_am_i_reg': 0x0A, 'who_am_i_val': 0x48, 'type': 'Magnetometer'},
    'QMC5883L': {'addr': 0x0D, 'who_am_i_reg': 0x0D, 'who_am_i_val': 0xFF, 'type': 'Magnetometer'},
    'BMP280': {'addr': 0x76, 'who_am_i_reg': 0xD0, 'who_am_i_val': 0x58, 'type': 'Barometer'},
    'BMP280_ALT': {'addr': 0x77, 'who_am_i_reg': 0xD0, 'who_am_i_val': 0x58, 'type': 'Barometer'},
    'BME280': {'addr': 0x76, 'who_am_i_reg': 0xD0, 'who_am_i_val': 0x60, 'type': 'Barometer'},
    'MS5611': {'addr': 0x77, 'who_am_i_reg': None, 'who_am_i_val': None, 'type': 'Barometer'},
    'VL53L0X': {'addr': 0x29, 'who_am_i_reg': 0xC0, 'who_am_i_val': 0xEE, 'type': 'ToF'},
}

# I2C bus configurations
I2C_BUSES = [
    {'id': 1, 'scl': 'B6', 'sda': 'B7'},
    {'id': 2, 'scl': 'B10', 'sda': 'B11'},
]


def read_sensor_register(i2c, addr, reg):
    """
    Read a register from an I2C sensor
    
    Args:
        i2c: I2C bus object
        addr: Sensor I2C address
        reg: Register address
    
    Returns:
        Register value or None on error
    """
    try:
        data = i2c.readfrom_mem(addr, reg, 1)
        return data[0]
    except:
        return None


def detect_i2c_sensor(i2c, sensor_name, sensor_info):
    """
    Detect a specific I2C sensor
    
    Args:
        i2c: I2C bus object
        sensor_name: Name of the sensor
        sensor_info: Dictionary with sensor details
    
    Returns:
        True if sensor detected, False otherwise
    """
    addr = sensor_info['addr']
    who_am_i_reg = sensor_info['who_am_i_reg']
    who_am_i_val = sensor_info['who_am_i_val']
    
    # Check if device responds at this address
    try:
        i2c.writeto(addr, b'')
    except:
        return False
    
    # If no WHO_AM_I register, assume it's the sensor
    if who_am_i_reg is None:
        return True
    
    # Read WHO_AM_I register
    value = read_sensor_register(i2c, addr, who_am_i_reg)
    
    if value == who_am_i_val:
        return True
    
    return False


def scan_i2c_sensors(verbose=True):
    """Scan for I2C sensors on all buses"""
    if I2C is None:
        print("Error: machine.I2C not available")
        return {}
    
    detected_sensors = {}
    
    for bus_config in I2C_BUSES:
        bus_id = bus_config['id']
        
        try:
            i2c = I2C(bus_id, 
                     scl=Pin(bus_config['scl']), 
                     sda=Pin(bus_config['sda']), 
                     freq=400000)
            
            if verbose:
                print(f"\nScanning I2C{bus_id}:")
            
            for sensor_name, sensor_info in I2C_SENSORS.items():
                if detect_i2c_sensor(i2c, sensor_name, sensor_info):
                    sensor_type = sensor_info['type']
                    addr = sensor_info['addr']
                    
                    if sensor_type not in detected_sensors:
                        detected_sensors[sensor_type] = []
                    
                    detected_sensors[sensor_type].append({
                        'name': sensor_name,
                        'bus': f'I2C{bus_id}',
                        'address': f'0x{addr:02X}'
                    })
                    
                    if verbose:
                        print(f"  Found {sensor_name} ({sensor_type}) at 0x{addr:02X}")
        
        except Exception as e:
            if verbose:
                print(f"  Error scanning I2C{bus_id}: {e}")
    
    return detected_sensors


def scan_spi_sensors(verbose=True):
    """
    Scan for SPI sensors
    Note: SPI sensors require CS pin selection, so this is more limited
    """
    if SPI is None:
        print("Error: machine.SPI not available")
        return {}
    
    if verbose:
        print("\nSPI Sensors:")
        print("  Note: SPI sensor detection requires CS pin configuration")
        print("  Common SPI sensors: MPU6000, ICM20689, BMI270, BMP280")
    
    # SPI detection would require knowing CS pins for each sensor
    # This is board-specific and typically configured in firmware
    
    return {}


def scan_sensors(verbose=True):
    """Scan for all sensors"""
    i2c_sensors = scan_i2c_sensors(verbose)
    spi_sensors = scan_spi_sensors(verbose)
    
    if verbose:
        print("\n" + "-" * 60)
        print("Sensor Summary:")
        
        if i2c_sensors:
            for sensor_type, sensors in i2c_sensors.items():
                print(f"\n  {sensor_type}:")
                for sensor in sensors:
                    print(f"    {sensor['name']} on {sensor['bus']} at {sensor['address']}")
        else:
            print("  No I2C sensors detected")
    
    return {
        'i2c': i2c_sensors,
        'spi': spi_sensors
    }


def get_sensor_summary():
    """Get summary of detected sensors"""
    if I2C is None:
        return {'error': 'I2C module not available'}
    
    sensors = scan_i2c_sensors(verbose=False)
    
    summary = {
        'imu_count': len(sensors.get('IMU', [])),
        'mag_count': len(sensors.get('Magnetometer', [])),
        'baro_count': len(sensors.get('Barometer', [])),
        'tof_count': len(sensors.get('ToF', []))
    }
    
    return summary


def test_sensor_data(sensor_type='IMU'):
    """
    Attempt to read data from a detected sensor
    
    Args:
        sensor_type: Type of sensor to test ('IMU', 'Magnetometer', 'Barometer')
    """
    if I2C is None:
        print("Error: machine.I2C not available")
        return
    
    sensors = scan_i2c_sensors(verbose=False)
    
    if sensor_type not in sensors or not sensors[sensor_type]:
        print(f"No {sensor_type} sensors detected")
        return
    
    sensor = sensors[sensor_type][0]
    print(f"\nTesting {sensor['name']} on {sensor['bus']}:")
    
    # This would require sensor-specific register reading
    # Implementation depends on the specific sensor
    print("  (Sensor-specific data reading not implemented)")


if __name__ == "__main__":
    scan_sensors(verbose=True)

# Made with Bob
