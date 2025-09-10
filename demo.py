import servo, time
from machine import Pin
servo1= servo.Servo(Pin(4), min_us=540, max_us=2440)
servo1.write_angle(0)
time.sleep(2)
servo1.write_angle(90)
time.sleep(2)
servo1.write_angle(180)
time.sleep(2)
servo1.write_angle(90)