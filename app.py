from flask import Flask, render_template, request, jsonify, send_file
import sounddevice as sd
import scipy.io.wavfile as wav
import requests
import time
import os

app = Flask(__name__)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API keys from the environment variables
API_USER_ID = os.getenv("USER_ID")
API_KEY = os.getenv("API_KEY")

# Record user's voice
def record_voice(filename="user_voice_sample.wav", duration=5, sample_rate=44100):
    print("Recording voice sample... Please speak.")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    wav.write(filename, sample_rate, recording)
    print("Recording completed and saved as", filename)
    return filename

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

@app.route('/record', methods=['POST'])
def record():
    duration = 5  # seconds
    filename = "user_voice_sample.wav"
    record_voice(filename, duration)
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
        "The keeper, a man named Elias, had long since passed, and the light had dimmed for the last "
        "time many years ago. But every evening, as the sun dipped below the horizon, a young girl "
        "named Lyla would walk to the lighthouse, sit on the rocks, and gaze at the ocean. "
        "One evening, as the sky turned violet, Lyla noticed something unusual—a soft, glowing light coming from the "
        "lighthouse window. Curious, she approached and found the door slightly ajar. Inside, the light flickered "
        "on its own, as if the lighthouse keeper had never left. Lyla stepped forward, and a voice, gentle as the wind, "
        "whispered from the shadows: “The light only shines when there is someone who believes.” Lyla, filled with wonder, "
        "smiled. She had always believed the lighthouse was magical. She made a promise to visit every night, to believe "
        "in the stories of the sea, and to keep the light shining. From then on, whenever she was near, the lighthouse would glow, "
        "guiding ships home, and lighting the path for those who still believed in the magic of the world."
    )

    # Generate TTS
    audio_content = generate_tts(story_text, voice_id)
    if not audio_content:
        return jsonify({"error": "TTS generation failed"}), 500

    # Save audio
    audio_filename = "story_audio.mp3"
    with open(audio_filename, "wb") as audio_file:
        audio_file.write(audio_content)

    # Delete the cloned voice
    delete_cloned_voice(voice_id)

    return send_file(audio_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


# import requests
# import sounddevice as sd
# import scipy.io.wavfile as wav
# import time
# from playsound import playsound

# # API Key and User Id
# API_USER_ID = 'Av5bwQg93sXBCNwd5xue3ICEBQg1'
# API_KEY = '6655db0bc6b64e31893e8f2f6142ccda'

# # Record the user's voice
# def record_voice(filename="user_voice_sample.wav", duration=5, sample_rate=44100):
#     print("Recording voice sample... Please speak.")
#     recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
#     sd.wait()  
#     wav.write(filename, sample_rate, recording)
#     print("Recording completed and saved as", filename)

# # Voice Cloning - Upload the audio sample
# def clone_voice(file_path, voice_name="user_cloned_voice"):
#     clone_url = 'https://api.play.ht/api/v2/cloned-voices/instant'
#     headers = {
#         'X-USER-ID': API_USER_ID,
#         'AUTHORIZATION': API_KEY,
#         'accept': 'application/json'
#     }
#     files = {'sample_file': (file_path, open(file_path, 'rb'), 'audio/wav')}
#     data = {
#         'voice_name': voice_name  
#     }
#     response = requests.post(clone_url, headers=headers, files=files, data=data)
#     if response.status_code == 201:
#         manifest_url = response.json().get('id')
#         print("Voice cloning initiated. Manifest URL:", manifest_url)
#         return manifest_url
#     else:
#         print("Failed to clone voice:", response.text)
#         return None

# # Retrieve the voice ID once cloning completes
# def retrieve_voice_id(manifest_url):
#     status_url = "https://api.play.ht/api/v2/cloned-voices"
#     headers = {
#         'X-USER-ID': API_USER_ID,
#         'AUTHORIZATION': API_KEY,
#         'accept': 'application/json'
#     }
#     data = {'manifest_url': manifest_url}
#     while True:
#         response = requests.get(status_url, headers=headers, params=data)
#         if response.status_code == 200:
#             json_response = response.json()
#             print(json_response[0])
#             if 'id' in json_response[0]:
#                 voice_id = json_response[0]['id']
#                 print("Voice cloning completed! Voice ID:", voice_id)
#                 return voice_id
#             print("Voice cloning in progress. Checking again in 5 seconds...")
#         else:
#             print("Error retrieving voice status:", response.text)
#             break
#         time.sleep(5)  
#     return None

# # Generate TTS using the cloned voice
# def generate_tts(text, voice_id):
#     tts_url = 'https://api.play.ht/api/v2/tts/stream'
#     headers = {
#         'X-USER-ID': API_USER_ID,
#         'AUTHORIZATION': API_KEY,
#         'accept': 'audio/mpeg',
#         'content-type': 'application/json'
#     }
#     data = {
#         'text': f'{text}',
#         'voice': f'{voice_id}'
#     }
#     response = requests.post(tts_url, headers=headers, json=data)
#     if response.status_code == 200:
#         print("TTS generation successful!")
#         return response.content
#     else:
#         print("Failed to generate TTS:", response.text)
#         return None

# # Delete the cloned voice
# def delete_cloned_voice(voice_id):
#     delete_url = f'https://api.play.ht/api/v2/cloned-voices/'
#     playload = {"voice_id":f'{voice_id}'}
#     headers = {
#         'X-USER-ID': API_USER_ID,
#         'AUTHORIZATION': API_KEY,
#         "accept": "application/json",
#         "content-type": "application/json"
#     }
#     response = requests.delete(delete_url, headers=headers, json=playload)
#     if response.status_code == 204:
#         print("Voice clone deleted successfully.")
#     else:
#         print("Failed to delete voice clone:", response.text)

# # Main function
# def main():
#     # Record the user's voice
#     filename = "user_voice_sample.wav"
#     record_voice(filename)

#     # Clone the voice
#     manifest_url = clone_voice(filename)
#     if manifest_url is None:
#         print("Voice cloning initiation failed")
#         return  

#     # Retrieve the cloned voice ID
#     voice_id = retrieve_voice_id(manifest_url)
#     if voice_id is None:
#         print("Voice ID retrieval failed")
#         return 

#     # Define the story text for TTS
#     story_text = "In a quiet town by the sea, there was an old lighthouse that no longer served its purpose. The keeper, a man named Elias, had long since passed, and the light had dimmed for the last time many years ago. But every evening, as the sun dipped below the horizon, a young girl named Lyla would walk to the lighthouse, sit on the rocks, and gaze at the ocean. One evening, as the sky turned violet, Lyla noticed something unusual—a soft, glowing light coming from the lighthouse window. Curious, she approached and found the door slightly ajar. Inside, the light flickered on its own, as if the lighthouse keeper had never left. Lyla stepped forward, and a voice, gentle as the wind, whispered from the shadows: “The light only shines when there is someone who believes.” Lyla, filled with wonder, smiled. She had always believed the lighthouse was magical. She made a promise to visit every night, to believe in the stories of the sea, and to keep the light shining. From then on, whenever she was near, the lighthouse would glow, guiding ships home, and lighting the path for those who still believed in the magic of the world."


#     # Generate TTS using the cloned voice
#     audio_content = generate_tts(story_text, voice_id)
#     if audio_content:
#         # Save the TTS audio to a file
#         audio_filename = "story_audio.mp3"
#         with open(audio_filename, "wb") as audio_file:
#             audio_file.write(audio_content)
#         print(f"Story audio saved as '{audio_filename}'")

#         # Play the story audio
#         playsound(audio_filename)

#         # Delete the cloned voice after playback
#         delete_cloned_voice(voice_id)

# if __name__ == "__main__":
#     main()

