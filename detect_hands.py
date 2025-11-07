# Hand tracking → MQTT (macOS-friendly, non-blocking, toggleable)
# q = quit | c = clear trail | s = snapshot | m = toggle MediaPipe | p = toggle MQTT
# pip install paho-mqtt opencv-python mediapipe

import os, ssl, json, time
from collections import deque
import cv2, paho.mqtt.client as mqtt
import mediapipe as mp

# -------- MQTT --------
BROKER   = "71b19996472b44ef8901c930925513fd.s1.eu.hivemq.cloud"
PORT     = 8883
USERNAME = "hiveular"
PASSWORD = "1HiveMind"
TOPIC    = "/COM"
CLIENT_ID = f"pub-laptop-{os.getpid()}"

ENABLE_MQTT = True
SEND_QOS = 0          # non-blocking; switch to 1 AFTER things are smooth

def on_connect(c,u,f,rc,props):
    print("[MQTT] Connected" if not rc.is_failure else f"[MQTT] Connect failed: {rc}")
def on_disconnect(c,u,rc,props): print(f"[MQTT] Disconnected: {rc}")
def on_publish(c,u,mid,rc,props): pass

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5,
                     callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.on_connect = on_connect; client.on_disconnect = on_disconnect; client.on_publish = on_publish
client.reconnect_delay_set(1, 30)
client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

# -------- Camera / Window (macOS friendly) --------
CAM_INDEX = 0
API = cv2.CAP_AVFOUNDATION
cap = cv2.VideoCapture(CAM_INDEX, API)
if not cap.isOpened():
    cap.release(); cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise SystemExit("Could not open camera. Check permissions / device index.")

# lighter resolution than 1280x720
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  960)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # reduce latency

ok, frame = cap.read()
frame = cv2.flip(frame, 1)
if not ok or frame is None: raise SystemExit("First frame failed.")

try: cv2.startWindowThread()
except: pass
WIN = "Hand Tracker"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL); cv2.resizeWindow(WIN, 960, 540)
cv2.putText(frame, "Initializing...", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2, cv2.LINE_AA)
cv2.imshow(WIN, frame); cv2.waitKey(1)

# -------- MediaPipe --------
ENABLE_MP = True
mp_hands  = mp.solutions.hands
mp_draw   = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, model_complexity=1,
                       min_detection_confidence=0.6, min_tracking_confidence=0.6)

# -------- UI / publish helpers --------
TRAIL_LEN = 80
trails = {0: deque(maxlen=TRAIL_LEN), 1: deque(maxlen=TRAIL_LEN)}
last_time, acc_t, acc_n = time.time(), 0.0, 0
fps = 0.0
ANGLE_LIMIT = 20
MAX_HZ = 15.0
DEADBAND_DEG = 2
last_send_t, last_angle = 0.0, None

def clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v
def put(img, text, y): cv2.putText(img, text, (10,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)

def maybe_publish_angle(angle):
    global last_send_t, last_angle
    if not ENABLE_MQTT: return
    now = time.time()
    if now - last_send_t < 1.0 / MAX_HZ: return
    if last_angle is not None and abs(angle - last_angle) < DEADBAND_DEG: return
    payload = json.dumps({"type":"servo","angle": int(angle)})
    # non-blocking publish
    client.publish(TOPIC, payload, qos=SEND_QOS)
    last_angle, last_send_t = angle, now

print("[INFO] Running. Press m to toggle MediaPipe, p to toggle MQTT, q to quit.")

try:
    while True:
        ok, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if not ok: print("[WARN] Frame grab failed."); continue

        h, w = frame.shape[:2]
        angle = 0

        if ENABLE_MP:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            if result.multi_hand_landmarks:
                for i, handLms in enumerate(result.multi_hand_landmarks):
                    mp_draw.draw_landmarks(
                        frame, handLms, mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style()
                    )
                    tip = handLms.landmark[8]
                    x_pix, y_pix = int(tip.x * w), int(tip.y * h)
                    trails[i].append((x_pix, y_pix))
                    tip_off_center = (tip.x - 0.5) * 2.0
                    angle = int(clamp(tip_off_center * ANGLE_LIMIT, -ANGLE_LIMIT, ANGLE_LIMIT))
            else:
                # optional: center when no hand
                angle = 0

        # trails
        for dq in trails.values():
            for j in range(1, len(dq)):
                if dq[j-1] is None or dq[j] is None: continue
                thickness = max(1, int(6 * (j/TRAIL_LEN)))
                cv2.line(frame, dq[j-1], dq[j], (0,255,255), thickness)

        # fps
        now = time.time(); dt = now - last_time; last_time = now
        acc_t += dt; acc_n += 1
        if acc_t >= 0.5: fps, acc_t, acc_n = acc_n/acc_t, 0.0, 0

        put(frame, f"FPS: {fps:.1f}  MP:{int(ENABLE_MP)} MQTT:{int(ENABLE_MQTT)}", 28)
        put(frame, "q=quit  c=clear  s=snap  m=toggle MP  p=toggle MQTT", 56)
        cv2.imshow(WIN, frame)
        maybe_publish_angle(angle)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('c'): [trails[k].clear() for k in trails]
        elif key == ord('s'):
            fn = f"snaps/hand_{int(time.time())}.jpg"; cv2.imwrite(fn, frame); print("Saved:", fn)
        elif key == ord('m'):
            ENABLE_MP = not ENABLE_MP; print("[TOGGLE] MediaPipe =", ENABLE_MP)
        elif key == ord('p'):
            ENABLE_MQTT = not ENABLE_MQTT; print("[TOGGLE] MQTT =", ENABLE_MQTT)

except KeyboardInterrupt:
    print("Interrupted.")

finally:
    hands.close()
    cap.release()
    cv2.destroyAllWindows()
    client.loop_stop(); client.disconnect()
    print("[CLEANUP] Closed.")