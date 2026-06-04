"""
STM32 F405 System Information Detection
Reports CPU, memory, flash, and firmware details
"""

import sys
import gc
import os


def get_cpu_info():
    """Get CPU identification and frequency"""
    info = {
        'platform': sys.platform,
        'implementation': sys.implementation.name,
        'version': '.'.join(map(str, sys.version_info[:3]))
    }
    
    try:
        import machine
        info['freq'] = machine.freq()
        info['unique_id'] = ''.join('{:02x}'.format(b) for b in machine.unique_id())
    except (ImportError, AttributeError):
        pass
    
    return info


def get_memory_info():
    """Get memory statistics"""
    gc.collect()
    
    info = {
        'free': gc.mem_free(),
        'allocated': gc.mem_alloc(),
        'total': gc.mem_free() + gc.mem_alloc()
    }
    
    return info


def get_flash_info():
    """Get flash storage information"""
    info = {}
    
    try:
        stat = os.statvfs('/')
        info['block_size'] = stat[0]
        info['total_blocks'] = stat[2]
        info['free_blocks'] = stat[3]
        info['total_bytes'] = stat[0] * stat[2]
        info['free_bytes'] = stat[0] * stat[3]
        info['used_bytes'] = info['total_bytes'] - info['free_bytes']
    except (OSError, AttributeError):
        pass
    
    return info


def get_system_summary():
    """Get summary of system information"""
    cpu = get_cpu_info()
    mem = get_memory_info()
    flash = get_flash_info()
    
    summary = {
        'platform': cpu.get('platform', 'unknown'),
        'cpu_freq_mhz': cpu.get('freq', 0) // 1_000_000,
        'ram_total_kb': mem.get('total', 0) // 1024,
        'ram_free_kb': mem.get('free', 0) // 1024,
        'flash_total_kb': flash.get('total_bytes', 0) // 1024,
        'flash_free_kb': flash.get('free_bytes', 0) // 1024
    }
    
    return summary


def display_system_info():
    """Display formatted system information"""
    cpu = get_cpu_info()
    mem = get_memory_info()
    flash = get_flash_info()
    
    print("\nCPU Information:")
    print(f"  Platform: {cpu.get('platform', 'unknown')}")
    print(f"  Implementation: {cpu.get('implementation', 'unknown')}")
    print(f"  Version: {cpu.get('version', 'unknown')}")
    
    if 'freq' in cpu:
        print(f"  Frequency: {cpu['freq'] / 1_000_000:.1f} MHz")
    
    if 'unique_id' in cpu:
        print(f"  Unique ID: {cpu['unique_id']}")
    
    print("\nMemory (RAM):")
    print(f"  Total: {mem['total'] / 1024:.1f} KB")
    print(f"  Free: {mem['free'] / 1024:.1f} KB")
    print(f"  Allocated: {mem['allocated'] / 1024:.1f} KB")
    print(f"  Usage: {(mem['allocated'] / mem['total'] * 100):.1f}%")
    
    if flash:
        print("\nFlash Storage:")
        print(f"  Total: {flash.get('total_bytes', 0) / 1024:.1f} KB")
        print(f"  Free: {flash.get('free_bytes', 0) / 1024:.1f} KB")
        print(f"  Used: {flash.get('used_bytes', 0) / 1024:.1f} KB")
        if flash.get('total_bytes', 0) > 0:
            usage = (flash.get('used_bytes', 0) / flash['total_bytes'] * 100)
            print(f"  Usage: {usage:.1f}%")


if __name__ == "__main__":
    display_system_info()

# Made with Bob
