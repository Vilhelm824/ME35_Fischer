import lis3dh, time, encoder, math
from machine import Pin

# KNN for K=1 
def nearest_neighbor(x,y):
    dist_min = 100000
    col = None
    # iterate to find the closest datapoint to the input
    for index, d in enumerate(data): # d is the data point for each iteration
        dist = math.sqrt((x-d[0])**2 + (y-d[1])**2)
        if(dist < dist_min):
            dist_min = dist
            tag = d[2]
    return tag


# button to record data points in training mode
def trainButton(p):
    global data
    global train_mode
    global STATE_TRAIN
    
    # to control debounce
    global last_entered_time
    entered_time = time.ticks_ms() # time this function was called
    if(time.ticks_diff(time.ticks_ms(),last_entered_time) < debounce_filter):
        return
    last_entered_time = entered_time 
    
    # only records data if in training mode
    if(STATE_TRAIN):
        # uses x and y acceleration data
        new_data = [h3lis331dl.read_accl_g()['x'], h3lis331dl.read_accl_g()['y'] , train_mode]
        data.append(new_data)
        print("recorded data point ", new_data)
    else:
        print("not in training mode")


# Enter training mode and cycle through the training states
def trainModeButton(p):
    global STATE_PLAY, STATE_TRAIN
    global train_mode
    # to control debounce
    global last_entered_time
    entered_time = time.ticks_ms() # time this function was called
    if(time.ticks_diff(time.ticks_ms(),last_entered_time) < debounce_filter):
        return
    last_entered_time = entered_time 
    print("pressed train mode")
    # update state to training mode
    STATE_PLAY = False
    STATE_TRAIN = True
    # cycle modes: 1=fwd, 0=stop, -1=bkwd
    train_mode += 1
    if(train_mode > 1):
        train_mode = -1
    print("training mode: ", train_mode)
    

def playButton(p):
    global STATE_PLAY, STATE_TRAIN
    
    # to control debounce
    global last_entered_time
    entered_time = time.ticks_ms() # time this function was called
    if(time.ticks_diff(time.ticks_ms(),last_entered_time) < debounce_filter):
        return
    last_entered_time = entered_time 
    print("play mode")
    # update state to play mode
    STATE_PLAY = True
    STATE_TRAIN = False

# Initialize the accelerometer with ESP32 I2C pins
h3lis331dl = lis3dh.H3LIS331DL(sda_pin=21, scl_pin=22)
# Initialize motor
motor = encoder.Motor(27, 14, 32,39)
# Initialize buttons
button_Train =  Pin(35, Pin.IN, Pin.PULL_UP)
button_Play = Pin(34, Pin.IN, Pin.PULL_UP)
button_TrainMode = Pin(25, Pin.IN, Pin.PULL_UP)
# debounce control vars
debounce_filter = 100
last_entered_time = 0
# KNN data array
data = []
# start in training mode
STATE_TRAIN = True
STATE_PLAY = False

train_mode = 0 # fwd=1, stop=0, bkwd=-1
motor_dir = 0
# buttons set up as interrupts, see callback functions
button_Train.irq(trigger=Pin.IRQ_RISING, handler=trainButton)
button_Play.irq(trigger=Pin.IRQ_RISING, handler=playButton)
button_TrainMode.irq(trigger=Pin.IRQ_RISING, handler=trainModeButton)


while(True):
    if(STATE_TRAIN):
        motor.stop()
    if(STATE_PLAY):
        # run KNN to get a motor direction for the
        # current sensor reading based on training data
        motor_dir = nearest_neighbor(h3lis331dl.read_accl_g()['x'], h3lis331dl.read_accl_g()['y'])
        # convert the KNN output tag to motor speeds
        if(motor_dir==0):
            motor.stop()
        elif(motor_dir==1):
            motor.setSpeed(1,50)
        elif(motor_dir==-1):
            motor.setSpeed(0,50)



