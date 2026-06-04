"""
STM32 F405 UART Detection
Scans for available UART ports and their configurations
"""

try:
    from machine import UART, Pin
except ImportError:
    UART = None
    Pin = None


# STM32F405 UART definitions
UART_PORTS = [
    {'id': 1, 'tx': 'A9', 'rx': 'A10', 'name': 'UART1'},
    {'id': 2, 'tx': 'A2', 'rx': 'A3', 'name': 'UART2'},
    {'id': 3, 'tx': 'B10', 'rx': 'B11', 'name': 'UART3'},
    {'id': 4, 'tx': 'A0', 'rx': 'A1', 'name': 'UART4'},
    {'id': 5, 'tx': 'C12', 'rx': 'D2', 'name': 'UART5'},
    {'id': 6, 'tx': 'C6', 'rx': 'C7', 'name': 'UART6'},
]

# Common baud rates for flight controllers
COMMON_BAUDS = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]


def test_uart_port(uart_id, tx_pin, rx_pin, baudrate=115200):
    """
    Test if a UART port is available
    
    Args:
        uart_id: UART port number
        tx_pin: TX pin name
        rx_pin: RX pin name
        baudrate: Baud rate to test
    
    Returns:
        True if port is available, False otherwise
    """
    if UART is None:
        return False
    
    try:
        uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        # Port initialized successfully
        uart.deinit()
        return True
    except Exception as e:
        return False


def scan_uarts(verbose=True):
    """Scan all UART ports"""
    if UART is None:
        print("Error: machine.UART not available")
        return
    
    print("\nUART Ports:")
    available_ports = []
    
    for port in UART_PORTS:
        uart_id = port['id']
        name = port['name']
        tx = port['tx']
        rx = port['rx']
        
        if verbose:
            print(f"\n  {name} (TX=P{tx}, RX=P{rx}):")
        
        is_available = test_uart_port(uart_id, tx, rx)
        
        if is_available:
            available_ports.append(name)
            if verbose:
                print(f"    Status: Available")
                print(f"    Common uses: GPS, Telemetry, MSP, SmartPort")
        else:
            if verbose:
                print(f"    Status: Not available or in use")
    
    return available_ports


def test_uart_bauds(uart_id, tx_pin, rx_pin):
    """
    Test which baud rates work for a UART port
    
    Args:
        uart_id: UART port number
        tx_pin: TX pin name
        rx_pin: RX pin name
    
    Returns:
        List of working baud rates
    """
    if UART is None:
        return []
    
    working_bauds = []
    
    for baud in COMMON_BAUDS:
        try:
            uart = UART(uart_id, baudrate=baud, tx=Pin(tx_pin), rx=Pin(rx_pin))
            working_bauds.append(baud)
            uart.deinit()
        except:
            pass
    
    return working_bauds


def scan_uart_details(uart_id):
    """
    Get detailed information about a specific UART port
    
    Args:
        uart_id: UART port number (1-6)
    """
    if UART is None:
        print("Error: machine.UART not available")
        return
    
    port = next((p for p in UART_PORTS if p['id'] == uart_id), None)
    if not port:
        print(f"Invalid UART ID: {uart_id}")
        return
    
    print(f"\n{port['name']} Details:")
    print(f"  TX Pin: P{port['tx']}")
    print(f"  RX Pin: P{port['rx']}")
    
    # Test availability
    is_available = test_uart_port(uart_id, port['tx'], port['rx'])
    print(f"  Available: {is_available}")
    
    if is_available:
        # Test baud rates
        print(f"\n  Supported Baud Rates:")
        bauds = test_uart_bauds(uart_id, port['tx'], port['rx'])
        for baud in bauds:
            print(f"    {baud}")


def get_uart_summary():
    """Get summary of UART availability"""
    if UART is None:
        return {'error': 'UART module not available'}
    
    available_count = 0
    
    for port in UART_PORTS:
        if test_uart_port(port['id'], port['tx'], port['rx']):
            available_count += 1
    
    return {
        'total_ports': len(UART_PORTS),
        'available_ports': available_count
    }


def uart_loopback_test(uart_id, tx_pin, rx_pin):
    """
    Perform a loopback test on a UART port
    Note: Requires TX and RX pins to be physically connected
    
    Args:
        uart_id: UART port number
        tx_pin: TX pin name
        rx_pin: RX pin name
    
    Returns:
        True if loopback test passes, False otherwise
    """
    if UART is None:
        return False
    
    try:
        uart = UART(uart_id, baudrate=115200, tx=Pin(tx_pin), rx=Pin(rx_pin))
        
        # Send test data
        test_data = b'LOOPBACK_TEST'
        uart.write(test_data)
        
        # Try to read it back
        import time
        time.sleep(0.1)  # Wait for data
        
        if uart.any():
            received = uart.read()
            uart.deinit()
            return received == test_data
        
        uart.deinit()
        return False
        
    except Exception as e:
        print(f"Loopback test error: {e}")
        return False


if __name__ == "__main__":
    scan_uarts(verbose=True)

# Made with Bob
