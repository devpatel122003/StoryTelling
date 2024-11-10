from flask import Flask, render_template, jsonify, request, Response
import scipy.io.wavfile as wav
import requests
import time
import os
import logging
from dotenv import load_dotenv
from pydub import AudioSegment

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

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    # Ensure the uploads directory exists
    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    audio_file = request.files['audio_file']
    filename = audio_file.filename
    audio_file.save(os.path.join(upload_folder, filename))  # Save audio to 'uploads' folder
    return jsonify({"filename": filename})

@app.route('/generate_story', methods=['POST'])
def generate_story():
    genre = request.json.get('genre', 'fantasy')  # Default to fantasy if no genre is provided
    
    # Assume the answers are saved in the 'uploads' directory
    answers = [
        "uploads/answer_1.wav",
        "uploads/answer_2.wav",
        "uploads/answer_3.wav",
        "uploads/answer_4.wav"
    ]
    
    # Combine the audio files into one
    combined_audio = AudioSegment.empty()
    
    # Loop through the audio files and combine them
    for answer in answers:
        audio = AudioSegment.from_file(answer)
        combined_audio += audio

    # Export the combined audio to a temporary file
    combined_audio.export("combined_audio.wav", format="wav")
    
    # Clone the voice using the combined audio file
    manifest_url = clone_voice("combined_audio.wav")  # Use the combined audio file
    if not manifest_url:
        return jsonify({"error": "Voice cloning initiation failed"}), 500

    # Retrieve the cloned voice ID
    voice_id = retrieve_voice_id(manifest_url)
    if not voice_id:
        return jsonify({"error": "Voice ID retrieval failed"}), 500

    # Generate story based on genre
    story_text = generate_story_text(genre)

    audio_content = generate_tts(story_text, voice_id)
    if not audio_content:
        return jsonify({"error": "TTS generation failed"}), 500

    # Delete the cloned voice after generating the story
    delete_cloned_voice(voice_id)

    # Send audio content directly to client
    return Response(audio_content, mimetype="audio/mpeg")

def generate_story_text(genre):
    # This is a placeholder function. In a real application, you would use a more sophisticated
    # method to generate a story based on the genre and the user's answers.
    stories = {
        "fantasy": "In a magical realm, a brave hero embarked on an epic quest...",
        "scifi": "In the distant future, humanity faced its greatest challenge yet...",
        "mystery": "The detective arrived at the scene, knowing this case would be unlike any other...",
        "romance": "Their eyes met across the crowded room, and in that moment, everything changed..."
    }
    return stories.get(genre, "Once upon a time, in a land far, far away...")

if __name__ == '__main__':
    app.run(debug=True)
