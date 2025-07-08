import speech_recognition as sr
from pydub import AudioSegment
import sys

def test_audio_libraries():
    print("Testing audio processing libraries...")
    
    # Test speech_recognition
    try:
        recognizer = sr.Recognizer()
        print("✅ SpeechRecognition initialized successfully")
    except Exception as e:
        print(f"❌ SpeechRecognition error: {str(e)}")
        
    # Test pydub
    try:
        # Just test importing AudioSegment
        print("✅ pydub AudioSegment initialized successfully")
    except Exception as e:
        print(f"❌ pydub error: {str(e)}")
        
    print("\nNote: For full audio processing functionality, you may need:")
    print("1. FFmpeg (for audio file processing)")
    print("2. PyAudio (for microphone input)")
    
if __name__ == "__main__":
    test_audio_libraries()
