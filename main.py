from audio_recorder import AudioRecorder
import whisper
import time
from tts_handler import TTSHandler
from gpt_handler import GPTHandler
from config import SAMPLE_RATE, CHANNELS, ELEVEN_LABS_VOICE_ID
import sys

audio_recorder = AudioRecorder(SAMPLE_RATE, CHANNELS)

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
    round_count = 1
    
    # Get debate context
    motion = input("Enter the debate motion: ")
    position = input("Enter your position (for/against): ").lower()
    while position not in ['for', 'against']:
        position = input("Please enter either 'for' or 'against': ").lower()
    
    # Get max rounds from user
    try:
        max_rounds = int(input("Enter number of rounds: "))
    except ValueError:
        max_rounds = 3  # Default to 3 rounds if invalid input
        print(f"Invalid input. Using default of {max_rounds} rounds.")

    # Set up the debate context
    gpt.set_debate_context(position, motion)

    # If position is 'for', automatically present opening arguments
    if position == 'for':
        print("\nPresenting opening arguments...")
        opening_args = gpt.generate_response(
            None,
            round_number=round_count
        )
        print("\nOpening Arguments:", opening_args)
        audio_file = tts.text_to_speech(opening_args, ELEVEN_LABS_VOICE_ID)
        tts.play_audio(audio_file)
        tts.cleanup_audio(audio_file)
        round_count += 1

    while round_count <= max_rounds:
        try:
            choice = input("Press Enter to start recording (or type 'exit' to quit): ")
            if choice.lower() == "exit":
                break

            # Record and transcribe user input
            wav_filename = audio_recorder.record_to_file()
             
            print("Transcribing audio...")
            transcription = transcribe_audio(wav_filename)
            print("\nYou said:", transcription)

            # Wait for user confirmation before rebuttal
            wait_for_user_confirmation()

            # Generate and speak response
            if round_count == max_rounds:
                print("\nGenerating closing statement...")
                closing_statement = gpt.generate_response(
                    transcription,
                    round_number=round_count,
                    is_closing=True
                )
                print("\nClosing Statement:", closing_statement)
                audio_file = tts.text_to_speech(closing_statement, ELEVEN_LABS_VOICE_ID)
                tts.play_audio(audio_file)
                tts.cleanup_audio(audio_file)
                tts.cleanup_audio(wav_filename)
                break  # End the debate after the closing statement
            else:
                rebuttal = gpt.generate_response(
                    transcription,
                    round_number=round_count
                )
                print(f"\nRound {round_count} Rebuttal:", rebuttal)
                audio_file = tts.text_to_speech(rebuttal, ELEVEN_LABS_VOICE_ID)
                tts.play_audio(audio_file)

                # Cleanup
                tts.cleanup_audio(wav_filename)
                tts.cleanup_audio(audio_file)
                round_count += 1
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Check audio devices at startup
    try:
        devices = audio_recorder.list_audio_devices()
        if not any(device['max_input_channels'] > 0 for device in devices):
            print("Error: No audio input devices found!")
            exit(1)
    except Exception as e:
        print(f"Error checking audio devices: {str(e)}")
        exit(1)

    debate_loop()
