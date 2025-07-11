from machine import Pin, I2C,I2S,PWM, AudioFormat, AudioStream
import time
import os
import socket
import ssd1306  # Assuming you're using an SSD1306 display
import urequests

# Global variables for recording state
is_recording = False
audio_i2s = None
recording_filename = "/flash/recorded_audio.wav"
# Initialize button on Pin 13 with pull-up resistor
button = Pin(13, Pin.IN, Pin.PULL_UP)
audio_format = AudioFormat(16000, 1, 44100)
mic_pin = Pin(22,Pin.IN)


def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('CyberSpace_2G', '13260958857')

    # Wait for connection
    while not wlan.isconnected():
        time.sleep(1)

    print('network config:', wlan.ifconfig())

def show_message_on_oled(oled, message):
    oled.fill(0)  # Clear the display
    # Split message into chunks of 15 characters
    line_length = 15
    lines = [message[i:i+line_length] for i in range(0, len(message), line_length)]
    
    # Display each line with 10 pixel vertical spacing
    for i, line in enumerate(lines):
        oled.text(line, 0, i*10)
    
    oled.show()  # Update the display

def display_wifi_status(oled):
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        status = "Connected"
    else:
        status = "Not Connected"

    oled.fill(0)  # Clear the display
    oled.text("WiFi Status:", 0, 0)
    oled.text(status, 0, 10)
    oled.show()  # Update the display
    

def initialize_oled():
    # Initialize I2C
    i2c = I2C(0, scl=Pin(2), sda=Pin(15))  # Initialize I2C with clock pin 26 and data pin 25
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # Initialize the OLED display (adjust width and height as needed)
    return oled

def initialize_audio():
    global audio_i2s, recording_filename
    
    # Configure I2S pins
    sck_pin = Pin(35)  # Serial Clock
    ws_pin = Pin(32)   # Word Select
    sd_pin = Pin(34)   # Serial Data
    
    audio_i2s = I2S(
        0,
        sck=sck_pin,
        ws=ws_pin,
        sd=sd_pin,
        mode=I2S.RX,
        bits=16,  # 16 bits per sample
        format=I2S.LEFT_JUSTIFIED, 
        rate=16000,  # Sample rate of 16000 Hz
        ibuf=4096  # Input buffer size
    )


def send_audio_file_to_backend(filepath):
    try:
        show_message_on_oled(oled, "Sending to backend...")
        
        # Read the audio file
        with open(filepath, 'rb') as file:
            audio_data = file.read()
        
        # Prepare the multipart form data
        boundary = '---011000010111000001101001'
        header = b'--' + boundary.encode() + b'\r\n'
        header += b'Content-Disposition: form-data; name="file"; filename="recorded_audio.wav"\r\n'
        header += b'Content-Type: audio/wav\r\n\r\n'
        
        footer = b'\r\n--' + boundary.encode() + b'--\r\n'
        
        # Combine all parts
        body = header + audio_data + footer
        
        # Send POST request
        url = 'http://localhost:50007/upload'
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        
        response = urequests.post(url, data=body, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            show_message_on_oled(oled, "File sent successfully!")
            print("Server response:", result)
            return result
        else:
            show_message_on_oled(oled, f"Error: {response.status_code}")
            print("Error:", response.text)
            return None
            
    except Exception as e:
        show_message_on_oled(oled, f"Error: {str(e)}")
        print("Error:", str(e))
        return None
    finally:
        try:
            response.close()
        except:
            pass


    


connect_to_wifi()

oled = initialize_oled()

display_wifi_status(oled)






#======= USER CONFIGURATION =======
RECORD_TIME_IN_SECONDS = 5
SAMPLE_RATE_IN_HZ = 8000
#======= USER CONFIGURATION =======

WAV_SAMPLE_SIZE_IN_BITS = 16
WAV_SAMPLE_SIZE_IN_BYTES = WAV_SAMPLE_SIZE_IN_BITS // 8
MIC_SAMPLE_BUFFER_SIZE_IN_BYTES = 4096
SDCARD_SAMPLE_BUFFER_SIZE_IN_BYTES = MIC_SAMPLE_BUFFER_SIZE_IN_BYTES // 2 # why divide by 2? only using 16-bits of 32-bit samples
NUM_SAMPLE_BYTES_TO_WRITE = RECORD_TIME_IN_SECONDS * SAMPLE_RATE_IN_HZ * WAV_SAMPLE_SIZE_IN_BYTES
NUM_SAMPLES_IN_DMA_BUFFER = 256
NUM_CHANNELS = 1

# snip_16_mono():  snip 16-bit samples from a 32-bit mono sample stream
# assumption: I2S configuration for mono microphone.  e.g. I2S channelformat = ONLY_LEFT or ONLY_RIGHT
# example snip:  
#   samples_in[] =  [0x44, 0x55, 0xAB, 0x77, 0x99, 0xBB, 0x11, 0x22]             
#   samples_out[] = [0xAB, 0x77, 0x11, 0x22]
#   notes:
#       samples_in[] arranged in little endian format:  
#           0x77 is the most significant byte of the 32-bit sample
#           0x44 is the least significant byte of the 32-bit sample
#
# returns:  number of bytes snipped
def snip_16_mono(samples_in, samples_out):
    num_samples = len(samples_in) // 4
    for i in range(num_samples):
        samples_out[2*i] = samples_in[4*i + 2]
        samples_out[2*i + 1] = samples_in[4*i + 3]
            
    return num_samples * 2

def create_wav_header(sampleRate, bitsPerSample, num_channels, num_samples):
    datasize = num_samples * num_channels * bitsPerSample // 8
    o = bytes("RIFF",'ascii')                                                   # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                                   # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                                  # (4byte) File type
    o += bytes("fmt ",'ascii')                                                  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                              # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                               # (2byte) Format type (1 - PCM)
    o += (num_channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                      # (4byte)
    o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (num_channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                                   # (2byte)
    o += bytes("data",'ascii')                                                  # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                        # (4byte) Data size in bytes
    return o


# Initialize I2S microphone
bck_pin = Pin(35)
ws_pin = Pin(32)
sdin_pin = Pin(34)



audio_in = I2S(
    I2S.NUM0, 
    bck=bck_pin, ws=ws_pin, sdin=sdin_pin,
    standard=I2S.PHILIPS, 
    mode=I2S.MASTER_RX,
    dataformat=I2S.B32,
    channelformat=I2S.ONLY_LEFT,
    samplerate=SAMPLE_RATE_IN_HZ,
    dmacount=50,
    dmalen=NUM_SAMPLES_IN_DMA_BUFFER
)

wav = open('mic_left_channel_16bits.wav','wb')

# create header for WAV file and write to SD card
wav_header = create_wav_header(
    SAMPLE_RATE_IN_HZ, 
    WAV_SAMPLE_SIZE_IN_BITS, 
    NUM_CHANNELS, 
    SAMPLE_RATE_IN_HZ * RECORD_TIME_IN_SECONDS
)
num_bytes_written = wav.write(wav_header)

# allocate sample arrays
#   memoryview used to reduce heap allocation in while loop
mic_samples = bytearray(MIC_SAMPLE_BUFFER_SIZE_IN_BYTES)
mic_samples_mv = memoryview(mic_samples)
wav_samples = bytearray(SDCARD_SAMPLE_BUFFER_SIZE_IN_BYTES)
wav_samples_mv = memoryview(wav_samples)

num_sample_bytes_written_to_wav = 0

def start():
    show_message_on_oled(oled,'Starting')
    # read 32-bit samples from I2S microphone, snip upper 16-bits, write snipped samples to WAV file
    while num_sample_bytes_written_to_wav < NUM_SAMPLE_BYTES_TO_WRITE:
        try:
            # try to read a block of samples from the I2S microphone
            # readinto() method returns 0 if no DMA buffer is full
            num_bytes_read_from_mic = audio_in.readinto(mic_samples_mv, timeout=0)
            if num_bytes_read_from_mic > 0:
                # snip upper 16-bits from each 32-bit microphone sample
                num_bytes_snipped = snip_16_mono(mic_samples_mv[:num_bytes_read_from_mic], wav_samples_mv)
                num_bytes_to_write = min(num_bytes_snipped, NUM_SAMPLE_BYTES_TO_WRITE - num_sample_bytes_written_to_wav)
                # write samples to WAV file
                num_bytes_written = wav.write(wav_samples_mv[:num_bytes_to_write])
                num_sample_bytes_written_to_wav += num_bytes_written
        except (KeyboardInterrupt, Exception) as e:
            show_message_on_oled(oled, 'caught exception {} {}'.format(type(e).__name__, e))
            break

    wav.close()
    audio_in.deinit()
    print('Done')
    print('%d sample bytes written to WAV file' % num_sample_bytes_written_to_wav)
    #send_audio_file_to_backend('mic_left_channel_16bits.wav')
    

# Set up interrupt handler for button press
def on_btn_pressed(pin):
    global is_recording
    _ = pin  # Access pin to avoid unused variable warning

    show_message_on_oled(oled, "Starting recording...")
    is_recording = True
    start()
    is_recording = False
    show_message_on_oled(oled, "Recording finished.")
    
    
button.irq(trigger=Pin.IRQ_FALLING, handler=on_btn_pressed)




