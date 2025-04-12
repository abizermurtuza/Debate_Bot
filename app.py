from flask import Flask, render_template, request, jsonify, send_file
from audio_recorder import AudioRecorder
from tts_handler import TTSHandler
from gpt_handler import GPTHandler
import whisper
import tempfile
import os
from config import SAMPLE_RATE, CHANNELS, ELEVEN_LABS_VOICE_ID, MAX_ROUNDS

app = Flask(__name__)

audio_recorder = AudioRecorder(SAMPLE_RATE, CHANNELS)
gpt = GPTHandler()
round_count = 1
tts = TTSHandler()
whisper_model = whisper.load_model("small")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_debate_context', methods=['POST'])
def set_debate_context():
    motion = request.form['motion']
    position = request.form['position']
    gpt.set_debate_context(position, motion)
    
    if position == 'for':
        opening_arguments = gpt.generate_response(None, round_number=round_count)
        audio_file = tts.text_to_speech(opening_arguments, ELEVEN_LABS_VOICE_ID)
        return jsonify({'text': opening_arguments, 'audio': audio_file})
    
    return jsonify({'success': True})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_data = request.files['audio'].read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_audio:
        temporary_audio.write(audio_data)
        temporary_audio_path = temporary_audio.name

    result = whisper_model.transcribe(temporary_audio_path)
    os.unlink(temporary_audio_path)
    
    return jsonify({'transcription': result["text"]})

@app.route('/generate_response', methods=['POST'])
def generate_response():
    global round_count
    transcription = request.form['transcription']
    round_count += 1
    
    if round_count >= MAX_ROUNDS:
        closing_statement = gpt.generate_response(transcription, round_number=round_count, is_closing=True)
        audio_file = tts.text_to_speech(closing_statement, ELEVEN_LABS_VOICE_ID)
        return jsonify({'text': closing_statement, 'audio': audio_file, 'is_closing': True, 'round_count': round_count})
    else:
        rebuttal = gpt.generate_response(transcription, round_number=round_count)
        audio_file = tts.text_to_speech(rebuttal, ELEVEN_LABS_VOICE_ID)
        return jsonify({'text': rebuttal, 'audio': audio_file, 'is_closing': False, 'round_count': round_count})

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_file(filename, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True)
