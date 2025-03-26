import sounddevice as sd
import soundfile as sf
import numpy as np
import time

def test_audio_devices():
    """Test and display all audio devices."""
    print("\nTesting audio devices...")
    
    try:
        devices = sd.query_devices()
        print("\nAll audio devices:")
        for i, device in enumerate(devices):
            print(f"\nDevice {i}: {device['name']}")
            print(f"Input channels: {device['max_input_channels']}")
            print(f"Output channels: {device['max_output_channels']}")
            print(f"Default samplerate: {device['default_samplerate']}")
    except Exception as e:
        print(f"Error querying devices: {e}")
        return False
    
    return True

def test_recording(duration=3, fs=16000, channels=1):
    """Test audio recording with the default input device."""
    print("\nTesting audio recording...")
    
    try:
        # Get default input device info
        device_info = sd.query_devices(kind='input')
        print(f"\nUsing input device: {device_info['name']}")
        
        print(f"Recording {duration} second test...")
        recording = sd.rec(int(duration * fs),
                         samplerate=fs,
                         channels=channels,
                         dtype='float32',
                         blocking=True)
        
        # Save test recording
        test_file = "test_recording.wav"
        sf.write(test_file, recording, fs)
        print(f"\nTest recording saved to {test_file}")
        
        return True
    except Exception as e:
        print(f"Recording test failed: {e}")
        return False

if __name__ == "__main__":
    print("Audio System Test")
    print("================")
    
    devices_ok = test_audio_devices()
    if devices_ok:
        recording_ok = test_recording()
        if recording_ok:
            print("\nAll tests completed successfully!")
        else:
            print("\nRecording test failed!")
    else:
        print("\nDevice detection failed!")
