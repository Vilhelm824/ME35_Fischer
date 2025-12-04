import cv2
import numpy as np
import pyapriltags as apriltag
import math


# resize image and generate diff color versions for processing
def process_image(raw_img, scale_factor=0.2):
    if raw_img is None:
        raise FileNotFoundError("Image not loaded. Check file path.")
        
    # Resize the color image b/c doesn't fit in screen
    color_img = cv2.resize(raw_img, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
    
    # Create required image formats
    grayscale_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    hsv_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
    
    return color_img, grayscale_img, hsv_img


# update the data arrays for apriltag positions
def detect_apriltags(grayscale_img, detector, color_img, control_points, robot_points):

    
    tags = detector.detect(grayscale_img)
    control_tag_count = 0
    
    for tag in tags:
        Cx, Cy = int(tag.center[0]), int(tag.center[1])
        cv2.circle(color_img, (Cx, Cy), 10, (0, 0, 255), -1) # Draw center

        match tag.tag_id:
            case 0: control_points[0] = tag.center; control_tag_count += 1
            case 1: control_points[1] = tag.center; control_tag_count += 1
            case 2: control_points[2] = tag.center; control_tag_count += 1
            case 3: control_points[3] = tag.center; control_tag_count += 1
            case 4: 
                # Robot tag: Find center and orientation point
                robot_points["center"] = tag.center
                robot_points["top"] = (tag.corners[0] + tag.corners[1]) / 2
    
    return control_tag_count


# detect ball position by a color threshold
def detect_ball(hsv_img, color_img, lower_thresh, upper_thresh):
    
    ball_point = np.array([-1, -1], dtype=np.float32)
    ball_found = False
    largest_area = 0
    min_radius, max_radius = 5, 50 # Tune these based on image scale
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.inRange(hsv_img, lower_thresh, upper_thresh)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        area = cv2.contourArea(c)
        
        # Calculate radius and center properties (minEnclosingCircle is good for balls)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        
        # Filter by size
        if min_radius < radius < max_radius: 
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX, cY = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                
                if area > largest_area:
                    largest_area = area
                    ball_point[0], ball_point[1] = cX, cY
                    ball_found = True
                    
                    # Draw detected contour (using the last valid radius)
                    cv2.circle(color_img, (cX, cY), int(radius), (0, 255, 0), 2)
                    
    return ball_point, ball_found


def calculate_pose(H, robot_points, ball_point):
    """Applies Homography and calculates robot orientation."""
    
    # 1. Prepare input array
    input_points = np.array([
        robot_points["center"],     # Index 0: Robot Position (P_A)
        robot_points["top"],        # Index 1: Robot Direction (P_B)
        ball_point                  # Index 2: Ball Position
    ], dtype=np.float32).reshape(-1, 1, 2)

    # 2. Apply Homography
    target_points_transformed = cv2.perspectiveTransform(input_points, H)

    # 3. Extract points
    robot_x, robot_y = target_points_transformed[0][0]
    robot_tag_top_x, robot_tag_top_y = target_points_transformed[1][0]
    ball_x, ball_y = target_points_transformed[2][0]

    # 4. Calculate Orientation
    delta_X = robot_tag_top_x - robot_x
    delta_Y = robot_tag_top_y - robot_y

    orientation_radians = np.arctan2(delta_Y, delta_X)
    orientation_degrees = np.degrees(orientation_radians)
    orientation_normalized = (orientation_degrees + 360) % 360
    
    return robot_x, robot_y, orientation_normalized, ball_x, ball_y

# ------------------------- MAIN EXECUTION -----------------------------

# --- INITIALIZATION ---
# Define dimensions of autonomous zone
W = 140   # Target Zone Width (cm)
H = 140   # Target Zone Height (cm)

# Target Plane Points (undistorted coordinate system)
target_points = np.array([
    [0, 0],      # BL tag maps to (0, 0)
    [W, 0],      # BR tag maps to (W, 0)
    [W, H],      # TR tag maps to (W, H)
    [0, H]       # TL tag maps to (0, H)
], dtype=np.float32)

# Initialize control and robot state arrays
control_points = np.zeros((4, 2), dtype=np.float32)
robot_points = {"center": np.zeros(2, dtype=np.float32), 
                "top": np.zeros(2, dtype=np.float32)}

# Initialize ball point to a known invalid pixel coordinate
ball_point = np.array([-1, -1], dtype=np.float32)

# Color Thresholds (Orange Ping Pong Ball) and Kernel
lower_orange = np.array([0, 100, 100])
upper_orange = np.array([25, 255, 255])
detector = apriltag.Detector()
H = None # Stores the calculated Homography matrix

try:
    # --- IMAGE ACQUISITION AND PRE-PROCESSING ---
    # In a live system, this would be inside the 'while True' loop
    raw_color_img = cv2.imread('test1.jpg')
    color_img, grayscale_img, hsv_img = process_image(raw_color_img)
    
    # dedtect apriltags
    control_tag_count = detect_apriltags(grayscale_img, detector, color_img, control_points, robot_points)
    
    # detect ball
    ball_point, ball_found = detect_ball(hsv_img, color_img, kernel, lower_orange, upper_orange)

    # --- HOMOGRAPHY CALCULATION (Calibration) ---

    if control_tag_count != 4:
        raise RuntimeError(f"Calibration tags missing: Found only {control_tag_count} out of 4.")
    
    # Calculate H once
    if H is None:
        H, mask = cv2.findHomography(control_points, target_points, method=cv2.RANSAC)
        print("Homography Matrix calculated.")
    # if H is still None, there was a problem
    if H is None:
        raise RuntimeError("Homography calculation failed")

    # POSE CALCULATION
    robot_x, robot_y, robot_theta, ball_x, ball_y = calculate_pose(H, robot_points, ball_point)

    # OUTPUT AND DISPLAY
    print("\n--- Corrected Robot & Ball State ---")
    print(f"Robot Position (X, Y): ({robot_x:.2f} cm, {robot_y:.2f} cm)")
    print(f"Robot Orientation (Degrees): {robot_theta:.2f}°")
    
    if ball_found:
        print(f"Ball Position (X, Y): ({ball_x:.2f} cm, {ball_y:.2f} cm)")
    else:
        print("Ball Position: Not Detected.")

    cv2.imshow("Detection Overlay", color_img)
    cv2.waitKey(0)

except RuntimeError as e:
    print(f"FATAL ERROR: {e}")
except FileNotFoundError as e:
    print(f"FATAL ERROR: {e}")
finally:
    # ensure windows are closed
    cv2.destroyAllWindows()
    cv2.waitKey(1)