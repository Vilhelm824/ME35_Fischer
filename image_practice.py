import cv2

cap = cv2.VideoCapture(0)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    b, g, r = cv2.split(frame)
    cv2.imshow("Selfie camera :) ", g)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.imwrite('output.jpg', frame) #save the last frame
        break

# Release everything when done
cap.release()
cv2.destroyAll