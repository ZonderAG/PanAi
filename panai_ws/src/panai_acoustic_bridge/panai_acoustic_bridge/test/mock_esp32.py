#!/usr/bin/env python3
import struct
import time
import threading
import sys
import os
import pty

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import (
    ProtocolParser, encode_frame, CMD_STRIKE, CMD_PING, MSG_SPECTRUM, MSG_TELEMETRY, MSG_PONG
)

def create_virtual_serial():
    master, slave = pty.openpty()
    import tty
    import termios
    tty.setraw(master)
    tty.setraw(slave)
    s_name = os.ttyname(slave)
    print(f"Mock ESP32 connected to: {s_name}")
    print(f"Please run node with parameter: serial_port:={s_name}")
    return master, s_name

def main():
    master, port_name = create_virtual_serial()
    parser = ProtocolParser()
    hit_counter = 0
    
    def telemetry_loop():
        while True:
            time.sleep(0.5) # 2 Hz
            ts = int(time.time() * 1000) & 0xFFFFFFFF
            payload = struct.pack('<IHib', ts, 1024, 0, 0)
            frame = encode_frame(MSG_TELEMETRY, payload)
            try:
                os.write(master, frame)
            except OSError:
                break

    threading.Thread(target=telemetry_loop, daemon=True).start()
    
    try:
        while True:
            data = os.read(master, 1024)
            if data:
                frames = parser.feed(data)
                for msg_type, payload in frames:
                    if msg_type == CMD_PING:
                        os.write(master, encode_frame(MSG_PONG))
                    elif msg_type == CMD_STRIKE:
                        # Simulate strike delay
                        time.sleep(0.1)
                        hit_counter += 1
                        num_bins = 1900
                        # hit_id:u32, fft_n:u16, num_bins:u16, bin_start_hz:f32, bin_end_hz:f32, spectrum:int16[num_bins]
                        header = struct.pack('<IHHff', hit_counter, 4096, num_bins, 1000.0, 20000.0)
                        spectrum = struct.pack(f'<{num_bins}h', *([-5000] * num_bins))
                        os.write(master, encode_frame(MSG_SPECTRUM, header + spectrum))
    except KeyboardInterrupt:
        print("\nExiting...")
    except OSError:
        print("\nPort closed")

if __name__ == '__main__':
    main()
