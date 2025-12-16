import machine
from machine import Pin, PWM
import network
import socket
import time

# --- CONFIGURATION ---
SSID = "Sam iPhone"
PASSWORD = "12345678"

# --- SPEED SETTINGS (Dynamic) ---
# We store these as variables so we can change them
current_max_speed  = 1023  # Starts Fast
current_turn_speed = 600   # Starts Fast Turn

# --- PINS ---
p1 = PWM(Pin(12), freq=1000) 
p2 = PWM(Pin(13), freq=1000)
p3 = PWM(Pin(14), freq=1000)
p4 = PWM(Pin(27), freq=1000)

SERVO_PIN = 19

# --- SERVO CLASS ---
class ServoMotor:
    def __init__(self, pin):
        self.servo = PWM(Pin(pin), freq=50)
        self.angle = 20 # Start Down
        self.set_angle(20) 
        
    def set_angle(self, angle):
        duty = int(26 + (angle * 102 / 180))
        self.servo.duty(duty)
        self.angle = angle
        
    def move_smooth(self, target, speed=0.02):
        step = 5 if target > self.angle else -5
        if target == self.angle: return
        
        for pos in range(self.angle, target + step, step):
            if (step > 0 and pos > target) or (step < 0 and pos < target): pos = target
            self.set_angle(pos)
            time.sleep(speed)
            if pos == target: break

# --- MOTOR FUNCTIONS (Now use dynamic variables) ---
def stop():  
    p1.duty(0); p2.duty(0); p3.duty(0); p4.duty(0)

def fwd():   
    p1.duty(current_max_speed); p2.duty(0)
    p3.duty(current_max_speed); p4.duty(0)

def bwd():   
    p1.duty(0); p2.duty(current_max_speed)
    p3.duty(0); p4.duty(current_max_speed)

def left():  
    # Left Motors Back, Right Motors Forward
    p1.duty(0); p2.duty(current_turn_speed)
    p3.duty(current_turn_speed); p4.duty(0)

def right(): 
    # Left Motors Forward, Right Motors Back
    p1.duty(current_turn_speed); p2.duty(0)
    p3.duty(0); p4.duty(current_turn_speed)

# --- WIFI SETUP ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting...")
while not wlan.isconnected():
    time.sleep(0.5)
    print(".", end="")
print(f"\nCAR READY: {wlan.ifconfig()[0]}")

# --- MAIN LOOP ---
def main():
    # Allow us to write to these global variables
    global current_max_speed, current_turn_speed
    
    servo = ServoMotor(SERVO_PIN)
    arm_is_up = False 
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 5000))
    
    while True:
        try:
            data, addr = s.recvfrom(1024)
            msg = data.decode('utf-8')
            
            # --- DRIVE COMMANDS ---
            if msg == 'fwd': fwd()
            elif msg == 'bwd': bwd()
            elif msg == 'lft': left()
            elif msg == 'rgt': right()
            elif msg == 'stop': stop()
            
            # --- SPEED MODES ---
            elif msg == 'fast':
                print("Mode: FAST")
                current_max_speed = 1023
                current_turn_speed = 600
            elif msg == 'slow':
                print("Mode: SLOW")
                current_max_speed = 300  # 55% Speed
                current_turn_speed = 200 # Gentle turns
            
            # --- ARM CONTROL ---
            elif msg == 'arm':
                if arm_is_up:
                    servo.move_smooth(20) # Down
                    arm_is_up = False
                else:
                    servo.move_smooth(90) # Up
                    arm_is_up = True
                    
        except Exception as e:
            stop()

if __name__ == "__main__":
    main()
