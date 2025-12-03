import cv2
import numpy as np
import pyapriltags as apriltag


cap = cv2.VideoCapture(0)
# Check if the camera opened successfully (Good Practice)
if not cap.isOpened():
    raise RuntimeError("Error: Could not open video stream.")

# color_img = cv2.imread('test2.jpg')
# image was too big to see in viewing pane
# color_img = cv2.resize(color_img, (0, 0), fx=0.2, fy=0.2, interpolation=cv2.INTER_AREA)

ret, color_img = cap.read()
# make grayscale and hsv images for processing
img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
hsv_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
cv2.imshow("image", color_img)

detector = apriltag.Detector()

# april tags coords from camera that bound the autonomous zone
control_points = np.array([
    [0, 0],  # Bottom-Left (BL) tag pixel center
    [0, 0],  # Bottom-Right (BR) tag pixel center
    [0, 0],  # Top-Right (TR) tag pixel center
    [0, 0]    # Top-Left (TL) tag pixel center
], dtype=np.float32)

# Target Plane Points (undistorted coordinate system)
# define dimensions of autonomous zone
W = 140  # Zone Width (cm)
H = 140   # Zone Height (cm)
target_points = np.array([
    [0, 0],      # BL tag maps to (0, 0)
    [W, 0],      # BR tag maps to (W, 0)
    [W, H],      # TR tag maps to (W, H)
    [0, H]       # TL tag maps to (0, H)
], dtype=np.float32)

# robot april tag points
robot_points = {"center":np.array([0,0], dtype=np.float32), "top":np.array([0,0], dtype=np.float32)}
ball_point = np.array([0,0], dtype=np.float32)

while(True):
    ret, color_img = cap.read()
    # make grayscale and hsv images for processing
    img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    hsv_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2HSV)
    # find apriltags
    tags = detector.detect(img)
    # track the number control tags to make sure they are all detected
    control_tag_count = 0

    for tag in tags:
        print(tag.tag_id) 
        

        # find the center of each tag
        Cx = int(tag.center[0])
        Cy = int(tag.center[1])
        # draw a circle over the center
        cv2.circle(color_img, (Cx, Cy), 10, (0, 0, 255), -1)

        match tag.tag_id:
            case 0: 
                control_points[0] = tag.center # BL tag
                control_tag_count += 1
            case 1:
                control_points[1] = tag.center # BR tag
                control_tag_count += 1
            case 2:
                control_points[2] = tag.center # TR tag
                control_tag_count += 1
            case 3:
                control_points[3] = tag.center # TL tag
                control_tag_count += 1
            # tag on robot
            case 4:
                # find midpoint of top edge of apriltag. Used for orientation
                # assuming these points are on the front of the robot
                top_center = (tag.corners[0] + tag.corners[1]) / 2
                # save position values
                robot_points["center"] = tag.center
                robot_points["top"] = top_center
        

    ## ball detection ##
    # Define Color Thresholds for Ping Pong Ball (orange)
    lower_orange = np.array([0, 100, 100])
    upper_orange = np.array([25, 255, 255])

    # Create Mask for ball
    mask = cv2.inRange(hsv_img, lower_orange, upper_orange)
    # clean up the mask--erode removes noise; Dilate fills holes
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    # Find external contours in the mask 
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # process contrours to locate ball
    ball_found = False
    min_radius = 5
    max_radius = 50
    largest_area = 0
    best_center = None

    if len(contours) > 0:
        for c in contours:
            area = cv2.contourArea(c)
            # Calculate radius and center properties
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            # filter the size, tune for the camera setup
            if min_radius < radius < max_radius: 
                # Find the center of the contour
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    
                    # Track the largest contour
                    if area > largest_area:
                        largest_area = area
                        best_center = (cX, cY)
                        ball_found = True

    if ball_found and best_center is not None:
        # Update the global ball_point array with the detected center pixel coordinates
        ball_point[0] = best_center[0]
        ball_point[1] = best_center[1]
        
        # Draw detected contour
        cv2.circle(color_img, best_center, int(radius), (255, 0, 0), 2)
        print(f"Ball detected at pixel: {best_center}")

    else:
        # If the ball is not found, leave ball_point as the last known position
        print("Ball not detected in frame.")


    cv2.imshow("image", color_img)

    # Caclulate homography matrix
    # note: maybe only needs to be done at initialization b/c camera won't move
    H, mask = cv2.findHomography(control_points, target_points, method=cv2.RANSAC)

    print("Homography Matrix (H):\n", H)

    if control_tag_count != 4:
        raise RuntimeError(f"Calibration tags missing: Found only {control_tag_count} out of 4.")
    if H is None:
        raise RuntimeError(f"Homography calculation failed")
    
    # Needs to be reshaped for cv2 perspectiveTransform
    # Combine all points into a single array shaped (N, 1, 2)
    input_points = np.array([
        robot_points["center"],   # Index 0: Robot Position
        robot_points["top"],      # Index 1: Robot Direction
        ball_point            # Index 2: Ball Position
    ], dtype=np.float32).reshape(-1, 1, 2)

    # Apply Homography
    # Transform all pixel coordinates to the Target Plane
    target_points_transformed = cv2.perspectiveTransform(input_points, H)

    # Extract transformed points
    robot_x, robot_y = target_points_transformed[0][0]  # Robot Center
    robot_tag_top_x, robot_tag_top_y = target_points_transformed[1][0]  # Robot Direction Point
    ball_x, ball_y = target_points_transformed[2][0] # Ball Center

    # Calculate Robot Orientation (Angle)
    delta_X = robot_tag_top_x - robot_x
    delta_Y = robot_tag_top_y - robot_y

    # Calculate angle using atan2
    orientation_radians = np.arctan2(delta_Y, delta_X)
    orientation_degrees = np.degrees(orientation_radians)
    orientation_normalized = (orientation_degrees + 360) % 360

    print("\n--- Corrected Robot & Ball State ---")
    print(f"Robot Position (X, Y): ({robot_x:.2f}, {robot_y:.2f})")
    print(f"Robot Orientation (Degrees): {orientation_normalized:.2f}°")
    print(f"Ball Position (X, Y): ({ball_x:.2f}, {ball_y:.2f})")

cv2.waitKey(0)
cv2.destroyAllWindows()