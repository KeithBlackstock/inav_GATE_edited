"""
STM32 F405 Timer and PWM Detection
Scans for available timers and PWM-capable pins
"""

try:
    from machine import Pin, PWM, Timer
except ImportError:
    Pin = None
    PWM = None
    Timer = None


# STM32F405 Timer definitions
# Timers 1-14 are available, but not all are accessible on all pins
TIMERS = list(range(1, 15))

# Common PWM output pins on F405 flight controllers
# Format: (pin_name, timer, channel)
PWM_PINS = [
    ('A0', 2, 1),   # TIM2_CH1
    ('A1', 2, 2),   # TIM2_CH2
    ('A2', 2, 3),   # TIM2_CH3
    ('A3', 2, 4),   # TIM2_CH4
    ('A6', 3, 1),   # TIM3_CH1
    ('A7', 3, 2),   # TIM3_CH2
    ('B0', 3, 3),   # TIM3_CH3
    ('B1', 3, 4),   # TIM3_CH4
    ('B4', 3, 1),   # TIM3_CH1 (alt)
    ('B5', 3, 2),   # TIM3_CH2 (alt)
    ('B6', 4, 1),   # TIM4_CH1
    ('B7', 4, 2),   # TIM4_CH2
    ('B8', 4, 3),   # TIM4_CH3
    ('B9', 4, 4),   # TIM4_CH4
    ('C6', 8, 1),   # TIM8_CH1
    ('C7', 8, 2),   # TIM8_CH2
    ('C8', 8, 3),   # TIM8_CH3
    ('C9', 8, 4),   # TIM8_CH4
]


def test_pwm_pin(pin_name, freq=1000):
    """
    Test if a pin supports PWM
    
    Args:
        pin_name: Pin name (e.g., 'A0')
        freq: PWM frequency to test
    
    Returns:
        True if PWM is supported, False otherwise
    """
    if PWM is None or Pin is None:
        return False
    
    try:
        pin = Pin(pin_name, Pin.OUT)
        pwm = PWM(pin, freq=freq)
        pwm.duty_u16(32768)  # 50% duty cycle
        pwm.deinit()
        return True
    except Exception as e:
        return False


def scan_timers(verbose=True):
    """Scan for available timers"""
    if Timer is None:
        print("Error: machine.Timer not available")
        return
    
    print("\nTimers:")
    available_timers = []
    
    for timer_id in TIMERS:
        try:
            timer = Timer(timer_id)
            available_timers.append(timer_id)
            if verbose:
                print(f"  Timer {timer_id}: Available")
            timer.deinit()
        except Exception as e:
            if verbose:
                print(f"  Timer {timer_id}: Not available")
    
    return available_timers


def scan_pwm_pins(verbose=True):
    """Scan for PWM-capable pins"""
    if PWM is None:
        print("Error: machine.PWM not available")
        return
    
    print("\nPWM Pins:")
    available_pwm = []
    
    for pin_name, timer, channel in PWM_PINS:
        is_available = test_pwm_pin(pin_name)
        
        if is_available:
            available_pwm.append({
                'pin': f'P{pin_name}',
                'timer': timer,
                'channel': channel
            })
            if verbose:
                print(f"  P{pin_name}: PWM available (TIM{timer}_CH{channel})")
        else:
            if verbose:
                print(f"  P{pin_name}: PWM not available")
    
    return available_pwm


def test_pwm_frequencies(pin_name):
    """
    Test different PWM frequencies on a pin
    
    Args:
        pin_name: Pin name to test
    """
    if PWM is None or Pin is None:
        print("Error: PWM not available")
        return
    
    print(f"\nTesting PWM frequencies on P{pin_name}:")
    
    # Common PWM frequencies for flight controllers
    frequencies = [50, 400, 1000, 2000, 8000, 16000, 32000]
    
    for freq in frequencies:
        try:
            pin = Pin(pin_name, Pin.OUT)
            pwm = PWM(pin, freq=freq)
            pwm.duty_u16(32768)  # 50% duty cycle
            print(f"  {freq} Hz: Supported")
            pwm.deinit()
        except Exception as e:
            print(f"  {freq} Hz: Not supported ({e})")


def get_timer_summary():
    """Get summary of timer availability"""
    if Timer is None or PWM is None:
        return {'error': 'Timer/PWM modules not available'}
    
    available_timers = 0
    available_pwm = 0
    
    for timer_id in TIMERS:
        try:
            timer = Timer(timer_id)
            available_timers += 1
            timer.deinit()
        except:
            pass
    
    for pin_name, _, _ in PWM_PINS:
        if test_pwm_pin(pin_name):
            available_pwm += 1
    
    return {
        'timers': available_timers,
        'pwm_pins': available_pwm
    }


def demonstrate_pwm(pin_name='A0', freq=1000):
    """
    Demonstrate PWM output on a pin
    
    Args:
        pin_name: Pin to use
        freq: PWM frequency
    """
    if PWM is None or Pin is None:
        print("Error: PWM not available")
        return
    
    print(f"\nDemonstrating PWM on P{pin_name} at {freq} Hz")
    print("Cycling duty cycle from 0% to 100%...")
    
    try:
        pin = Pin(pin_name, Pin.OUT)
        pwm = PWM(pin, freq=freq)
        
        import time
        
        # Sweep duty cycle
        for duty in range(0, 65536, 6553):  # 0% to 100% in 10 steps
            pwm.duty_u16(duty)
            duty_percent = (duty / 65535) * 100
            print(f"  Duty: {duty_percent:.1f}%")
            time.sleep(0.5)
        
        pwm.deinit()
        print("PWM demonstration complete")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    scan_timers(verbose=True)
    scan_pwm_pins(verbose=True)

# Made with Bob
