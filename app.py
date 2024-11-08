from flask import Flask, render_template, jsonify, request, send_file, Response
import scipy.io.wavfile as wav
import requests
import time
import os
import logging
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_USER_ID = os.getenv("USER_ID")
API_KEY = os.getenv("API_KEY")

# Clone voice
def clone_voice(file_path, voice_name="user_cloned_voice"):
    clone_url = 'https://api.play.ht/api/v2/cloned-voices/instant'
    headers = {
        'X-USER-ID': API_USER_ID,
        'AUTHORIZATION': API_KEY,
        'accept': 'application/json'
    }
    files = {'sample_file': (file_path, open(file_path, 'rb'), 'audio/wav')}
    data = {'voice_name': voice_name}
    response = requests.post(clone_url, headers=headers, files=files, data=data)
    if response.status_code == 201:
        manifest_url = response.json().get('id')
        return manifest_url
    else:
        return None

# Retrieve the voice ID once cloning completes
def retrieve_voice_id(manifest_url):
    status_url = "https://api.play.ht/api/v2/cloned-voices"
    headers = {
        'X-USER-ID': API_USER_ID,
        'AUTHORIZATION': API_KEY,
        'accept': 'application/json'
    }
    data = {'manifest_url': manifest_url}
    while True:
        response = requests.get(status_url, headers=headers, params=data)
        if response.status_code == 200:
            json_response = response.json()
            if 'id' in json_response[0]:
                return json_response[0]['id']
        time.sleep(5)

# Generate TTS using the cloned voice
def generate_tts(text, voice_id):
    tts_url = 'https://api.play.ht/api/v2/tts/stream'
    headers = {
        'X-USER-ID': API_USER_ID,
        'AUTHORIZATION': API_KEY,
        'accept': 'audio/mpeg',
        'content-type': 'application/json'
    }
    data = {'text': text, 'voice': voice_id}
    response = requests.post(tts_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.content
    else:
        return None

# Delete the cloned voice
def delete_cloned_voice(voice_id):
    delete_url = f'https://api.play.ht/api/v2/cloned-voices/'
    headers = {
        'X-USER-ID': API_USER_ID,
        'AUTHORIZATION': API_KEY,
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.delete(delete_url, headers=headers, json={"voice_id": voice_id})
    return response.status_code == 204

@app.route('/')
def index():
    return render_template('index.html')

# Route to upload audio file from client-side recording
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    audio_file = request.files['audio_file']
    filename = "user_voice_sample.wav"
    audio_file.save(filename)
    return jsonify({"filename": filename})

@app.route('/generate_story', methods=['POST'])
def generate_story():
    # Clone the voice
    manifest_url = clone_voice("user_voice_sample.wav")
    if not manifest_url:
        return jsonify({"error": "Voice cloning initiation failed"}), 500

    # Retrieve the cloned voice ID
    voice_id = retrieve_voice_id(manifest_url)
    if not voice_id:
        return jsonify({"error": "Voice ID retrieval failed"}), 500

    # Story text
    story_text = (
        "In a quiet town by the sea, there was an old lighthouse that no longer served its purpose. "
    )

    # Generate TTS
    audio_content = generate_tts(story_text, voice_id)
    if not audio_content:
        return jsonify({"error": "TTS generation failed"}), 500

    # Delete the cloned voice after generating the story
    delete_cloned_voice(voice_id)

    # Send audio content directly to client
    return Response(audio_content, mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(debug=True)
