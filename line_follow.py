import time, neopixel
from machine import SoftI2C, Pin
from veml6040 import VEML6040
from encoder import Motor


def readColor(sensorR, sensorL):
    try:
        sensorR.trigger_measurement()
        sensorL.trigger_measurement()
        data = (sensorR.read_rgbw(), sensorL.read_rgbw())
        return data
    except OSError as e:
        if e.args[0] == 19: # errno 19 is ENODEV (No such device)
            print("I2C Error: VEML6040 not responding. Check wiring.")
        else:
            print(f"I2C Read Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    


# initialize motors
motorR = Motor(13, 12, 32,39)
motorL = Motor(27, 14, 32,39)
# initialize neopixel
np = neopixel.NeoPixel(Pin(15), 2)


# initialize I2C
# two channels bc 2 sensors w/ same addr
try:
    i2cR = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000) #Check for I2C pins from pinouts
    i2cL = SoftI2C(scl=Pin(32), sda=Pin(33), freq=100000) #Check for I2C pins from pinouts
    print("I2C initialized successfully.")
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit()

# initialize color sensors
try:
    sensorR = VEML6040(i2cR)
    sensorL = VEML6040(i2cL)
    print("VEML6040 sensor object created.")
except Exception as e:
    print(f"Error creating VEML6040 object: {e}")
    exit()


# sensor value threshold for white vs black
thresh = 550
motorSpeed = 30

# change sensor integration time to 40ms
IT_40MS = (0b000 << 4) # 40 ms
sensorR.set_integration_time(IT_40MS)
sensorL.set_integration_time(IT_40MS)


while(True):
    # get color data
    colorData = readColor(sensorR, sensorL)
    whiteR = colorData[0][3]
    whiteL = colorData[1][3]
    print(colorData)
    if(whiteR > thresh and whiteL > thresh):
        # go forward
        motorR.setSpeed(0, motorSpeed)
        motorL.setSpeed(0, motorSpeed)
    elif(whiteR < thresh and whiteL > thresh):
        # turn right
        motorR.setSpeed(1, motorSpeed)
        motorL.setSpeed(0, motorSpeed)
    elif(whiteR > thresh and whiteL < thresh):
        # turn left
        motorR.setSpeed(0, motorSpeed)
        motorL.setSpeed(1, motorSpeed)
    elif(whiteR < thresh and whiteL < thresh):
        # stop
        motorR.stop()
        motorL.stop()
