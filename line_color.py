import time, neopixel
from machine import SoftI2C, Pin
from veml6040 import VEML6040


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

# sensor value threshold for colors
thresh_red = 8000
thresh_grn = 5000
thresh_blu = 3500
thresh_wht = 15000

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
    
# initialize neopixel
np = neopixel.NeoPixel(Pin(15), 2)
np[0] = (0, 0, 0)
np[1] = np[0]
np.write()

red, green, blue, white = readColor(sensor)
print(f"Red: {red}, Green: {green}, Blue: {blue}, White: {white}")


while True:
    # get color data
    red, green, blue, white = readColor(sensor)
    print(red, green, blue, white)
    
    if(red > thresh_red and white < thresh_wht):
        np[0] = (255, 0, 0)
        np[1] = np[0]
        np.write()
    elif(green > thresh_grn and white < thresh_wht):
        np[0] = (0, 255, 0)
        np[1] = np[0]
        np.write()
    elif(blue > thresh_blu and white < thresh_wht):
        np[0] = (0, 0, 255)
        np[1] = np[0]
        np.write()    
        
    time.sleep(0.5)
        

