import os
import socket
import tempfile
from dotenv import load_dotenv
from agents import Agent, Runner
from openai import OpenAI
import json
import asyncio
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os


# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_AGENT_ID = "agent-1"  # Replace with your actual agent ID
HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
PORT = int(os.getenv("BACKEND_PORT", 50007))
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}  # Add more extensions if needed

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_audio_to_agent(file_path):
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # First, transcribe the audio
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            prompt="Transcribe this audio file to text.",
            language="en",
            response_format="text",
        )
    # Now, send the transcript to the agent
    print(f"Transcription result: {transcript}")
    agent = Agent(name="Audio Transcription Agent", instructions="you are an agent responds to the user based on the transcription.")
    result = asyncio.run(run_agent(agent, transcript))
    print(f"Agent response: {result.final_output}")
    return result


async def run_agent(agent, input_text):
    result = await Runner.run(
        starting_agent=agent,
        input=input_text,
    )
    return result

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # try:
        #     result = send_audio_to_agent(file_path)
        #     return jsonify({
        #         'message': 'File uploaded successfully',
        #         'filename': filename,
        #         'agent_response': result.final_output
        #     }), 200
        # except Exception as e:
        #     return jsonify({'error': str(e)}), 500``
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)


