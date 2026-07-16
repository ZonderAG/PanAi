import numpy as np

class Triangulator:
    def __init__(self, config):
        self.geometry = config['geometry']
        self.working_distance = self.geometry['working_distance_mm']
        self.baseline = self.geometry['laser_camera_baseline_mm']
        self.angle_deg = self.geometry['laser_angle_deg']
        self.angle_rad = np.radians(self.angle_deg)
        
        # Mock intrinsics for MVP
        self.mm_per_px_approx = 200.0 / 1280.0
        self.cx = 1280 / 2
        self.cy = 720 / 2
        
    def triangulate(self, points_px):
        \"\"\"
        Converts (x_px, y_px) to (x_px, z_mm)
        Returns list of tuples to keep grid alignment for depth map construction.
        \"\"\"
        profile = []
        for x_px, y_px in points_px:
            dy_px = y_px - self.cy
            z_mm = (dy_px * self.mm_per_px_approx) / np.tan(self.angle_rad)
            profile.append((x_px, float(z_mm)))
            
        return profile
