"""
STM32 F405 Bus Detection (I2C and SPI)
Scans for available I2C and SPI buses and connected devices
"""

try:
    from machine import I2C, SPI, Pin
except ImportError:
    I2C = None
    SPI = None
    Pin = None


# STM32F405 I2C bus definitions
I2C_BUSES = [
    {'id': 1, 'scl': 'B6', 'sda': 'B7'},
    {'id': 2, 'scl': 'B10', 'sda': 'B11'},
]

# STM32F405 SPI bus definitions
SPI_BUSES = [
    {'id': 1, 'sck': 'A5', 'miso': 'A6', 'mosi': 'A7'},
    {'id': 2, 'sck': 'B13', 'miso': 'B14', 'mosi': 'B15'},
    {'id': 3, 'sck': 'C10', 'miso': 'C11', 'mosi': 'C12'},
]

# Common I2C device addresses
COMMON_I2C_ADDRESSES = {
    0x68: 'MPU6000/MPU6050 (IMU)',
    0x69: 'MPU6000/MPU6050 (IMU alt)',
    0x1E: 'HMC5883L (Magnetometer)',
    0x0D: 'QMC5883L (Magnetometer)',
    0x77: 'BMP280/BME280 (Barometer)',
    0x76: 'BMP280/BME280 (Barometer alt)',
    0x29: 'VL53L0X (ToF sensor)',
    0x50: 'EEPROM (24C02)',
    0x3C: 'OLED Display (SSD1306)',
}


def scan_i2c_bus(bus_id, scl_pin, sda_pin):
    """
    Scan a specific I2C bus for devices
    
    Args:
        bus_id: I2C bus number
        scl_pin: SCL pin name
        sda_pin: SDA pin name
    
    Returns:
        List of detected device addresses
    """
    if I2C is None:
        return []
    
    try:
        i2c = I2C(bus_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        devices = i2c.scan()
        return devices
    except Exception as e:
        print(f"  Error scanning I2C{bus_id}: {e}")
        return []


def scan_i2c(verbose=True):
    """Scan all I2C buses"""
    if I2C is None:
        print("Error: machine.I2C not available")
        return
    
    print("\nI2C Buses:")
    all_devices = {}
    
    for bus in I2C_BUSES:
        bus_id = bus['id']
        scl = bus['scl']
        sda = bus['sda']
        
        if verbose:
            print(f"\n  I2C{bus_id} (SCL=P{scl}, SDA=P{sda}):")
        
        devices = scan_i2c_bus(bus_id, scl, sda)
        
        if devices:
            all_devices[f"I2C{bus_id}"] = devices
            for addr in devices:
                device_name = COMMON_I2C_ADDRESSES.get(addr, 'Unknown device')
                if verbose:
                    print(f"    0x{addr:02X}: {device_name}")
        else:
            if verbose:
                print(f"    No devices found")
    
    return all_devices


def scan_spi_bus(bus_id, sck_pin, miso_pin, mosi_pin):
    """
    Check if a specific SPI bus is available
    
    Args:
        bus_id: SPI bus number
        sck_pin: SCK pin name
        miso_pin: MISO pin name
        mosi_pin: MOSI pin name
    
    Returns:
        True if bus is available, False otherwise
    """
    if SPI is None:
        return False
    
    try:
        spi = SPI(bus_id, 
                  baudrate=1000000,
                  polarity=0, 
                  phase=0,
                  sck=Pin(sck_pin),
                  miso=Pin(miso_pin),
                  mosi=Pin(mosi_pin))
        # Try to read/write to test the bus
        spi.write(b'\x00')
        return True
    except Exception as e:
        return False


def scan_spi(verbose=True):
    """Scan all SPI buses"""
    if SPI is None:
        print("Error: machine.SPI not available")
        return
    
    print("\nSPI Buses:")
    available_buses = []
    
    for bus in SPI_BUSES:
        bus_id = bus['id']
        sck = bus['sck']
        miso = bus['miso']
        mosi = bus['mosi']
        
        if verbose:
            print(f"\n  SPI{bus_id} (SCK=P{sck}, MISO=P{miso}, MOSI=P{mosi}):")
        
        is_available = scan_spi_bus(bus_id, sck, miso, mosi)
        
        if is_available:
            available_buses.append(f"SPI{bus_id}")
            if verbose:
                print(f"    Status: Available")
                print(f"    Note: SPI devices require CS pin selection for detection")
        else:
            if verbose:
                print(f"    Status: Not available or error")
    
    return available_buses


def scan_buses(verbose=True):
    """Scan all communication buses"""
    i2c_devices = scan_i2c(verbose)
    spi_buses = scan_spi(verbose)
    
    return {
        'i2c': i2c_devices,
        'spi': spi_buses
    }


def get_bus_summary():
    """Get summary of available buses"""
    summary = {
        'i2c_buses': 0,
        'i2c_devices': 0,
        'spi_buses': 0
    }
    
    if I2C is None or SPI is None:
        summary['error'] = 'Bus modules not available'
        return summary
    
    # Count I2C buses and devices
    for bus in I2C_BUSES:
        try:
            devices = scan_i2c_bus(bus['id'], bus['scl'], bus['sda'])
            if devices:
                summary['i2c_buses'] += 1
                summary['i2c_devices'] += len(devices)
        except:
            pass
    
    # Count SPI buses
    for bus in SPI_BUSES:
        try:
            if scan_spi_bus(bus['id'], bus['sck'], bus['miso'], bus['mosi']):
                summary['spi_buses'] += 1
        except:
            pass
    
    return summary


def read_i2c_register(bus_id, addr, reg):
    """
    Read a register from an I2C device
    
    Args:
        bus_id: I2C bus number
        addr: Device address
        reg: Register address
    
    Returns:
        Register value or None on error
    """
    if I2C is None:
        return None
    
    bus_config = next((b for b in I2C_BUSES if b['id'] == bus_id), None)
    if not bus_config:
        return None
    
    try:
        i2c = I2C(bus_id, 
                  scl=Pin(bus_config['scl']), 
                  sda=Pin(bus_config['sda']), 
                  freq=400000)
        data = i2c.readfrom_mem(addr, reg, 1)
        return data[0]
    except Exception as e:
        print(f"Error reading I2C register: {e}")
        return None


if __name__ == "__main__":
    scan_buses(verbose=True)

# Made with Bob
