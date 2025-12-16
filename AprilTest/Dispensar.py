import machine
from machine import Pin, PWM
import network
import socket
import time

# --- YOUR HOTSPOT CREDENTIALS (EXACT COPY) ---
SSID = "Sam iPhone"
PASSWORD = "12345678"

# --- SERVO CONFIGURATION ---
SERVO_PIN = 19 

class ServoMotor:
    def __init__(self, pin):
        self.servo = PWM(Pin(pin), freq=50)
        self.current_angle = 0
        
    def set_angle(self, angle):
        # 0° = ~26, 180° = ~128
        duty = int(26 + (angle * 102 / 180))
        self.servo.duty(duty)
        self.current_angle = angle
        
    def move_to(self, angle, speed=0.05):
        step = 5 if angle > self.current_angle else -5
        if angle == self.current_angle: return
            
        for pos in range(self.current_angle, angle + step, step):
            if (step > 0 and pos > angle) or (step < 0 and pos < angle): pos = angle
            self.set_angle(pos)
            time.sleep(speed)
            if pos == angle: break

# --- CONNECT TO HOTSPOT (EXACT COPY FROM CAR) ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print(f"Connecting to {SSID}...")

# Wait until connected (timeout after 10 seconds)
timeout = 10
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1
    print(".", end="")

if wlan.isconnected():
    print("\n--- CONNECTED! ---")
    print(f"DISPENSER IP ADDRESS: {wlan.ifconfig()[0]}")
    print("------------------")
    
    # Blink the onboard LED to show success
    try:
        led = machine.Pin(2, machine.Pin.OUT)
        for i in range(5):
            led.value(not led.value())
            time.sleep(0.1)
    except:
        pass
        
else:
    print("\nError: Could not connect. Check SSID apostrophe.")

# --- MAIN PROGRAM ---
def main():
    # Initialize Servo
    servo = ServoMotor(SERVO_PIN)
    servo.set_angle(0)
    
    # Dispense Pattern
    position_sequence = [0, 90, 180, 90] 
    current_step = 0

    # UDP Server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 5000))
    
    print("Ready to dispense. Press 'd' on computer.")

    while True:
        try:
            # Listen for packet
            data, addr = s.recvfrom(1024)
            msg = data.decode('utf-8')
            
            if msg == 'dispense':
                print(f"Dispensing! Step {current_step}")
                
                # Advance Sequence
                current_step = (current_step + 1) % len(position_sequence)
                target = position_sequence[current_step]
                
                # Move Servo
                servo.move_to(target, speed=0.02)
                
        except Exception as e:
            # If there's an error, just print it and keep listening
            print("Error:", e)
            # Re-init servo if needed, or just pass

if __name__ == "__main__":
    main()
