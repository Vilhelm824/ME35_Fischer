import urequests
import secrets #imports lib that has ssid and pwd
#Example from https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html 
def wifi_connect():
    import network #imports network library to connect to wifi
    
    sta_if = network.WLAN(network.WLAN.IF_STA)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(secrets.SSID, secrets.PWD)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ipconfig('addr4'))
    
wifi_connect()


token = secrets.at_api_token #
url ="https://api.airtable.com/v0/appPEV50bLCHxnHUu/testtable"
headers = {'Authorization': 'Bearer ' + token}

response = urequests.get(url, headers=headers)

print(response.status_code)

if response.status_code == 200:
    data = response.json()
    print("Response data:", data)
    for rec in data["records"]:
        print(rec["fields"]["where"]) #'where' is the name of the column 
else:
    print(f"Error: {response.status_code}")
    print(response.text)
    

