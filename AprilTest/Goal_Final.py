import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time

# MQTT SETTINGS
MQTT_BROKER = "71b19996472b44ef8901c930925513fd.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "ball/goal_status"
MQTT_CLIENT_ID = "ball_detector"
mqtt_username = "hiveular"
mqtt_pass = "1HiveMind"

CAMERA_INDEX = 1  

TOP_LINE_Y_PERCENT = 15      # Top horizontal line
LEFT_LINE_X_PERCENT = 25     # Left vertical line
RIGHT_LINE_X_PERCENT = 75    # Right vertical line

# COLOR DETECTION
BLUE_LOWER = np.array([90, 50, 50])
BLUE_UPPER = np.array([130, 255, 255])

MIN_SATURATION = 80
MIN_VALUE = 60
MAX_VALUE = 255
MIN_AREA = 100

# GOAL TIMING
GOAL_DURATION = 5 
MISS_DURATION = 3

# MQTT SETUP
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(username=mqtt_username, password=mqtt_pass)
mqtt_client.tls_set()

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print(f"Connected to MQTT broker")
except Exception as e:
    print(f"Warning: Could not connect to MQTT broker: {e}")

# INITIALIZE CAMERA
print(f"Initializing camera {CAMERA_INDEX}...")
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Error: Cannot open camera {CAMERA_INDEX}")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("\n" + "="*70)
print("BALL GOAL DETECTION SYSTEM")
print("="*70)
print("Controls:")
print("  'q' - Quit")
print("  'c' - Toggle calibration window")
print("  '+/-' - Adjust top line up/down")
print("  'l' - Move left line left")
print("  'L' - Move left line right")
print("  'r' - Move right line right")
print("  'R' - Move right line left")
print("  'SPACE' - Reset status")
print("="*70 + "\n")

show_calibration = False

# Goal tracking - LOCKED once triggered
goal_locked = False
miss_locked = False
goal_start_time = None
miss_start_time = None
last_publish_time = 0
PUBLISH_INTERVAL = 1  # Publish every 0.5 seconds

def get_color_name(hue):
    """Convert HSV hue value to color name"""
    if hue < 11:
        return "RED"
    elif hue < 25:
        return "ORANGE"
    elif hue < 35:
        return "YELLOW"
    elif hue < 85:
        return "GREEN"
    elif hue < 130:
        return "BLUE"
    elif hue < 170:
        return "PURPLE"
    else:
        return "RED"

def publish_status(status):
    """Publish status to MQTT"""
    global last_publish_time
    current_time = time.time()
    
    if current_time - last_publish_time >= PUBLISH_INTERVAL:
        try:
            message = f"{status}|{current_time}"
            mqtt_client.publish(MQTT_TOPIC, message)
            print(f"MQTT: {status}")
            last_publish_time = current_time
        except Exception as e:
            print(f"MQTT Error: {e}")

def reset_status():
    """Reset goal/miss status"""
    global goal_start_time, miss_start_time, goal_locked, miss_locked
    goal_start_time = None
    miss_start_time = None
    goal_locked = False
    miss_locked = False
    publish_status("WAITING")
    print("Status reset")

def draw_lines(frame, height, width):
    """Draw the three black lines"""
    top_y = int(height * TOP_LINE_Y_PERCENT / 100)
    left_x = int(width * LEFT_LINE_X_PERCENT / 100)
    right_x = int(width * RIGHT_LINE_X_PERCENT / 100)
    
    # Draw lines
    cv2.line(frame, (0, top_y), (width, top_y), (0, 0, 0), 3) # top
    cv2.line(frame, (left_x, top_y), (left_x, height), (0, 0, 0), 3) # left
    cv2.line(frame, (right_x, top_y), (right_x, height), (0, 0, 0), 3) # right
    
    # Label zones
    cv2.putText(frame, "GOAL", (int((left_x + right_x)/2) - 30, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, "MISS", (10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, "MISS", (right_x + 10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    return top_y, left_x, right_x

def check_ball_zone(center, top_y, left_x, right_x, height):
    """Check which zone the ball is in - ONLY if not already locked"""
    global goal_start_time, miss_start_time, goal_locked, miss_locked
    
    # If already locked into a goal or miss, don't check anymore
    if goal_locked or miss_locked:
        return
    
    x, y = center
    
    # Only check if ball is below the top line
    if y > top_y:
        # Check if in middle section (GOAL)
        if left_x <= x <= right_x:
            if not goal_locked:
                goal_locked = True
                goal_start_time = time.time()
                publish_status("GOAL")
                print("*** GOAL SCORED - LOCKED FOR 10 SECONDS ***")
        # Check if in outer sections (MISS)
        else:
            if not miss_locked:
                miss_locked = True
                miss_start_time = time.time()
                publish_status("MISS")
                print("*** MISSED SHOT - LOCKED FOR 3 SECONDS ***")

# Main loop
while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Cannot read frame")
        break
    
    height, width = frame.shape[:2]
    
    # Draw lines and get coordinates
    top_y, left_x, right_x = draw_lines(frame, height, width)
    
    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create mask for colored objects (high saturation)
    saturation_mask = cv2.inRange(hsv, 
                                   np.array([0, MIN_SATURATION, MIN_VALUE]), 
                                   np.array([180, 255, MAX_VALUE]))
    
    # Create mask to exclude blue
    blue_mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    blue_mask = cv2.bitwise_not(blue_mask)
    
    # Combine masks
    mask = cv2.bitwise_and(saturation_mask, blue_mask)
    
    # Remove noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    ball_detected = False
    current_status = "WAITING"
    status_color = (255, 255, 0)
    
    # Process contours
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        if area > MIN_AREA:
            (x, y), radius = cv2.minEnclosingCircle(largest_contour)
            center = (int(x), int(y))
            radius = int(radius)
            
            perimeter = cv2.arcLength(largest_contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            else:
                circularity = 0
            
            if circularity > 0.6 and radius > 3:
                ball_detected = True
                cx, cy = center
                
                if 0 <= cy < hsv.shape[0] and 0 <= cx < hsv.shape[1]:
                    pixel_hsv = hsv[cy, cx]
                    h_value = pixel_hsv[0]
                    ball_color = get_color_name(h_value)
                    
                    # Set circle color
                    if ball_color == "RED":
                        circle_color = (0, 0, 255)
                    elif ball_color == "ORANGE":
                        circle_color = (0, 165, 255)
                    elif ball_color == "YELLOW":
                        circle_color = (0, 255, 255)
                    elif ball_color == "GREEN":
                        circle_color = (0, 255, 0)
                    elif ball_color == "PURPLE":
                        circle_color = (255, 0, 255)
                    else:
                        circle_color = (255, 255, 255)
                else:
                    ball_color = "UNKNOWN"
                    circle_color = (255, 255, 255)
                
                # Draw ball
                cv2.circle(frame, center, radius, circle_color, 2)
                cv2.circle(frame, center, 5, circle_color, -1)
                
                # Draw ball info
                text = f"{ball_color} Ball"
                cv2.putText(frame, text, (center[0] - 50, center[1] - radius - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, circle_color, 2)
                
                # Check which zone the ball is in (only if not locked)
                check_ball_zone(center, top_y, left_x, right_x, height)
    
    # Determine current status based on locked timers
    current_time = time.time()
    
    if goal_locked and goal_start_time is not None:
        elapsed = current_time - goal_start_time
        if elapsed < GOAL_DURATION:
            remaining = GOAL_DURATION - elapsed
            current_status = f"GOAL! ({remaining:.1f}s)"
            status_color = (0, 255, 0)
            publish_status("GOAL")
        else:
            # Unlock after duration expires
            goal_locked = False
            goal_start_time = None
            current_status = "WAITING"
            status_color = (255, 255, 0)
            publish_status("WAITING")
    
    elif miss_locked and miss_start_time is not None:
        elapsed = current_time - miss_start_time
        if elapsed < MISS_DURATION:
            remaining = MISS_DURATION - elapsed
            current_status = f"MISS! ({remaining:.1f}s)"
            status_color = (0, 0, 255)
            publish_status("MISS")
        else:
            # Unlock after duration expires
            miss_locked = False
            miss_start_time = None
            current_status = "WAITING"
            status_color = (255, 255, 0)
            publish_status("WAITING")
    
    else:
        # Not locked, publish waiting if no ball
        if not ball_detected:
            publish_status("WAITING")
    
    # Display status message
    cv2.rectangle(frame, (10, 10), (width - 10, 80), (0, 0, 0), -1)
    cv2.putText(frame, current_status, (20, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
    
    # Display line positions
    cv2.putText(frame, f"Top: {TOP_LINE_Y_PERCENT}% | L: {LEFT_LINE_X_PERCENT}% | R: {RIGHT_LINE_X_PERCENT}%", 
               (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Display frame
    cv2.imshow('Ball Detection', frame)
    
    # Show calibration windows if requested
    if show_calibration:
        cv2.imshow('HSV', hsv)
        cv2.imshow('Mask', mask)
    
    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        show_calibration = not show_calibration
        if not show_calibration:
            cv2.destroyWindow('HSV')
            cv2.destroyWindow('Mask')
    elif key == ord('+') or key == ord('='):
        TOP_LINE_Y_PERCENT = max(0, TOP_LINE_Y_PERCENT - 1)
        print(f"Top Line: {TOP_LINE_Y_PERCENT}%")
    elif key == ord('-') or key == ord('_'):
        TOP_LINE_Y_PERCENT = min(100, TOP_LINE_Y_PERCENT + 1)
        print(f"Top Line: {TOP_LINE_Y_PERCENT}%")
    elif key == ord('l'):
        LEFT_LINE_X_PERCENT = max(0, LEFT_LINE_X_PERCENT - 1)
        print(f"Left Line: {LEFT_LINE_X_PERCENT}%")
    elif key == ord('L'):
        LEFT_LINE_X_PERCENT = min(RIGHT_LINE_X_PERCENT - 1, LEFT_LINE_X_PERCENT + 1)
        print(f"Left Line: {LEFT_LINE_X_PERCENT}%")
    elif key == ord('r'):
        RIGHT_LINE_X_PERCENT = min(100, RIGHT_LINE_X_PERCENT + 1)
        print(f"Right Line: {RIGHT_LINE_X_PERCENT}%")
    elif key == ord('R'):
        RIGHT_LINE_X_PERCENT = max(LEFT_LINE_X_PERCENT + 1, RIGHT_LINE_X_PERCENT - 1)
        print(f"Right Line: {RIGHT_LINE_X_PERCENT}%")
    elif key == ord(' '):
        reset_status()

publish_status("SHUTDOWN")
mqtt_client.loop_stop()
mqtt_client.disconnect()
cap.release()
cv2.destroyAllWindows()
print("Ball detection stopped")
