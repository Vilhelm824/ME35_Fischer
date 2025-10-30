import network
import time
import servo
from umqtt.simple import MQTTClient
import ssl
import secrets
import neopixel
import json
from machine import Pin, PWM

class MQTTDevice:
    def __init__(self):
        self.SSID = secrets.SSID
        self.PASSWORD = secrets.PWD

        # Servo intialize
        self.servoL = servo.Servo(4)
        self.servoR = servo.Servo(19)
        # buzzer initialize
        self.buzzer = PWM(Pin(23))
        self.buzzer.duty(0)
        
        self.entered_time = 0
        # MQTT settings
        self.MQTT_BROKER = secrets.mqtt_url 
        self.MQTT_PORT = 8883
        self.MQTT_USERNAME = secrets.mqtt_username 
        self.MQTT_PASSWORD = secrets.mqtt_password 
        self.CLIENT_ID = "arms"
        self.TOPIC_PUB = "/COM"
        
    def tone(self, freq, duration):
        if freq == 0:  # rest
            self.buzzer.duty(0)
        else:
            self.buzzer.freq(freq)
            self.buzzer.duty(512)
        time.sleep(duration)
        self.buzzer.duty(0)
        time.sleep(0.05)  # short pause between notes
    
    # "Dun dada dun!" victory sound
    def victory_sound(self):
        # "dun da-da DUN!"
        self.tone(659, 0.15)   # E5
        self.tone(784, 0.15)   # G5
        self.tone(880, 0.15)   # A5
        self.tone(988, 0.25)   # B5
        self.tone(784, 0.15)   # G5
        self.tone(988, 0.15)   # B5
        self.tone(1047, 0.4)
        
    def failure_sound(self):
        # Trying to match the linked sound effect
        self.tone(392, 0.3)   # G4 — initial note
        self.tone(349, 0.2)   # F4 — drop
        self.tone(330, 0.2)   # E4 — further drop
        self.tone(294, 0.3)   # D4 — longer
        self.tone(247, 0.3)   # B3 — slower descending “wah”
        self.tone(220, 1.3)   # A3 — final low hold for the sad finish

    
    def move_servo(self, angleL, angleR):
            self.servoL.write_angle(angleL)
            self.servoR.write_angle(angleR)
            print("moved: ", angleL, angleR)
        
    def make_sound(self, which_sound):
        if(which_sound=="happy"):
            self.victory_sound()
        if(which_sound=="sad"):
            self.failure_sound()
       
    def connect_wifi(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print("Connecting to WiFi...")
            self.wlan.connect(self.SSID, self.PASSWORD)
            timeout = 10
            while not self.wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
        if self.wlan.isconnected():
            print("WiFi Connected! IP:", self.wlan.ifconfig()[0])
            return True
        else:
            print("WiFi connection failed!")
            return False

    def publish(self, topic, msg):
        self.client.publish(topic, msg)
        print(f"Published message to topic '{topic}' : '{msg}'")
        
    def subscribe(self, topic):
        self.client.subscribe(topic)
        
    def sub_cb(self, topic, msg):
        json_str = json.loads(msg)
        print(f"Received message on topic '{topic.decode()}' : '{msg.decode()}'")
        try:
            if(json_str["type"]=="servo"):
                angleL = int(json_str["angleL"])
                angleR = int(json_str["angleR"])
                self.move_servo(angleL, angleR)
            elif(json_str["type"]=="button"):
                which_sound = json_str["sound"]
                self.make_sound(which_sound)
        except Exception as e:
            print(f"Error: {e}")

    def mqtt_connect(self):
        try:
            self.client = MQTTClient(
                client_id = self.CLIENT_ID,
                server = self.MQTT_BROKER,
                port = self.MQTT_PORT,
                user = self.MQTT_USERNAME,
                password = self.MQTT_PASSWORD,
                ssl = True,  # Enable SSL
                ssl_params = {'server_hostname': self.MQTT_BROKER}  # Important for certificate validation
            )
            self.client.set_callback(self.sub_cb)
            self.client.connect()
            
            print("MQTT Connected successfully!")
            return self.client
        except OSError as e:
            print(f"MQTT Connection failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


mqtt_obj = MQTTDevice()

if mqtt_obj.connect_wifi():
    client = mqtt_obj.mqtt_connect()
    mqtt_obj.subscribe("/COM")

while True:
    try:
        client.check_msg()
        time.sleep(1)
    except Exception as e:
        print(f"Checking message failed: {e}")
    

      