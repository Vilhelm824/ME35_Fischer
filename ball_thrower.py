import time
from encoder import Motor

# initialize motors
motorR = Motor(14, 27, 32,39)
motorL = Motor(12, 13, 32,39)
motorR.stop()
motorL.stop()

# initialize var for motor speed
launch_speed = 0;
tune_offset = 0;


# loops until a launch_speed is successfully set
while(launch_speed == 0):
    # get launch dist from user
    launch_dist = float(input("enter desired launch distance: "))
    
    if (launch_dist<2.0 or launch_dist>6.0):
        print("Out of distance range, try again")
    else:
        # find motor speed for input distance using equation
        launch_speed = int(3.7*launch_dist+18.3)


print(f"Launching at speed: {launch_speed}")
# launch the ball by running the motors for 3 sec
motorR.setSpeed(1, launch_speed+tune_offset)
motorL.setSpeed(0, launch_speed+tune_offset)
time.sleep(12)
motorR.stop()
motorL.stop()


