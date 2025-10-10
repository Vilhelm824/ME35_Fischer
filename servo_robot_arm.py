import time, math
import encoder, lis3dh, kinematics, servo
from machine import Pin, PWM


def servo_angle(servo, angle):
    #Using duty_ns
    maxd = 2500
    mind = 500
    duty = int(mind + angle*(maxd-mind)/180)
    servo.duty_ns(duty*1000)
    
    
def get_direction():
    x = (accl1.read_accl_g()['x'])
    y = (accl1.read_accl_g()['y'])
    if x > THRESHOLD:
        x = -1
    elif x < (-1*THRESHOLD):
        x = 1
    else:
        x = 0
    if y > THRESHOLD:
        y = 1
    elif y < (-1*THRESHOLD):
        y = -1
    else:
        y = 0
    return(x,y)


def stateButton(p):
    global STATE_ACCL_CONTROL, start
    #to control debounce
    global last_entered_time
    entered_time = time.ticks_ms() # time this function was called
    if((time.ticks_ms() - last_entered_time) < debounce_filter):
        return
    last_entered_time = entered_time
    start = time.ticks_ms()
    STATE_ACCL_CONTROL = not STATE_ACCL_CONTROL
    print("switching modes")
    
    
# accelerator value threshold--defines dead zone for tilting control
THRESHOLD = 0.6
# State - control with accelerometer or trace out path
STATE_ACCL_CONTROL = True
button_state = Pin(34, Pin.IN, Pin.PULL_UP)
debounce_filter = 100
last_entered_time = 0
button_state.irq(trigger=Pin.IRQ_RISING, handler=stateButton)
# initialize accelerometers on two I2C channels
accl1 = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
#accl2 = lis3dh.H3LIS331DL(sda_pin=33, scl_pin=32)
# initialize servos
servo1 = PWM(Pin(4), freq=50, duty_u16=0)
servo2 = PWM(Pin(5), freq=50, duty_u16=0)
# set servos to neutral pos
servo_angle(servo1, 90)
servo_angle(servo2, 180)
# set up kinematics
l1 = 108
l2 = 120
robo = kinematics.TwoDofArm(l1, l2)
# path function scaling + offset
fun_scale = 5
x_off = 70
y_off = 100
# scaling for accelerometer control
scale = .5
pos = (90,90)
time.sleep(2)
start = time.ticks_ms()
delta = 0.0 # time variable

while(True):
    if(STATE_ACCL_CONTROL):
        # get x,y data from accelerometers
        direction = get_direction()
        x = pos[0] + direction[0] * scale
        y = pos[1] + direction[1] * scale
    else:
        # get current time
        delta = time.ticks_diff(time.ticks_ms(), start) / 1000
        # reset time at 6.25s, the period of our parametric function
        if(delta > 6.25): start = time.ticks_ms()
        # get x,y data from parametric function (heart shape)
        x = fun_scale * (16*math.pow((math.sin(delta)), 3)) + x_off
        y = fun_scale * (13*math.cos(delta)-5*math.cos(2*delta)-2*math.cos(3*delta)-math.cos(4*delta)) + y_off
        
    # check if x,y is within reach of the arm
    if ((x + l1)**2 + y**2) < l1**2:
        print("in dead zone")
        theta = math.atan2(y,(x+l1))
        pos = (l1* math.cos(theta)-l1, l1 * math.sin(theta))
    elif (x**2 + y**2) > (l1+l2)**2:
        print("too far out")
        theta = math.atan2(y,x)
        print(theta)
        print(math.cos(theta))
        print(math.sin(theta))
        pos = ((l1+l2-4) * math.cos(theta), (l1+l2-4) * math.sin(theta))
    else:
        pos = (x,y)
        
    # find joint angles using inverse kinematics
    print (f"x: {pos[0]}  y: {pos[1]}")
    d1,d2 = robo.inverse(pos[0],pos[1])
    
    # if not valid angles for servos, skip iteration
    if(d1<0 or d1>180 or d2<0 or d2>180):
        print("continuing")
        continue
    
    # update servo positions
    print(f"angles: {d1}  {d2}")
    servo_angle(servo1, int(d1))
    servo_angle(servo2, int(d2))
    time.sleep(.01)
