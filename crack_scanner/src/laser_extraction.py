import cv2
import numpy as np

def extract_laser_line(frame_half, brightness_threshold=180, roi_min=0, roi_max=720):
    \"\"\"
    Vectorized extraction of the laser line center using Center of Gravity (CoG).
    Extracts within ROI to save computation.
    \"\"\"
    # Limit to ROI
    roi = frame_half[roi_min:roi_max, :]
    
    # Assuming red laser. Extract red channel. BGR format: red is channel 2
    if len(roi.shape) == 3:
        red_channel = roi[:, :, 2]
    else:
        red_channel = roi
        
    # Create mask for brightness threshold
    mask = red_channel > brightness_threshold
    weights = red_channel.astype(float) * mask
    
    # We want CoG along Y axis for each X column
    # Y coordinates array
    y_coords = np.arange(roi.shape[0]).reshape(-1, 1)
    
    # Sum of weights (denominator)
    sum_weights = np.sum(weights, axis=0)
    
    # Sum of y * weights (numerator)
    sum_y_weights = np.sum(weights * y_coords, axis=0)
    
    # To avoid division by zero
    valid_cols = sum_weights > 0
    
    # Calculate Y center
    y_centers_roi = np.zeros(roi.shape[1], dtype=float)
    y_centers_roi[valid_cols] = sum_y_weights[valid_cols] / sum_weights[valid_cols]
    
    # Add back roi_min offset
    y_centers_full = y_centers_roi + roi_min
    
    # Extract as list of (x, y) for valid columns
    x_valid = np.where(valid_cols)[0]
    y_valid = y_centers_full[valid_cols]
    
    return list(zip(x_valid, y_valid))
