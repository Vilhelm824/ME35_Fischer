

import machine
import time
from machine import SoftI2C, Pin
from veml6040 import VEML6040

try:
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000) #Check for I2C pins from pinouts
    print("I2C initialized successfully.")
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit()


try:
    sensor = VEML6040(i2c)
    print("VEML6040 sensor object created.")
except Exception as e:
    print(f"Error creating VEML6040 object: {e}")
    exit()



while True:
    try:
        sensor.trigger_measurement()
        red, green, blue, white = sensor.read_rgbw()
        print(f"Red: {red}, Green: {green}, Blue: {blue}, White: {white}")
    except OSError as e:
        if e.args[0] == 19: # errno 19 is ENODEV (No such device)
            print("I2C Error: VEML6040 not responding. Check wiring.")
        else:
            print(f"I2C Read Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    time.sleep(2)