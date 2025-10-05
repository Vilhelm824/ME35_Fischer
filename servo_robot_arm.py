import servo, encoder, lis3dh, kinematics, time

def ReadXY():
    x = (accl1.read_accl_g()['x'] + cartXOFF) * cartScale
    y = (accl2.read_accl_g()['y'] + cartYOFF) * cartScale
    return(x,y)

# scaling factor to convert accelerometer vals to cartesian coords
cartScale = 100
# offset vals for the same purpose
cartXOFF = 0
cartYOFF = 0

# initialize accelerometers on two I2C channels
accl1 = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
accl2 = lis3dh.H3LIS331DL(sda_pin=33, scl_pin=32)

# initialize servos
servo1 = servo.Servo(4)
servo2 = servo.Servo(5)
# set servos to neutral pos
servo1.write_angle(90)
servo2.write_angle(90)

# set up kinematics
l1 = 120
l2 = 120
robo = kinematics.TwoDofArm(l1, l2)


# TODO: control loop
# currently only positions arm based on accl readings
# needs a path to follow
while(True):
    # get x,y data from accelerometers
    x,y = ReadXY()
    # find joint angles using inverse kinematics
    d1,d2 = robo.inverse(x,y)
    
    print(f"Position: ({x:+4.0f}, {y:+4.0f})\t Angles: ({d1:4.0f}, {d2:4.0f})")
    
    # if not valid angles for servos, skip iteration
    if(d1<0 or d1>180 or d2<0 or d2>180):
        continue
    # update servo positions
    servo1.write_angle(d1)
    servo2.write_angle(d2)
    
    time.sleep(0.1)
    