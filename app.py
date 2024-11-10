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
    logger.info("Starting voice cloning for file: %s", file_path)
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
        logger.info("Voice cloning initiated successfully, manifest URL: %s", manifest_url)
        return manifest_url
    else:
        logger.error("Voice cloning failed with status code: %d, response: %s", response.status_code, response.text)
        return None

# Retrieve the voice ID once cloning completes
def retrieve_voice_id(manifest_url):
    logger.info("Retrieving voice ID for manifest URL: %s", manifest_url)
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
                voice_id = json_response[0]['id']
                logger.info("Voice ID retrieved successfully: %s", voice_id)
                return voice_id
        else:
            logger.warning("Voice ID retrieval failed with status code: %d", response.status_code)
        time.sleep(5)

# Generate TTS using the cloned voice
def generate_tts(text, voice_id):
    logger.info("Generating TTS for text using voice ID: %s", voice_id)
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
        logger.info("TTS generation successful")
        return response.content
    else:
        logger.error("TTS generation failed with status code: %d, response: %s", response.status_code, response.text)
        return None

# Delete the cloned voice
def delete_cloned_voice(voice_id):
    logger.info("Deleting cloned voice with ID: %s", voice_id)
    delete_url = f'https://api.play.ht/api/v2/cloned-voices/'
    headers = {
        'X-USER-ID': API_USER_ID,
        'AUTHORIZATION': API_KEY,
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.delete(delete_url, headers=headers, json={"voice_id": voice_id})
    if response.status_code == 204:
        logger.info("Cloned voice deleted successfully")
    else:
        logger.error("Failed to delete cloned voice with status code: %d, response: %s", response.status_code, response.text)
    return response.status_code == 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info("Uploads directory created")

    audio_file = request.files['audio_file']
    filename = audio_file.filename
    file_path = os.path.join(upload_folder, filename)
    audio_file.save(file_path)
    logger.info("Audio file uploaded and saved as: %s", file_path)
    return jsonify({"filename": filename})

@app.route('/generate_story', methods=['POST'])
def generate_story():
    genre = request.json.get('genre', 'fantasy')  # Default to fantasy if no genre is provided
    logger.info("Story generation initiated with genre: %s", genre)
    
    answers = ["uploads/answer_1.wav", "uploads/answer_2.wav", "uploads/answer_3.wav", "uploads/answer_4.wav"]
    combined_audio = AudioSegment.empty()
    
    for answer in answers:
        audio = AudioSegment.from_file(answer)
        combined_audio += audio
        os.remove(answer)  # Delete each answer file after merging
        logger.info("Answer file %s merged and deleted", answer)

    combined_path = "combined_audio.wav"
    combined_audio.export(combined_path, format="wav")
    logger.info("Combined audio saved as: %s", combined_path)
    
    manifest_url = clone_voice(combined_path)
    if not manifest_url:
        os.remove(combined_path)  # Cleanup combined file
        logger.error("Voice cloning initiation failed for combined audio")
        return jsonify({"error": "Voice cloning initiation failed"}), 500

    voice_id = retrieve_voice_id(manifest_url)
    if not voice_id:
        os.remove(combined_path)  # Cleanup combined file
        logger.error("Voice ID retrieval failed")
        return jsonify({"error": "Voice ID retrieval failed"}), 500

    story_text = generate_story_text(genre)
    audio_content = generate_tts(story_text, voice_id)
    if not audio_content:
        delete_cloned_voice(voice_id)
        os.remove(combined_path)  # Cleanup combined file
        logger.error("TTS generation failed")
        return jsonify({"error": "TTS generation failed"}), 500

    delete_cloned_voice(voice_id)
    os.remove(combined_path)
    logger.info("Generated story successfully and cleaned up temporary files")

    return Response(audio_content, mimetype="audio/mpeg")

def generate_story_text(genre):
    stories = {
        "fantasy": "In a magical realm, a brave hero embarked on an epic quest...",
        "scifi": "In the distant future, humanity faced its greatest challenge yet...",
        "mystery": "The detective arrived at the scene, knowing this case would be unlike any other...",
        "romance": "Their eyes met across the crowded room, and in that moment, everything changed..."
    }
    logger.info("Story text generated for genre: %s", genre)
    return stories.get(genre, "Once upon a time, in a land far, far away...")

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True)
