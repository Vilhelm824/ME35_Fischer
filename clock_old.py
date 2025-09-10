import machine, time

button = machine.Pin(34, machine.Pin.IN, machine.Pin.PULL_UP)

while(True):
    print(button.value())
    time.sleep_ms(500)
