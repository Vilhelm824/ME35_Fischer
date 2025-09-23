import time
from machine import SoftI2C, Pin
from veml6040 import VEML6040
from encoder import Motor


def readColor(sensor):
    try:
        sensor.trigger_measurement()
        red, green, blue, white = sensor.read_rgbw()
        return red, green, blue, white
    except OSError as e:
        if e.args[0] == 19: # errno 19 is ENODEV (No such device)
            print("I2C Error: VEML6040 not responding. Check wiring.")
        else:
            print(f"I2C Read Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# sensor value threshold for white vs black
threshold = 15000

# initialize motor
motor = Motor(14,27, 32,39)

# initialize I2C
try:
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000) #Check for I2C pins from pinouts
    print("I2C initialized successfully.")
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit()

# initialize color sensor
try:
    sensor = VEML6040(i2c)
    print("VEML6040 sensor object created.")
except Exception as e:
    print(f"Error creating VEML6040 object: {e}")
    exit()


red, green, blue, white = readColor(sensor)
print(f"Red: {red}, Green: {green}, Blue: {blue}, White: {white}")


while True:
    # get color data
    red, green, blue, white = readColor(sensor)
    print(white)
    if(white < threshold):
        # slow down
        motor.stop()
    else:
        motor.setSpeed(0, 20)
    time.sleep(0.5)
        
