import lis3dh
import time
import machine

def demo():
    try:
        # Initialize the accelerometer with ESP32 default pins
        h3lis331dl = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
        
        # Read WHO AM I register
        who_am_i = h3lis331dl.read_who_am_i()
        print(f"WHO AM I: 0x{who_am_i:02X}")
        
        # Read raw acceleration data
        accl_raw = h3lis331dl.read_accl()
        print("Raw:    X = {0:6}   Y = {1:6}   Z = {2:6}"
              .format(accl_raw['x'], accl_raw['y'], accl_raw['z']))
        
        # Read acceleration data in g units
        accl_g = h3lis331dl.read_accl_g()
        print("Accel: AX = {0:6.3f}g AY = {1:6.3f}g AZ = {2:6.3f}g"
              .format(accl_g['x'], accl_g['y'], accl_g['z']))
        
    except KeyboardInterrupt:
        print("Measurement stopped by user")
    except Exception as e:
        print(f"Error: {e}")


demo()
