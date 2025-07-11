import ssd1306  # Assuming you're using an SSD1306 display
from machine import I2C, Pin


class oled_display:
    def __init__(self, width=128, height=64):
        
        self.i2c = I2C(0, scl=Pin(2), sda=Pin(15))
        self.oled = ssd1306.SSD1306_I2C(width, height, self.i2c)

    def show_message(self, message):
        self.oled.fill(0)  # Clear the display
        # Split message into chunks of 15 characters
        line_length = 15
        lines = [message[i:i+line_length] for i in range(0, len(message), line_length)]
        
        # Display each line with 10 pixel vertical spacing
        for i, line in enumerate(lines):
            self.oled.text(line, 0, i*10)

        self.oled.show()  # Update the display
    def get_oled(self):
        return self.oled