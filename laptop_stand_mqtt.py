import network
import time
from umqtt.simple import MQTTClient
import ssl
import secrets
import neopixel
import json
from machine import Pin
import servo

class MQTTDevice:
    def __init__(self):
        self.SSID = secrets.SSID
        self.PASSWORD = secrets.PWD


        self.entered_time = 0
        # MQTT settings
        self.MQTT_BROKER = secrets.mqtt_url 
        self.MQTT_PORT = 8883
        self.MQTT_USERNAME = secrets.mqtt_username 
        self.MQTT_PASSWORD = secrets.mqtt_password 
        self.CLIENT_ID = "houston"
        self.TOPIC_PUB = "/COM"
        
        # Servo intialize
        self.servo1 = servo.Servo(4)
        self.servoAngle = 90;
        self.servo1.write_angle(servoAngle)
        
    def move_servo(self, increment):
        print(increment)
        newAngle = self.servoAngle + increment
        if newAngle >= 0 and newAngle <= 180:
            self.servoAngle = newAngle
        elif newAngle < 0:
            self.servoAngle = 0
            print("can't turn further")
        elif newAngle > 180:
            self.servoAngle = 180
            print("can't turn further")

        self.servo1.write_angle(self.servoAngle)
        
       
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
                increment = int(json_str["angle"])
                self.move_servo(increment)

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
        time.sleep(0.5)
    except Exception as e:
        print(f"Checking message failed: {e}")
    

      
            
          

