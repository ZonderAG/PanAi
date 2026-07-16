import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from panai_msgs.msg import FrameMeta, DepthProfile, SessionState
from diagnostic_updater import Updater, DiagnosticStatusWrapper
import diagnostic_msgs.msg
import threading
import time
import sys
import os
import math

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
crack_scanner_src = os.path.join(current_dir, 'crack_scanner', 'src')
sys.path.append(crack_scanner_src)
from config import load_config
from capture import CameraCapture
from laser_power import LaserPower
from laser_extraction import extract_laser_line
from triangulation import Triangulator
from sync_and_package import SyncAndPackage
from profile_stack import ProfileStack
from storage import Storage

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        
        self.declare_parameter('camera_device', '/dev/video0')
        
        default_config_path = os.path.join(current_dir, 'crack_scanner', 'config', 'config.yaml')
        self.declare_parameter('config_path', default_config_path)
        
        self.meta_pub = None
        self.profile_pub = None
        self.session_sub = None
        
        self.capture = None
        self.laser = None
        self.triangulator = None
        self.sync = None
        
        self.profile_stack = None
        self.storage = None
        
        self.is_session_active = False
        self.process_thread = None
        self.stop_thread = threading.Event()
        
        self.diag_updater = Updater(self)
        self.diag_updater.setHardwareID('gxvision_camera')
        self.diag_updater.add('Camera', self.check_camera)
        
        self.timer_group = ReentrantCallbackGroup()
        self.sub_group = ReentrantCallbackGroup()
        self.config = None
        self.session_id = ""
        
    def check_camera(self, stat: DiagnosticStatusWrapper):
        if self.capture and hasattr(self.capture, 'cap') and self.capture.cap is not None and self.capture.cap.isOpened():
            stat.summary(diagnostic_msgs.msg.DiagnosticStatus.OK, 'Camera active')
        else:
            stat.summary(diagnostic_msgs.msg.DiagnosticStatus.ERROR, 'Camera not opened')
        return stat
        
    def session_callback(self, msg: SessionState):
        if msg.state == 1: # ACTIVE
            if not self.is_session_active:
                self.get_logger().info(f"Session {msg.session_id} started. Initializing Storage.")
                self.session_id = msg.session_id
                self.profile_stack = ProfileStack()
                
                self.storage = Storage(self.config)
                self.is_session_active = True
        else:
            if self.is_session_active:
                self.get_logger().info("Session stopped. Finalizing Storage.")
                self.is_session_active = False
                if self.storage and self.profile_stack:
                    self.storage.finalize(self.profile_stack.get_all())
                self.storage = None
                self.profile_stack = None

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        config_path = self.get_parameter('config_path').value
        
        try:
            self.config = load_config(config_path)
        except Exception as e:
            self.get_logger().error(f"Failed to load config from {config_path}: {e}")
            return TransitionCallbackReturn.FAILURE
            
        self.config['camera']['device'] = self.get_parameter('camera_device').value
        
        try:
            self.capture = CameraCapture(self.config)
            self.laser = LaserPower(self.config)
            self.triangulator = Triangulator(self.config)
            self.sync = SyncAndPackage(self.config)
            
            self.laser.turn_on()
            
        except Exception as e:
            self.get_logger().error(f"Hardware initialization failed: {e}")
            if self.laser:
                self.laser.cleanup()
            return TransitionCallbackReturn.FAILURE
            
        self.meta_pub = self.create_lifecycle_publisher(FrameMeta, '/panai/vision/frame_meta', 10)
        self.profile_pub = self.create_lifecycle_publisher(DepthProfile, '/panai/vision/depth_profile', 10)
        self.session_sub = self.create_subscription(SessionState, '/panai/session/state', self.session_callback, 10, callback_group=self.sub_group)
        
        self.get_logger().info("Vision node configured successfully.")
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.capture.start()
        self.stop_thread.clear()
        self.process_thread = threading.Thread(target=self.processing_loop, daemon=True)
        self.process_thread.start()
        self.get_logger().info("Vision node activated. Processing loop started.")
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.stop_thread.set()
        if self.process_thread:
            self.process_thread.join()
        if self.capture:
            self.capture.stop()
        self.get_logger().info("Vision node deactivated.")
        return super().on_deactivate(state)

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        if self.laser:
            self.laser.cleanup()
        self.destroy_publisher(self.meta_pub)
        self.destroy_publisher(self.profile_pub)
        self.destroy_subscription(self.session_sub)
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.stop_thread.set()
        if self.process_thread:
            self.process_thread.join(timeout=1.0)
        if self.capture:
            self.capture.stop()
        if self.laser:
            self.laser.cleanup()
        return TransitionCallbackReturn.SUCCESS

    def processing_loop(self):
        roi_min = self.config['processing']['roi_y_min']
        roi_max = self.config['processing']['roi_y_max']
        thresh = self.config['processing']['brightness_threshold']
        
        last_frame_ts = 0
        frame_idx = 0
        
        while not self.stop_thread.is_set():
            if self.laser:
                self.laser.check_watchdog(True)
            
            frame_half, frame_time_ns = self.capture.get_latest_frame()
            if frame_half is None or frame_time_ns == last_frame_ts:
                time.sleep(0.005)
                continue
                
            last_frame_ts = frame_time_ns
            frame_idx += 1
            
            line_points_px = extract_laser_line(frame_half, thresh, roi_min, roi_max)
            
            profile_3d = self.triangulator.triangulate(line_points_px)
            
            mock_telemetry = {'esp_ts': 0, 'height_mm': 0.0, 'humidity': 0, 'strike': 0}
            packaged = self.sync.sync(frame_half, profile_3d, frame_time_ns, mock_telemetry)
            packaged['frame_index'] = frame_idx
            
            video_relpath = ""
            if self.is_session_active and self.storage:
                self.profile_stack.add_packaged_frame(packaged)
                self.storage.stream_write(packaged)
                video_relpath = "rgb/raw_video.avi" # Путь внутри папки сессии
                
            now_msg = self.get_clock().now().to_msg()
            
            if self.profile_pub and self.profile_pub.is_activated:
                dmsg = DepthProfile()
                dmsg.header.stamp = now_msg
                dmsg.header.frame_id = 'laser_link'
                
                width = self.config['camera']['combined_frame_width'] // 2
                z_array = [math.nan] * width
                for x_px, z_mm in profile_3d:
                    if 0 <= int(x_px) < width:
                        z_array[int(x_px)] = float(z_mm)
                        
                dmsg.z_mm = z_array
                dmsg.row_pitch_mm = 0.0 # Будет заполнено одометрией или калибровкой на уровне объединения
                self.profile_pub.publish(dmsg)
                
            if self.meta_pub and self.meta_pub.is_activated:
                mmsg = FrameMeta()
                mmsg.header.stamp = now_msg
                mmsg.frame_index = frame_idx
                mmsg.video_relpath = video_relpath
                self.meta_pub.publish(mmsg)

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
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
