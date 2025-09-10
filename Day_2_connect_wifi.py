import urequests

#Example from https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html 
def wifi_connect():
    import network #imports network library to connect to wifi
    import secrets #imports lib that has ssid and pwd
    sta_if = network.WLAN(network.WLAN.IF_STA)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(secrets.SSID, secrets.PWD)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ipconfig('addr4'))
    
wifi_connect()
