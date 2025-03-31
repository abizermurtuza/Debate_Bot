import sounddevice as sd
import soundfile as sf
import whisper
import time
import numpy as np
import tempfile
from tts_handler import TTSHandler
from gpt_handler import GPTHandler
from config import DEFAULT_RECORDING_DURATION, SAMPLE_RATE, CHANNELS, ELEVEN_LABS_VOICE_ID

def list_audio_devices():
    """List all available audio input devices."""
    print("\nAvailable audio input devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"{i}: {device['name']}")
    return devices

def record_audio(duration=DEFAULT_RECORDING_DURATION, fs=SAMPLE_RATE, channels=CHANNELS):
    try:
        # Get default input device
        device_info = sd.query_devices(kind='input')
        if device_info is None:
            raise RuntimeError("No input device found!")

        print(f"Using input device: {device_info['name']}")
        print(f"Recording for {duration} seconds...")
        
        audio = sd.rec(int(duration * fs), 
                      samplerate=fs, 
                      channels=channels, 
                      dtype='float32',
                      blocking=True)
    except Exception as e:
        raise RuntimeError(f"Recording failed: {str(e)}")
    return audio, fs

def save_to_wav(audio, fs, filename):
    sf.write(filename, audio, fs)

def transcribe_audio(filename, model_name="base"):
    model = whisper.load_model(model_name)
    result = model.transcribe(filename)
    return result["text"]

def wait_for_user_confirmation():
    """Prompt user to continue and optionally add delay."""
    while True:
        response = input("\nPress Enter to hear the rebuttal, or enter a number of seconds to wait: ").strip()
        if response == "":
            return
        try:
            delay = float(response)
            print(f"\nWaiting for {delay} seconds...")
            time.sleep(delay)
            return
        except ValueError:
            print("Please enter a valid number or press Enter to continue immediately.")

def debate_loop():
    gpt = GPTHandler()
    tts = TTSHandler()
    first_round = True

    # Get debate context
    motion = input("Enter the debate motion: ")
    position = input("Enter your position (for/against): ").lower()
    while position not in ['for', 'against']:
        position = input("Please enter either 'for' or 'against': ").lower()

    # Set up the debate context
    gpt.set_debate_context(position, motion)

    # If position is 'for', automatically present opening arguments
    if position == 'for':
        print("\nPresenting opening arguments...")
        opening_args = gpt.generate_response(
            None,
            is_first_round=True
        )
        print("\nOpening Arguments:", opening_args)
        audio_file = tts.text_to_speech(opening_args, ELEVEN_LABS_VOICE_ID)
        tts.play_audio(audio_file)
        tts.cleanup_audio(audio_file)
        first_round = False

    while True:
        try:
            duration = int(input("Enter recording duration (or 0 to exit): "))
            if duration == 0:
                break

            # Record and transcribe user input
            audio, fs = record_audio(duration)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_filename = tmp.name
            save_to_wav(audio, fs, wav_filename)
            transcription = transcribe_audio(wav_filename)
            print("\nYou said:", transcription)

            # Wait for user confirmation before rebuttal
            wait_for_user_confirmation()

            # Generate and speak response
            rebuttal = gpt.generate_response(
                transcription,
                is_first_round=first_round
            )
            first_round = False
            print("\nRebuttal:", rebuttal)
            audio_file = tts.text_to_speech(rebuttal, ELEVEN_LABS_VOICE_ID)
            tts.play_audio(audio_file)

            # Cleanup
            tts.cleanup_audio(wav_filename)
            tts.cleanup_audio(audio_file)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Check audio devices at startup
    try:
        devices = list_audio_devices()
        if not any(device['max_input_channels'] > 0 for device in devices):
            print("Error: No audio input devices found!")
            exit(1)
    except Exception as e:
        print(f"Error checking audio devices: {str(e)}")
        exit(1)

    debate_loop()
