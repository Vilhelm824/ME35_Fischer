import servo, encoder, lis3dh, kinematics

# initialize accelerometers on two I2C channels
accl1 = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
accl2 = lis3dh.H3LIS331DL(sda_pin=33, scl_pin=32)
# accelerometer test
accl1_val = accl1.read_accl_g()['x']
accl2_val = accl2.read_accl_g()['x']

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

