import network
import time
from umqtt.simple import MQTTClient
import ssl
import secrets
import neopixel
import json
from machine import Pin

class MQTTDevice:
    def __init__(self):
        self.SSID = secrets.SSID
        self.PASSWORD = secrets.PWD

        #Neopixel intialize
        self.np = neopixel.NeoPixel(Pin(15), 2)

        self.entered_time = 0
        # MQTT settings
        self.MQTT_BROKER = secrets.mqtt_url 
        self.MQTT_PORT = 8883
        self.MQTT_USERNAME = secrets.mqtt_username 
        self.MQTT_PASSWORD = secrets.mqtt_password 
        self.CLIENT_ID = "houston"
        self.TOPIC_PUB = "/COM"

        self.button1 = Pin(34, Pin.IN, Pin.PULL_UP)
        self.button1.irq(trigger = Pin.IRQ_RISING, handler = self.D34_pressed)
        self.button2 = Pin(35, Pin.IN, Pin.PULL_UP)
        self.button2.irq(trigger = Pin.IRQ_RISING, handler = self.D35_pressed)
   
    def D34_pressed(self, p):
        # debounce filter 
        now_time = time.ticks_ms()
        if(now_time - self.entered_time < 200):
            return
        self.entered_time = now_time
        
        json_str = json.dumps({"type":"button", "sound":"happy"})
        self.client.publish(self.TOPIC_PUB, json_str)
        print("D34 was pressed")
        
    def D35_pressed(self, p):
        # debounce filter 
        now_time = time.ticks_ms()
        if(now_time - self.entered_time < 200):
            return
        self.entered_time = now_time
        
        json_str = json.dumps({"type":"button", "sound":"sad"})
        self.client.publish(self.TOPIC_PUB, json_str)
        print("D35 was pressed")
        
    def move_servo(self, angleL, angleR):
        print(angleL, angleR)
        
    def make_sound(self, which_sound):
        print(which_sound)
       
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
                angleR = int(json_str["angleL"])
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
        angleL = input("what angle for left (0-180): ")
        angleR = input("what angle for right (0-180): ")
        json_str = json.dumps({"type":"servo", "angleL":angleL, "angleR":angleR})
        client.publish("/COM", json_str)

        time.sleep(1)
    except Exception as e:
        print(f"Checking message failed: {e}")
    

      
            
          

