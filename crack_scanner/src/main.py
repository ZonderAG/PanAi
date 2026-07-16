import time
import logging
import signal
import sys

from config import load_config
from capture import CameraCapture
from serial_receiver import SerialReceiverThread
from laser_power import LaserPower
from laser_extraction import extract_laser_line
from triangulation import Triangulator
from sync_and_package import SyncAndPackage
from profile_stack import ProfileStack
from storage import Storage
from visualization import Visualizer

running = True

def signal_handler(sig, frame):
    global running
    print('\\nGraceful shutdown requested...')
    running = False

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    
    config = load_config()
    logging.basicConfig(level=getattr(logging, config['runtime'].get('log_level', 'INFO')))
    logger = logging.getLogger(\"main\")
    logger.info(\"Starting V2 Pipeline (Real-time Triangulation)...\")
    
    laser = LaserPower(config)
    capture = CameraCapture(config)
    serial_rx = SerialReceiverThread(config)
    triangulator = Triangulator(config)
    sync = SyncAndPackage(config)
    profile_stack = ProfileStack()
    storage = Storage(config)
    visualizer = Visualizer(config)
    
    roi_min = config['processing']['roi_y_min']
    roi_max = config['processing']['roi_y_max']
    thresh = config['processing']['brightness_threshold']
    
    capture.start()
    serial_rx.start()
    
    time.sleep(2)
    laser.turn_on()
    
    logger.info(\"Starting processing loop. Press Ctrl+C to stop.\")
    last_frame_ts = 0
    
    try:
        while running:
            start_t = time.time()
            
            # Watchdog check
            telemetry_alive = serial_rx.get_latest() is not None
            laser.check_watchdog(telemetry_alive)
            
            # 1. Capture left-кадр (RGB)
            frame_half, frame_time_ns = capture.get_latest_frame()
            if frame_half is None or frame_time_ns == last_frame_ts:
                time.sleep(0.005)
                continue
            
            last_frame_ts = frame_time_ns
            
            # 2. Laser extraction (ROI, CoG, субпиксель)
            line_points_px = extract_laser_line(frame_half, thresh, roi_min, roi_max)
            
            # 3. Triangulation (px -> мм)
            profile_3d = triangulator.triangulate(line_points_px)
            
            # 4. Sync and Package (Soft Sync)
            telemetry = serial_rx.get_latest()
            packaged = sync.sync(frame_half, profile_3d, frame_time_ns, telemetry)
            
            # 5. Profile stack (накопление строк)
            profile_stack.add_packaged_frame(packaged)
            
            # 6. Storage (запись потока)
            storage.stream_write(packaged)
            
            # 7. Visualization
            visualizer.show_live(frame_half, line_points_px, profile_3d)
            
    except Exception as e:
        logger.error(f\"Error in main loop: {e}\")
        
    finally:
        logger.info(\"Shutting down...\")
        laser.cleanup()
        capture.stop()
        serial_rx.stop()
        visualizer.close()
        
        storage.finalize(profile_stack.get_all())
        logger.info(\"Shutdown complete.\")

if __name__ == \"__main__\":
    main()
