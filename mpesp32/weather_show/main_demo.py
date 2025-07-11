from machine import Pin, I2C,I2S
import time
import os
import socket
import urequests

from oled import oled_display
from wifi import WifiManager



button = Pin(13, Pin.IN, Pin.PULL_UP)


oled_instance = oled_display()
wifi_manager = WifiManager('CyberSpace_2G', '13260958857')
wifi_manager.connect()
wifi_manager.get_status()

max_retries = 5
retry_count = 0
while retry_count < max_retries:
    if wifi_manager.is_connected():
        oled_instance.show_message("WiFi Connected")
        break
    else:
        oled_instance.show_message("Connecting to WiFi...")
        time.sleep(1)
        retry_count += 1





    









    












