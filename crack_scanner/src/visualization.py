import cv2
import numpy as np

class Visualizer:
    def __init__(self, config):
        self.enabled = config['runtime'].get('visualization_enabled', False)
        
    def show_live(self, frame_half, line_points_px, profile_3d):
        if not self.enabled:
            return
            
        vis_frame = frame_half.copy()
        if len(vis_frame.shape) == 2:
            vis_frame = cv2.cvtColor(vis_frame, cv2.COLOR_GRAY2BGR)
            
        for x, y in line_points_px:
            cv2.circle(vis_frame, (int(x), int(y)), 1, (0, 255, 0), -1)
            
        cv2.imshow("Laser Extraction", vis_frame)
        
        plot_h = 400
        plot_w = 800
        plot_img = np.zeros((plot_h, plot_w, 3), dtype=np.uint8)
        
        if profile_3d:
            # Map X from 0..1280 to 0..800
            # Map Z from -20..20 to 0..400
            xs = np.array([p[0] for p in profile_3d])
            zs = np.array([p[1] for p in profile_3d])
            
            if len(xs) > 1:
                x_min, x_max = 0, 1280
                z_min, z_max = -20, 20
                
                xs_px = ((xs - x_min) / (x_max - x_min)) * plot_w
                zs_px = plot_h / 2 - ((zs) / (z_max - z_min)) * (plot_h / 2)
                
                pts = np.vstack((xs_px, zs_px)).astype(np.int32).T
                cv2.polylines(plot_img, [pts], False, (255, 255, 255), 1)
                    
        cv2.imshow("2D Profile", plot_img)
        cv2.waitKey(1)
        
    def close(self):
        if self.enabled:
            cv2.destroyAllWindows()
