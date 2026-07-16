import struct

# Constants
SOF = b'\xAA\x55'

# RPi -> ESP32
CMD_STRIKE = 0x01
CMD_PING = 0x02

# ESP32 -> RPi
MSG_SPECTRUM = 0x81
MSG_TELEMETRY = 0x82
MSG_PONG = 0x83

def calc_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def encode_frame(msg_type: int, payload: bytes = b'') -> bytes:
    length = len(payload)
    type_len_payload = struct.pack('<BH', msg_type, length) + payload
    crc = calc_crc16(type_len_payload)
    return SOF + type_len_payload + struct.pack('<H', crc)

class ProtocolParser:
    def __init__(self):
        self.buffer = bytearray()
        
    def feed(self, data: bytes):
        self.buffer.extend(data)
        frames = []
        while len(self.buffer) >= 7: # min size: SOF(2) + TYPE(1) + LEN(2) + CRC(2)
            sof_idx = self.buffer.find(SOF)
            if sof_idx == -1:
                self.buffer.clear()
                break
            
            if sof_idx > 0:
                self.buffer = self.buffer[sof_idx:]
            
            if len(self.buffer) < 7:
                break
                
            msg_type = self.buffer[2]
            length = struct.unpack('<H', self.buffer[3:5])[0]
            
            total_frame_size = 5 + length + 2
            if len(self.buffer) < total_frame_size:
                break # Wait for more data
                
            frame_data = self.buffer[:total_frame_size]
            payload = frame_data[5:5+length]
            expected_crc = struct.unpack('<H', frame_data[-2:])[0]
            
            type_len_payload = frame_data[2:5+length]
            actual_crc = calc_crc16(type_len_payload)
            
            if actual_crc == expected_crc:
                frames.append((msg_type, payload))
                self.buffer = self.buffer[total_frame_size:]
            else:
                # Corrupted frame, skip SOF and search again
                self.buffer = self.buffer[2:]
                
        return frames

def decode_spectrum(payload: bytes):
    # hit_id:u32, fft_n:u16, num_bins:u16, bin_start_hz:f32, bin_end_hz:f32, spectrum:int16[num_bins]
    header_fmt = '<IHHff'
    header_size = struct.calcsize(header_fmt)
    hit_id, fft_n, num_bins, bin_start_hz, bin_end_hz = struct.unpack(header_fmt, payload[:header_size])
    spectrum_fmt = f'<{num_bins}h'
    spectrum = struct.unpack(spectrum_fmt, payload[header_size:])
    return hit_id, fft_n, num_bins, bin_start_hz, bin_end_hz, list(spectrum)

def decode_telemetry(payload: bytes):
    # timestamp_ms:u32, humidity_raw:u16, encoder_ticks:i32, status_flags:u8
    fmt = '<IHib'
    timestamp_ms, humidity_raw, encoder_ticks, status_flags = struct.unpack(fmt, payload)
    return timestamp_ms, humidity_raw, encoder_ticks, status_flags
