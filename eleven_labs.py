import requests
import tempfile
import pygame
from config import ELEVEN_LABS_API_KEY

class ElevenLabsHandler:
    def __init__(self):
        self.api_key = ELEVEN_LABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        pygame.mixer.init()

    def text_to_speech(self, text, voice_id):
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(response.content)
                return tmp.name
        else:
            raise Exception(f"Error in text-to-speech: {response.text}")

    def play_audio(self, audio_file):
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
