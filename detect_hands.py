# Hand tracking with fingertip trail (macOS-friendly)
# q = quit | c = clear trail | s = save frame
import cv2, time, os, json
from collections import deque

# ----- MQTT Setup -----
url = "71b19996472b44ef8901c930925513fd.s1.eu.hivemq.cloud"
username = "hiveular"
password = "1HiveMind"
portnumber = 8883




# ----- Camera setup (macOS: AVFoundation) -----
CAM_INDEX = 0
API = cv2.CAP_AVFOUNDATION  # on Windows/Linux, use cv2.VideoCapture(0) without API
cap = cv2.VideoCapture(CAM_INDEX, API)
if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise SystemExit("Could not open camera. Check Camera permissions and try index 1.")

cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ----- MediaPipe Hands -----
import mediapipe as mp
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
mp_styles= mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,          # 0=fast, 1=balanced, 2=accurate
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ----- fingertip trails (per hand) -----
# Index finger tip is landmark id 8
TRAIL_LEN = 80
trails = {0: deque(maxlen=TRAIL_LEN), 1: deque(maxlen=TRAIL_LEN)}  # hand 0, hand 1
os.makedirs("snaps", exist_ok=True)
cv2.namedWindow("Hand Tracker", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Hand Tracker", 960, 540)
last = time.time(); fps = 0.0; acc_t = 0.0; acc_n = 0
def put(img, text, y):
    cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)
while True:
    ok, frame = cap.read()
    if not ok:
        print("Frame grab failed.")
        break
    # MediaPipe expects RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    h, w = frame.shape[:2]
    
    # var for tracking how far fingertip is from center of frame
    # 0 is center, goes from -1 to 1
    tip_off_center = 0
    # Draw hands + collect fingertip points
    if result.multi_hand_landmarks:
        for i, handLms in enumerate(result.multi_hand_landmarks):
            # Draw connections and landmarks (nice default style)
            mp_draw.draw_landmarks(
                frame, handLms, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style()
            )
            # fingertip (landmark 8) in pixels
            tip = handLms.landmark[8]
            print(tip.x)
            # calculate how far the fingertip is from the center
            tip_off_center = (tip.x - 0.5)*2
            angle = int(tip_off_center * 10)
            json_str = json.dumps({"type":"servo", "angle":f"{angle}"})
            
            x, y = int(tip.x * w), int(tip.y * h)
            trails[i].append((x, y))
    else:
        # no hands → slowly fade trails (optional)
        pass
    # Draw fingertip trails as polylines (smooth)
    for dq in trails.values():
        for j in range(1, len(dq)):
            if dq[j-1] is None or dq[j] is None:
                continue
            thickness = max(1, int(6 * (j / TRAIL_LEN)))  # thicker for recent points
            cv2.line(frame, dq[j-1], dq[j], (0, 255, 255), thickness)
    # Simple FPS
    now = time.time()
    dt = now - last; last = now
    acc_t += dt; acc_n += 1
    if acc_t >= 0.5:
        fps = acc_n / acc_t
        acc_t = 0.0; acc_n = 0
    put(frame, f"FPS: {fps:.1f}", 28)
    put(frame, "q=quit  c=clear trail  s=snapshot", 56)
    cv2.imshow("Hand Tracker", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        for k in trails: trails[k].clear()
    elif key == ord('s'):
        fn = f"snaps/hand_{int(time.time())}.jpg"
        cv2.imwrite(fn, frame); print("Saved:", fn)
        
    
# Cleanup
hands.close()
cap.release()
cv2.destroyAllWindows()
client.disconnect()