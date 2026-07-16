import cv2
import threading
import time
import logging

class CameraCapture:
    def __init__(self, config):
        self.config = config['camera']
        self.device_index = self.config['device_index']
        self.width = self.config['combined_frame_width']
        self.height = self.config['combined_frame_height']
        self.fps = self.config['fps']
        self.active_lens = self.config['active_lens']
        
        self.cap = None
        self.running = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.thread = None
        
        self.logger = logging.getLogger(__name__)

    def _connect(self):
        if self.cap is not None:
            self.cap.release()
        
        self.logger.info(f"Connecting to camera {self.device_index}...")
        self.cap = cv2.VideoCapture(self.device_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        if not self.cap.isOpened():
            self.logger.error("Failed to open camera.")
            return False
            
        self.logger.info("Camera opened successfully.")
        return True

    def _capture_loop(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                if not self._connect():
                    time.sleep(1)
                    continue
            
            ret, frame = self.cap.read()
            frame_time_ns = time.time_ns()
            
            if not ret:
                self.logger.warning("Failed to read frame, reconnecting...")
                self.cap.release()
                time.sleep(1)
                continue
                
            # Split frame
            half_width = frame.shape[1] // 2
            if self.active_lens == "left":
                processed_frame = frame[:, :half_width]
            else:
                processed_frame = frame[:, half_width:]
                
            with self.lock:
                self.latest_frame = (processed_frame, frame_time_ns)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                frame, ts = self.latest_frame
                return frame.copy(), ts
            return None, None

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
