#!/usr/bin/env python3
"""Live edge-counter readout for the RX-signal-detect firmware (main.c).

Polls g_rx_sbus_stats (PA2) and g_ail_stats (PA3) over an already-running
OpenOCD telnet RPC session (default localhost:4444) while the target keeps
executing -- no halt, no UART, no extra wiring beyond the ST-Link already
attached. Start OpenOCD separately first, e.g.:

    openocd -f interface/stlink.cfg -f target/stm32f1x.cfg

then run this script alongside it.
"""
import argparse
import re
import socket
import time

# From `arm-none-eabi-nm build/hacked_firmware.elf` after the current build.
# Each signal_stats_t is 3 uint32_t words: edge_count, last_period_us, last_edge_cycle.
RX_SBUS_ADDR = 0x20000034
AIL_ADDR = 0x20000028


def send(sock, cmd):
    sock.sendall((cmd + "\n").encode())
    data = b""
    sock.settimeout(0.5)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b"> ") or data.endswith(b"\xfb\x01"):
                break
    except socket.timeout:
        pass
    return data.decode(errors="replace")


def read_words(sock, addr, count):
    out = send(sock, f"mdw 0x{addr:08x} {count}")
    m = re.search(r"0x[0-9a-fA-F]+:\s+((?:[0-9a-fA-F]{8}\s*)+)", out)
    if not m:
        return None
    return [int(w, 16) for w in m.group(1).split()]


def fmt(name, words, prev_count, dt):
    if words is None:
        return f"{name}: <read failed -- is OpenOCD's telnet server (port 4444) running and attached?>"
    count, period_us, _ = words
    rate_str = ""
    if prev_count is not None and dt > 0:
        delta = count - prev_count
        if delta < 0:
            delta += 1 << 32
        rate_str = f"  ({delta / dt:6.1f} edges/s)"
    return f"{name}: edges={count:10d}  last_period_us={period_us:8d}{rate_str}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=4444)
    ap.add_argument("--interval", type=float, default=0.5, help="seconds between polls")
    args = ap.parse_args()

    sock = socket.create_connection((args.host, args.port), timeout=5)
    send(sock, "")  # drain the banner/initial prompt

    last_rx = None
    last_ail = None
    t_prev = time.time()

    print(f"Polling g_rx_sbus_stats (PA2, RX_SBUS) / g_ail_stats (PA3, AIL) every {args.interval}s. Ctrl+C to stop.\n")
    try:
        while True:
            rx = read_words(sock, RX_SBUS_ADDR, 3)
            ail = read_words(sock, AIL_ADDR, 3)
            now = time.time()
            dt = now - t_prev
            t_prev = now

            print(fmt("RX_SBUS(PA2)", rx, last_rx, dt))
            print(fmt("AIL    (PA3)", ail, last_ail, dt))
            print("-" * 64)

            if rx is not None:
                last_rx = rx[0]
            if ail is not None:
                last_ail = ail[0]

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
