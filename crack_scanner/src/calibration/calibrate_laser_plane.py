import yaml
from pathlib import Path

def main():
    print(\"Laser plane calibration script (placeholder).\")
    print(\"Instructions:\")
    print(\"1. Place a flat target at known distances (e.g., 150, 170, 190 mm).\")
    print(\"2. Record laser line pixel positions at each distance.\")
    print(\"3. Fit a plane equation in camera coordinates.\")
    print(\"4. Save results to calib/laser_plane.yaml\")
    
    calib_data = {
        'plane_equation': {
            'A': 0.0,
            'B': -1.0,
            'C': 1.0,
            'D': -170.0
        }
    }
    
    out_path = Path(__file__).parent.parent.parent / 'calib' / 'laser_plane.yaml'
    with open(out_path, 'w') as f:
        yaml.dump(calib_data, f)
    print(f\"Saved dummy laser plane to {out_path}\")

if __name__ == \"__main__\":
    main()
