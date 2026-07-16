import os
import cv2
import csv
import json
import numpy as np
from pathlib import Path
from datetime import datetime

class Storage:
    def __init__(self, config):
        self.output_dir = Path(config['runtime']['output_dir'])
        self.scan_id = datetime.now().strftime(\"%Y%m%d_%H%M%S\")
        self.scan_dir = self.output_dir / f\"scan_{self.scan_id}\"
        
        self.rgb_dir = self.scan_dir / \"rgb\"
        self.depth_dir = self.scan_dir / \"depth\"
        self.acoustic_dir = self.scan_dir / \"acoustic_spectra\"
        
        self.rgb_dir.mkdir(parents=True, exist_ok=True)
        self.depth_dir.mkdir(parents=True, exist_ok=True)
        self.acoustic_dir.mkdir(parents=True, exist_ok=True)
        
        self.fps = config['camera']['fps']
        
        # We need the width/height of the LEFT frame
        self.width = config['camera']['combined_frame_width'] // 2
        self.height = config['camera']['combined_frame_height']
        
        self.video_path = self.rgb_dir / \"raw_video.avi\"
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.video_writer = cv2.VideoWriter(str(self.video_path), self.fourcc, self.fps, (self.width, self.height))
        
        self.telemetry_path = self.scan_dir / \"telemetry_log.csv\"
        self.telemetry_file = open(self.telemetry_path, 'w', newline='')
        self.telemetry_writer = csv.writer(self.telemetry_file)
        self.telemetry_writer.writerow(['frame_index', 'rpi_ts_ns', 'esp_ts_ms', 'height_mm', 'humidity_raw', 'acoustic_trigger'])
        
    def stream_write(self, packaged):
        \"\"\"
        Write video frame and telemetry incrementally to avoid RAM overflow.
        \"\"\"
        self.video_writer.write(packaged['rgb_frame'])
        self.telemetry_writer.writerow([
            packaged['frame_index'],
            packaged['frame_time_ns'],
            packaged['esp_timestamp_ms'],
            packaged['height_mm'],
            packaged['humidity_raw'],
            packaged['acoustic_trigger']
        ])
        
    def finalize(self, profile_stack_data):
        \"\"\"
        Write accumulated depth profiles and meta.json.
        profile_stack_data is list of packaged dicts.
        \"\"\"
        self.video_writer.release()
        self.telemetry_file.close()
        
        # Save depth profiles and meta
        depth_meta_path = self.depth_dir / \"depth_meta.csv\"
        npy_path = self.depth_dir / \"depth_profiles.npy\"
        
        # Construct dense array for profiles. 
        # Since profile points count can vary, we will store a fixed width array (e.g. 1280) per frame.
        # Initialize with NaN
        num_frames = len(profile_stack_data)
        depth_matrix = np.full((num_frames, self.width), np.nan, dtype=np.float32)
        
        with open(depth_meta_path, 'w', newline='') as df:
            d_writer = csv.writer(df)
            d_writer.writerow(['frame_index', 'rpi_timestamp_ns', 'height_mm', 'num_valid_points'])
            
            for i, p in enumerate(profile_stack_data):
                pts = p['profile_3d']
                num_valid = len(pts)
                d_writer.writerow([p['frame_index'], p['frame_time_ns'], p['height_mm'], num_valid])
                
                for x_px, z_mm in pts:
                    if 0 <= int(x_px) < self.width:
                        depth_matrix[i, int(x_px)] = z_mm
                        
        np.save(str(npy_path), depth_matrix)
        
        # Save meta.json
        meta_path = self.scan_dir / \"meta.json\"
        with open(meta_path, 'w') as f:
            json.dump({
                'scan_id': self.scan_id,
                'total_frames': num_frames,
                'date': datetime.now().isoformat()
            }, f, indent=4)
