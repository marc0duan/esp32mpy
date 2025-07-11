import urequests
from oled import oled_display

class utils:
    @staticmethod
    def send_audio_file_to_backend(oled,filepath):
        try:
            oled.show_message_on_oled( "Sending to backend...")
            
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
                oled.show_message_on_oled("File sent successfully!")
                print("Server response:", result)
                return result
            else:
                oled.show_message_on_oled(f"Error: {response.status_code}")
                print("Error:", response.text)
                return None
                
        except Exception as e:
            oled.show_message_on_oled(f"Error: {str(e)}")
            print("Error:", str(e))
            return None
        finally:
            try:
                response.close()
            except:
                pass