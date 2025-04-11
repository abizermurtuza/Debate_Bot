import sounddevice as sounddevice
import soundfile as soundfile
import numpy as numpy
import queue
import threading
import tempfile

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels

    def list_audio_devices(self):
        """List all available audio input devices."""
        print("\nAvailable audio input devices:")
        devices = sounddevice.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"{i}: {device['name']}")
        return devices

    def record_audio(self, duration):
        try:
            device_info = sounddevice.query_devices(kind='input')
            if device_info is None:
                raise RuntimeError("No input device found!")

            print(f"Using input device: {device_info['name']}")
            print(f"Recording for {duration} seconds...")
            
            audio = sounddevice.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels, 
                          dtype='float32',
                          blocking=True)
        except Exception as e:
            raise RuntimeError(f"Recording failed: {str(e)}")
        return audio, self.sample_rate

    def continuous_recording(self):
        """Record audio continuously until user presses Enter to stop."""
        queue_instance = queue.Queue()
        recording = True
        audio_data = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            queue_instance.put(indata.copy())
        
        def input_thread_func():
            print("\nRecording... Press Enter to stop.")
            input()  # Wait for Enter key
            nonlocal recording
            recording = False
        
        input_thread = threading.Thread(target=input_thread_func)
        input_thread.daemon = True
        input_thread.start()
        
        with sounddevice.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback):
            while recording:
                try:
                    audio_data.append(queue_instance.get(timeout=0.5))
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    break
        
        if not audio_data:
            raise RuntimeError("No audio recorded")
        
        return numpy.concatenate(audio_data), self.sample_rate

    def save_to_wav(self, audio, fs, filename):
        soundfile.write(filename, audio, fs)

    def record_to_file(self, duration=None):
        if duration:
            audio, fs = self.record_audio(duration)
        else:
            audio, fs = self.continuous_recording()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_filename = tmp.name
        self.save_to_wav(audio, fs, wav_filename)
        return wav_filename
