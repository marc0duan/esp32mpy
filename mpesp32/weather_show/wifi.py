import network
from oled import oled_display

class WifiManager:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.oled_instance = oled_display()

    def connect(self):
        if not self.wlan.isconnected():
            self.oled_instance.show_message(f"Connecting to {self.ssid}...")
            self.wlan.connect(self.ssid, self.password)
            while not self.wlan.isconnected():
                pass
        self.oled_instance.show_message('Connected:')
        self.oled_instance.show_message(str(self.wlan.ifconfig()))

    def is_connected(self):
        return self.wlan.isconnected()

    def disconnect(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.oled_instance.show_message("Disconnected from WiFi")

    def get_status(self):
        if self.wlan.isconnected():
            status = "Connected"
        else:
            status = "Not Connected"
        self.oled_instance.show_message(status)