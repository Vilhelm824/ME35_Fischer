import cv2
import numpy as np
import pyapriltags as apriltag
import time
import math
import json
import paho.mqtt.client as mqtt


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


# detect the apriltag positions in the image
def detect_apriltags(grayscale_img, detector, color_img, control_points, robot_points):

    tags = detector.detect(grayscale_img)
    control_tag_count = 0
    robot_found = False
    
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
                robot_found = True
    
    return control_tag_count, robot_found


# detect ball position in image by a color threshold
def detect_ball(hsv_img, color_img, lower_thresh, upper_thresh, kernel):
    # Blue exclusion range  filter this out
    BLUE_LOWER = np.array([90, 50, 50])      # Covers cyan to deep blue
    BLUE_UPPER = np.array([130, 255, 255])

    ball_point = np.array([-1000, -1000], dtype=np.float32)
    ball_found = False
    largest_area = 0
    min_radius, max_radius = 1, 5 # Tune these based on image scale

    saturation_mask = cv2.inRange(hsv_img, lower_thresh, upper_thresh)
    # Create mask for blue
    blue_mask = cv2.inRange(hsv_img, BLUE_LOWER, BLUE_UPPER)
    blue_mask = cv2.bitwise_not(blue_mask)  # Invert to exclude blue
    # Combine masks: keep only saturated colors that are NOT blue
    mask = cv2.bitwise_and(saturation_mask, blue_mask)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        area = cv2.contourArea(c)
        
        # Calculate radius and center properties (minEnclosingCircle is good for balls)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        # Calculate circularity to verify it’s round
        perimeter = cv2.arcLength(c, True)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
        else:
            circularity = 0
        # Filter by size
        if (min_radius < radius < max_radius) and circularity > 0.6: 
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX, cY = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                
                if area > largest_area:
                    largest_area = area
                    ball_point[0], ball_point[1] = cX, cY
                    ball_found = True
                    
                    # Draw detected contour (using the last valid radius)
                    cv2.circle(color_img, (cX, cY), int(radius), (0, 255, 0), 2)
                    print(circularity)
                    
    return ball_point, ball_found


# apply homography to calculate robot and ball coordinate positions
def calculate_pose(H, robot_points, ball_point):
    
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
    orientation_normalized = (orientation_radians + 2*math.pi) % (2*math.pi)
    orientation_degrees = np.degrees(orientation_radians)
    
    
    return robot_x, robot_y, orientation_normalized, ball_x, ball_y

# ------------------------- MAIN EXECUTION -----------------------------

# Define dimensions of autonomous zone
W = 135   # Target Zone Width (cm)
H = 139   # Target Zone Height (cm)

# Target Plane Points (undistorted coordinate system of autonomous zone)
target_points = np.array([
    [0, 0],      # BL tag maps to (0, 0)
    [W, 0],      # BR tag maps to (W, 0)
    [W, H],      # TR tag maps to (W, H)
    [0, H]       # TL tag maps to (0, H)
], dtype=np.float32)

# Initialize control, robot, and ball state arrays
control_points = np.zeros((4, 2), dtype=np.float32)
robot_points = {"center": np.zeros(2, dtype=np.float32), 
                "top": np.zeros(2, dtype=np.float32)}
ball_point = np.array([-1000, -1000], dtype=np.float32)

# Color Thresholds (Orange Ping Pong Ball) and Kernel
lower_orange = np.array([0, 20, 50])
upper_orange = np.array([179, 255, 255])
kernel = np.ones((5, 5), np.uint8)

detector = apriltag.Detector()
H = None # Stores the calculated Homography matrix

FRAME_DELAY = 0.2

mqtt_url = "71b19996472b44ef8901c930925513fd.s1.eu.hivemq.cloud"
mqtt_port = 8883
mqtt_username = "hiveular"
mqtt_pass = "1HiveMind"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(username=mqtt_username, password=mqtt_pass)
client.tls_set()
print("connecting to mqtt")
client.connect(mqtt_url, mqtt_port)
print("starting mqtt loop")
client.loop_start()

print("initializing webcam")
cap = cv2.VideoCapture(1)

# Check if camera opened successfully
if not cap.isOpened():
    raise RuntimeError("Error: Could not open camera")

try:
    print("starting processing loop")
    while True:
        # raw_color_img = cv2.imread('test2.jpg')
        ret, raw_color_img = cap.read()
        if not ret:
            print("couldn't capture frame, continuing")
            time.sleep(0.1)
            continue
        color_img, grayscale_img, hsv_img = process_image(raw_color_img, scale_factor=0.5)
        
        # detect apriltags
        control_tag_count, robot_found = detect_apriltags(grayscale_img, detector, color_img, control_points, robot_points)
        
        # detect ball
        ball_point, ball_found = detect_ball(hsv_img, color_img, lower_orange, upper_orange, kernel)

        # show image with all the overlays of detected tags + ball
        cv2.imshow("Detection Overlay", color_img)

        if control_tag_count != 4:
            print(f"Calibration tags missing: Found only {control_tag_count} out of 4.")
            time.sleep(0.1)
            continue
        
        # Calculate homography matrix H once (camera is stationary)
        if H is None:
            print("Calculating Homography Matrix")
            H, mask = cv2.findHomography(control_points, target_points, method=cv2.RANSAC)
            print("Homography Matrix calculated.")
        # if H is still None, there was a problem
        if H is None:
            print("Homography calculation failed")
            time.sleep(0.1)
            continue

        # calculate robot and ball coords with homography
        robot_x, robot_y, robot_theta, ball_x, ball_y = calculate_pose(H, robot_points, ball_point)

        pos_data_json = json.dumps({
            'robot_found':robot_found,
            'robot_x':float(robot_x),
            'robot_y':float(robot_y),
            'robot_theta':float(robot_theta),
            'ball_found':ball_found,
            'ball_x':float(ball_x),
            'ball_y':float(ball_y)
            })

        print("publishing: ", pos_data_json)

        msg_info = client.publish("robot/position", pos_data_json, qos=0)

        time.sleep(FRAME_DELAY)
        cv2.waitKey(1)

except RuntimeError as e:
    print(f"FATAL ERROR: {e}")
except FileNotFoundError as e:
    print(f"FATAL ERROR: {e}")
finally:
    # ensure windows are closed
    client.loop_stop()
    cv2.destroyAllWindows()
    cv2.waitKey(1)