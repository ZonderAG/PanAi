import serial
import threading
import time
import logging

class SerialReceiverThread:
    def __init__(self, config):
        self.port = config['serial']['port']
        self.baudrate = config['serial']['baudrate']
        self.timeout = config['serial']['timeout_sec']
        
        self.ser = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Telemetry data format: 
        # rpi_timestamp_ns, esp_timestamp_ms, encoder_ticks, height_mm, humidity_raw, acoustic_trigger
        self.latest_telemetry = None 
        
        self.logger = logging.getLogger(__name__)

    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.logger.info(f"Connected to ESP32 on {self.port}")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to ESP32 on {self.port}: {e}")
            return False

    def _calculate_checksum(self, data_str):
        # Calculate XOR checksum of data_str (between $ and *)
        checksum = 0
        for char in data_str:
            checksum ^= ord(char)
        return checksum

    def _receive_loop(self):
        while self.running:
            if self.ser is None or not self.ser.is_open:
                if not self._connect():
                    time.sleep(1)
                    continue

            try:
                line_bytes = self.ser.readline()
                if not line_bytes:
                    continue
                
                recv_time_ns = time.time_ns()
                
                line = line_bytes.decode('ascii', errors='ignore').strip()
                if not line.startswith('$TELEMETRY') or '*' not in line:
                    continue
                    
                # Format: $TELEMETRY,ts,enc,height,hum,ac*cs
                data_part, checksum_part = line.split('*', 1)
                data_inner = data_part[1:] # remove $
                
                try:
                    received_cs = int(checksum_part, 16)
                    # Uncomment to enforce checksum verification
                    # if self._calculate_checksum(data_inner) != received_cs:
                    #     self.logger.warning("Checksum mismatch, dropping packet")
                    #     continue
                except ValueError:
                    continue
                
                parts = data_inner.split(',')
                if len(parts) == 6:
                    _, esp_ts, enc, h_mm, hum, ac_trig = parts
                    
                    telemetry_dict = {
                        'rpi_timestamp_ns': recv_time_ns,
                        'esp_timestamp_ms': int(esp_ts),
                        'encoder_ticks': int(enc),
                        'height_mm': float(h_mm),
                        'humidity_raw': int(hum),
                        'acoustic_trigger': int(ac_trig)
                    }
                    
                    with self.lock:
                        self.latest_telemetry = telemetry_dict
                        
            except Exception as e:
                self.logger.debug(f"Serial read error: {e}")
                time.sleep(0.01)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

    def get_latest(self):
        with self.lock:
            if self.latest_telemetry is not None:
                return self.latest_telemetry.copy()
            return None

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.ser is not None:
            self.ser.close()
