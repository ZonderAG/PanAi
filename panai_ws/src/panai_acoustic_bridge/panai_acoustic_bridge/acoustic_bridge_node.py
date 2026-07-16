import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from panai_msgs.srv import TriggerStrike
from panai_msgs.msg import AcousticSpectrum, EnvironmentSample
from diagnostic_updater import Updater, DiagnosticStatusWrapper
import diagnostic_msgs.msg
import serial
import threading
import time
import queue
from .protocol import (
    ProtocolParser, encode_frame, decode_spectrum, decode_telemetry,
    CMD_STRIKE, CMD_PING, MSG_SPECTRUM, MSG_TELEMETRY, MSG_PONG
)

class AcousticBridgeNode(Node):
    def __init__(self):
        super().__init__('acoustic_bridge_node')
        
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('telemetry_timeout_s', 2.0)
        
        self.serial_port = None
        self.read_thread = None
        self.stop_thread = threading.Event()
        
        self.spectrum_pub = None
        self.humidity_pub = None
        self.trigger_srv = None
        
        self.parser = ProtocolParser()
        self.last_telemetry_time = 0.0
        
        # Queues for inter-thread communication
        self.pong_queue = queue.Queue()
        self.spectrum_queue = queue.Queue()
        self.telemetry_queue = queue.Queue()
        
        self.diag_updater = Updater(self)
        self.diag_updater.setHardwareID('esp32_acoustic')
        self.diag_updater.add('Connection', self.check_connection)
        
        self.timer_group = ReentrantCallbackGroup()
        self.srv_group = ReentrantCallbackGroup()
        
    def check_connection(self, stat: DiagnosticStatusWrapper):
        timeout = self.get_parameter('telemetry_timeout_s').value
        if self.serial_port and self.serial_port.is_open:
            time_since = time.time() - self.last_telemetry_time
            if time_since > timeout and self.last_telemetry_time > 0:
                stat.summary(diagnostic_msgs.msg.DiagnosticStatus.ERROR, 'esp32_unreachable')
                stat.add('Time since last telemetry', str(time_since))
            else:
                stat.summary(diagnostic_msgs.msg.DiagnosticStatus.OK, 'Connected')
        else:
            stat.summary(diagnostic_msgs.msg.DiagnosticStatus.ERROR, 'Disconnected')
        return stat

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        
        try:
            self.serial_port = serial.Serial(port, baud, timeout=0.1)
        except Exception as e:
            self.get_logger().error(f"Failed to open port {port}: {e}")
            return TransitionCallbackReturn.FAILURE
            
        self.stop_thread.clear()
        self.read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
        self.read_thread.start()
        
        # Ping
        self.serial_port.write(encode_frame(CMD_PING))
        try:
            self.pong_queue.get(timeout=2.0)
            self.get_logger().info("PONG received, configured successfully.")
        except queue.Empty:
            self.get_logger().error("No PONG response from ESP32.")
            self.stop_thread.set()
            self.read_thread.join()
            self.serial_port.close()
            return TransitionCallbackReturn.FAILURE
            
        self.spectrum_pub = self.create_lifecycle_publisher(AcousticSpectrum, '/panai/acoustic/spectrum', 10)
        self.humidity_pub = self.create_lifecycle_publisher(EnvironmentSample, '/panai/env/humidity', 10)
        
        # ROS2 callbacks reading from queues
        self.process_timer = self.create_timer(0.05, self.process_queues, callback_group=self.timer_group)
        self.trigger_srv = self.create_service(TriggerStrike, '/panai/acoustic/trigger_strike', self.trigger_callback, callback_group=self.srv_group)
        
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.last_telemetry_time = time.time() # Reset timeout
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        return super().on_deactivate(state)

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.stop_thread.set()
        if self.read_thread:
            self.read_thread.join()
        if self.serial_port:
            self.serial_port.close()
            
        self.destroy_publisher(self.spectrum_pub)
        self.destroy_publisher(self.humidity_pub)
        self.destroy_service(self.trigger_srv)
        self.destroy_timer(self.process_timer)
        
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.stop_thread.set()
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        return TransitionCallbackReturn.SUCCESS

    def serial_read_loop(self):
        while not self.stop_thread.is_set():
            try:
                data = self.serial_port.read(1024)
                if data:
                    frames = self.parser.feed(data)
                    for msg_type, payload in frames:
                        if msg_type == MSG_PONG:
                            self.pong_queue.put(True)
                        elif msg_type == MSG_TELEMETRY:
                            self.last_telemetry_time = time.time()
                            self.telemetry_queue.put(payload)
                        elif msg_type == MSG_SPECTRUM:
                            self.spectrum_queue.put(payload)
            except Exception as e:
                self.get_logger().error(f"Serial read error: {e}")
                time.sleep(1.0)

    def process_queues(self):
        # Process telemetry
        while not self.telemetry_queue.empty():
            payload = self.telemetry_queue.get()
            if self.humidity_pub and self.humidity_pub.is_activated:
                ts_ms, hum_raw, enc, flags = decode_telemetry(payload)
                msg = EnvironmentSample()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.humidity_raw = hum_raw
                self.humidity_pub.publish(msg)
                
        # Process spectrums that came asynchronously (not via srv)
        while not self.spectrum_queue.empty():
            payload = self.spectrum_queue.get()
            if self.spectrum_pub and self.spectrum_pub.is_activated:
                msg = self._build_spectrum_msg(payload)
                self.spectrum_pub.publish(msg)

    def _build_spectrum_msg(self, payload):
        hit_id, fft_n, num_bins, bin_start, bin_end, spec_data = decode_spectrum(payload)
        msg = AcousticSpectrum()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.hit_id = hit_id
        msg.fft_n = fft_n
        msg.num_bins = num_bins
        msg.bin_start_hz = bin_start
        msg.bin_end_hz = bin_end
        msg.spectrum_db_x100 = spec_data
        return msg

    def trigger_callback(self, request, response):
        if not self.serial_port or not self.serial_port.is_open:
            response.success = False
            response.message = "Port not open"
            return response
            
        # Send command
        self.serial_port.write(encode_frame(CMD_STRIKE))
        
        # Wait for spectrum response
        try:
            payload = self.spectrum_queue.get(timeout=3.0)
            msg = self._build_spectrum_msg(payload)
            
            if self.spectrum_pub and self.spectrum_pub.is_activated:
                self.spectrum_pub.publish(msg)
                
            response.success = True
            response.spectrum = msg
            response.message = "Strike successful"
        except queue.Empty:
            response.success = False
            response.message = "Timeout waiting for spectrum"
            
        return response

def main(args=None):
    rclpy.init(args=args)
    node = AcousticBridgeNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
