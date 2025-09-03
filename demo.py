import servo
from machine import Pin
servo1= servo.Servo(Pin(19))
servo1.write_angle(90)