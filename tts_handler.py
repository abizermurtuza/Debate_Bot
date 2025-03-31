import pyttsx3
from gtts import gTTS
import os
import wave
import tempfile
import pygame
import time
import logging
import threading
from pydub import AudioSegment
from eleven_labs import ElevenLabsHandler
from typing import Dict, List

class TTSError(Exception):
    """Custom exception for TTS service failures"""
    pass

class TTSHandler:
    def __init__(self):
        self.services = {
            'elevenlabs': {'available': False, 'handler': None, 'max_chars': 2500},
            'pyttsx3': {'available': False, 'handler': None, 'max_chars': 5000},
            'gtts': {'available': True, 'handler': None, 'max_chars': 5000}
        }
        self.file_locks: Dict[str, threading.Lock] = {}
        self.retry_count = 3
        self._initialize_services()
        self._initialize_audio()
        self.temp_files: List[str] = []

    def _initialize_services(self):
        """Initialize TTS services with proper error handling"""
        try:
            self.services['elevenlabs']['handler'] = ElevenLabsHandler()
            self.services['elevenlabs']['available'] = True
        except Exception as e:
            logging.warning(f"ElevenLabs initialization failed: {e}")

        try:
            self.services['pyttsx3']['handler'] = pyttsx3.init()
            self.services['pyttsx3']['available'] = True
        except Exception as e:
            logging.warning(f"pyttsx3 initialization failed: {e}")

    def _initialize_audio(self):
        """Initialize audio playback system"""
        try:
            pygame.mixer.init()
        except Exception as e:
            logging.error(f"Failed to initialize audio system: {e}")
            raise TTSError("Audio system initialization failed")

    def _chunk_text(self, text: str, max_chars: int) -> List[str]:
        """Split text into chunks that respect sentence boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        sentences = text.split('. ')
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_chars:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _get_temp_file(self, suffix: str) -> str:
        """Create and track temporary files."""
        temp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        self.temp_files.append(temp.name)
        return temp.name

    def _combine_audio_files(self, audio_files: List[str]) -> str:
        """Combine multiple audio files into a single file."""
        combined_audio = AudioSegment.empty()
        for audio_file in audio_files:
            combined_audio += AudioSegment.from_file(audio_file)
        combined_file = self._get_temp_file('.wav')
        combined_audio.export(combined_file, format='wav')
        return combined_file

    def text_to_speech(self, text, voice_id, fallback_order=['elevenlabs', 'pyttsx3', 'gtts']):
        """Convert text to speech using available services with fallback"""
        errors = []
        
        for service in fallback_order:
            if not self.services[service]['available']:
                continue
                
            try:
                # Split text into manageable chunks
                chunks = self._chunk_text(text, self.services[service]['max_chars'])
                audio_files = []

                for chunk in chunks:
                    for attempt in range(self.retry_count):
                        try:
                            if service == 'elevenlabs':
                                audio_files.append(self._eleven_labs_tts(chunk, voice_id))
                            elif service == 'pyttsx3':
                                audio_files.append(self._pyttsx3_tts(chunk))
                            elif service == 'gtts':
                                audio_files.append(self._gtts_tts(chunk))
                            break
                        except Exception as e:
                            if attempt == self.retry_count - 1:
                                raise e
                            time.sleep(1)

                return self._combine_audio_files(audio_files) if len(audio_files) > 1 else audio_files[0]
            except Exception as e:
                errors.append(f"{service}: {str(e)}")
                continue

        error_msg = "All TTS services failed: " + "; ".join(errors)
        logging.error(error_msg)
        raise TTSError(error_msg)

    def _eleven_labs_tts(self, text, voice_id):
        return self.services['elevenlabs']['handler'].text_to_speech(text, voice_id)

    def _pyttsx3_tts(self, text):
        wav_file = self._get_temp_file('.wav')
        self.services['pyttsx3']['handler'].save_to_file(text, wav_file)
        self.services['pyttsx3']['handler'].runAndWait()
        return wav_file

    def _gtts_tts(self, text):
        mp3_file = self._get_temp_file('.mp3')
        tts = gTTS(text=text, lang='en')
        tts.save(mp3_file)
        # Convert MP3 to WAV for better compatibility
        return self._convert_to_wav(mp3_file)

    def _convert_to_wav(self, mp3_file):
        """Convert MP3 to WAV format for better playback compatibility"""
        try:
            wav_file = mp3_file.replace('.mp3', '.wav')
            audio = AudioSegment.from_mp3(mp3_file)
            audio.export(wav_file, format='wav')
            os.remove(mp3_file)  # Clean up the MP3 file
            return wav_file
        except Exception as e:
            raise TTSError(f"Audio conversion failed: {e}")

    def play_audio(self, audio_file):
        if not os.path.exists(audio_file):
            raise TTSError(f"Audio file not found: {audio_file}")

        try:
            self._validate_audio_file(audio_file)
        except Exception as e:
            raise TTSError(f"Invalid audio file: {e}")

        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        try:
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            logging.error(f"Playback error: {e}")
        finally:
            pygame.mixer.music.unload()

    def _validate_audio_file(self, audio_file):
        """Validate audio file before playback"""
        if audio_file.endswith('.wav'):
            with wave.open(audio_file, 'rb') as wav:
                if wav.getnchannels() == 0 or wav.getsampwidth() == 0:
                    raise TTSError("Invalid WAV file format")

    def cleanup_audio(self, audio_file):
        from temp_file_manager import temp_file_manager
        temp_file_manager.remove_file(audio_file)
