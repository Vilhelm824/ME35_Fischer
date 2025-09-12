from machine import Pin
import time

#Method 1 - using loop
'''
ButtonA = Pin(35, Pin.IN)
ButtonA.value()

while True:
    if not ButtonA.value():

        #startTime = time.ticks_ms() #gives time in ms
        while not ButtonA.value(): #stay in the loop while the button is pressed
            pass # do nothing
        endTime = time.ticks_ms()
        
        print("Elapsed time (in ms): ", endTime - startTime)
            

'''
'''
#method 2 - using interrupt

starttime = 0
endtime = 0


ButtonB = Pin(34, Pin.IN)

def callback(p):
    global starttime
    global endtime

    
    entered_time = time.ticks_ms() # time this function was called

    if(ButtonB.value() == 0):
        print("setting start time")
        starttime = entered_time
    else:
        print("setting end time")
        endtime = time.ticks_ms()
        print("pressed time", endtime - starttime)

     
ButtonB.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler= callback)


'''
#method 2 - using interrupt (with debounce)
'''       
starttime = 0
endtime = 0
last_entered_time = 0
debounce_filter = 50

ButtonB = Pin(34, Pin.IN)

def callback(p):
    global starttime
    global endtime
    global last_entered_time
    
    entered_time = time.ticks_ms() # time this function was called
    if((time.ticks_ms() - last_entered_time) < debounce_filter):
        return
    last_entered_time = entered_time
    if(ButtonB.value() == 0):
        print("setting start time")
        starttime = last_entered_time
    else:
        print("setting end time")
        endtime = time.ticks_ms()
        print("pressed time", endtime - starttime)

     
ButtonB.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler= callback)

'''


    
