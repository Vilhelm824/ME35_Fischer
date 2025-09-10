import machine, time, math, urequests
from servo import Servo

# map the time to a degree output for the servo
# follows cos function 0-180deg linearly approaching 90deg
# supposed to resemble a pendulum
def TimeToDeg(t):
    deg = 90*math.cos(math.pi*t)*(-t/59+1)+90
    return int(deg)


# map UV index to degree output for servo
# scale 0-11+UV to 180-0deg
def UVToDeg(uv):
    # scale shows max 12UV
    if uv > 11:
        uv = 11
    deg = -uv*180/11+180
    return int(deg)

# Example from https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html 
def wifi_connect():
    import network # imports network library to connect to wifi
    import secrets # imports lib that has ssid and pwd
    sta_if = network.WLAN(network.WLAN.IF_STA)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(secrets.SSID, secrets.PWD)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ipconfig('addr4'))


def GetUV():
    # Define the API endpoint
    global url
    response = urequests.get(url, headers=None)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        return data["now"]["uvi"]
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def CheckButton():
    global STATE_CLOCK, STATE_UV, hasRequested
    if(button.value()==0):
        # swap modes if button pressed
        STATE_CLOCK = not STATE_CLOCK
        STATE_UV = not STATE_CLOCK
        hasRequested = False
        print("swapped mode")
        time.sleep_ms(500)


# var declerations
delta = 0.0 # time variable
servoPos = 90 # in deg
# api url for long and lat of my backyard
url = "https://currentuvindex.com/api/v1/uvi?latitude=42.406605&longitude=-71.110886"
# for iv https://currentuvindex.com/api/v1/uvi?latitude=34.409595&longitude=-119.866405
uvCurr = 11
hasRequested = False # use this to prevent constant api requests
STATE_CLOCK = True
STATE_UV = False

# initialize the wifi, servo, button, and ticker
wifi_connect()
hand = Servo(machine.Pin(4), min_us=540, max_us=2440) # calibrated for dial
button = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)
start = time.ticks_ms()

lastCycle = time.ticks_ms() # for testing loop run time


while(True):
    delta = time.ticks_diff(time.ticks_ms(), start) / 1000
    # reset counter each minute
    if(delta >= 60.0):
        start = time.ticks_ms()
        
    if STATE_CLOCK:
        servoPos = TimeToDeg(delta)
        hand.write_angle(servoPos)
        
    elif STATE_UV:
        # should only run once when changed into this mode
        if(not hasRequested):
            print('sending req')
            uvCurr = GetUV()
            print('got data')
            hasRequested = True
        servoPos = UVToDeg(uvCurr)
        hand.write_angle(servoPos)
    else:
        print("state err")
        
    CheckButton()
    
    #print(time.ticks_diff(time.ticks_ms(), lastCycle))
    lastCycle = time.ticks_ms()
