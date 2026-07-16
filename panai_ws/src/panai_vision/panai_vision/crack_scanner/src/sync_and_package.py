import logging

class SyncAndPackage:
    def __init__(self, config):
        self.sync_window_ns = config['serial']['sync_window_ms'] * 1_000_000
        self.logger = logging.getLogger(__name__)
        self.frame_index = 0
        
    def sync(self, rgb_frame, profile_3d, frame_time_ns, telemetry):
        """
        Returns a packaged dictionary if successfully synchronized, 
        or partially synchronized if no telemetry is available.
        """
        packaged = {
            'frame_index': self.frame_index,
            'rgb_frame': rgb_frame,
            'profile_3d': profile_3d,
            'frame_time_ns': frame_time_ns,
            'telemetry_sync': False,
            'height_mm': 0.0,
            'humidity_raw': 0,
            'acoustic_trigger': 0,
            'esp_timestamp_ms': 0
        }
        
        if telemetry is not None:
            diff_ns = abs(frame_time_ns - telemetry['rpi_timestamp_ns'])
            if diff_ns <= self.sync_window_ns:
                packaged['telemetry_sync'] = True
                packaged['height_mm'] = telemetry['height_mm']
                packaged['humidity_raw'] = telemetry['humidity_raw']
                packaged['acoustic_trigger'] = telemetry['acoustic_trigger']
                packaged['esp_timestamp_ms'] = telemetry['esp_timestamp_ms']
            else:
                # Outside of window, we use last known telemetry but mark as desync
                packaged['height_mm'] = telemetry['height_mm']
                packaged['humidity_raw'] = telemetry['humidity_raw']
                packaged['acoustic_trigger'] = telemetry['acoustic_trigger']
                packaged['esp_timestamp_ms'] = telemetry['esp_timestamp_ms']
                
        self.frame_index += 1
        return packaged
