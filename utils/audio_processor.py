# utils/audio_processor.py
import requests
import streamlit as st
import tempfile
import os
from typing import Optional, Tuple, List, Dict, Any
import logging
try:
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    import speech_recognition as sr
    import numpy as np
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False
    AudioSegment = None
    split_on_silence = None
    sr = None

logger = logging.getLogger(__name__)

class AnimalSoundProcessor:
    """
    Process animal sound recordings to remove human speech and keep pure animal sounds
    """
    
    def __init__(self):
        if not AUDIO_PROCESSING_AVAILABLE:
            st.warning("Audio processing libraries not installed. Please install: pip install pydub SpeechRecognition")
            self.recognizer = None
        else:
            self.recognizer = sr.Recognizer()
        
    def process_audio_remove_speech(self, audio_url: str, animal_name: str) -> Optional[str]:
        """
        Download audio, detect and remove human speech, keep animal sounds
        
        Args:
            audio_url: URL of the audio file
            animal_name: Name of the animal for context
            
        Returns:
            URL or file path of processed audio with speech removed
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            logger.warning("Audio processing not available - returning original URL")
            return audio_url
            
        try:
            # Download audio file
            temp_dir = tempfile.mkdtemp()
            original_file = os.path.join(temp_dir, "original.mp3")
            processed_file = os.path.join(temp_dir, "processed.mp3")
            
            # Download the audio
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()
            
            with open(original_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Load audio with pydub
            audio = AudioSegment.from_file(original_file)
            
            # Convert to WAV for speech recognition
            wav_file = os.path.join(temp_dir, "temp.wav")
            audio.export(wav_file, format="wav")
            
            # Process audio to remove speech
            cleaned_audio = self._remove_speech_segments(wav_file, audio, animal_name)
            
            if cleaned_audio and len(cleaned_audio) > 1000:  # At least 1 second
                # Export cleaned audio
                cleaned_audio.export(processed_file, format="mp3")
                return processed_file
            else:
                logger.warning(f"Processed audio too short for {animal_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing audio for {animal_name}: {e}")
            return None
    
    def _remove_speech_segments(self, wav_file: str, audio, animal_name: str):
        """
        Identify and remove segments containing human speech
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            return audio
        try:
            # Split audio on silence to get segments
            segments = split_on_silence(
                audio,
                min_silence_len=500,  # 0.5 seconds of silence
                silence_thresh=audio.dBFS - 14,
                keep_silence=200  # Keep 0.2 seconds of silence
            )
            
            cleaned_segments = []
            
            for i, segment in enumerate(segments):
                # Export segment to temporary WAV for speech recognition
                temp_segment_file = f"temp_segment_{i}.wav"
                segment.export(temp_segment_file, format="wav")
                
                # Check if segment contains human speech
                contains_speech = self._detect_human_speech(temp_segment_file, animal_name)
                
                if not contains_speech:
                    cleaned_segments.append(segment)
                else:
                    logger.info(f"Removed speech segment {i} for {animal_name}")
                
                # Clean up temporary file
                try:
                    os.remove(temp_segment_file)
                except:
                    pass
            
            # Combine cleaned segments
            if cleaned_segments:
                result = AudioSegment.empty()
                for segment in cleaned_segments:
                    result += segment
                    # Add small silence between segments
                    result += AudioSegment.silent(duration=100)
                
                return result
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error removing speech segments: {e}")
            return audio  # Return original if processing fails
    
    def _detect_human_speech(self, audio_file: str, animal_name: str) -> bool:
        """
        Detect if an audio segment contains human speech
        """
        try:
            with sr.AudioFile(audio_file) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            # Try to recognize speech
            try:
                text = self.recognizer.recognize_google(audio_data, language='en-US')
                text_lower = text.lower()
                
                # Common words/phrases that indicate human narration
                human_indicators = [
                    'this is', 'here we have', 'you can hear', 'listen to', 
                    'recorded', 'sound of', 'call of', 'song of',
                    'male', 'female', 'adult', 'juvenile',
                    'morning', 'evening', 'dawn', 'dusk',
                    'location', 'recorded at', 'captured',
                    'macaulay library', 'cornell', 'ornithology',
                    'bird', 'animal', 'species', 'identification'
                ]
                
                # Check if text contains human speech indicators
                for indicator in human_indicators:
                    if indicator in text_lower:
                        logger.info(f"Detected human speech: '{text}' for {animal_name}")
                        return True
                
                # If we can recognize clear words, it's likely human speech
                if len(text.split()) >= 2:
                    logger.info(f"Detected speech (multiple words): '{text}' for {animal_name}")
                    return True
                    
                return False
                
            except sr.UnknownValueError:
                # No speech recognized - likely animal sound
                return False
            except sr.RequestError:
                # API error - assume it's not speech
                return False
                
        except Exception as e:
            logger.error(f"Error in speech detection: {e}")
            return False  # If unsure, keep the segment
    
    def analyze_audio_content(self, audio_url: str, animal_name: str) -> Dict[str, Any]:
        """
        Analyze audio content to determine speech vs animal sound ratio
        """
        try:
            temp_dir = tempfile.mkdtemp()
            audio_file = os.path.join(temp_dir, "analyze.mp3")
            
            # Download audio
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()
            
            with open(audio_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Load and analyze
            audio = AudioSegment.from_file(audio_file)
            duration = len(audio) / 1000.0  # Duration in seconds
            
            # Split into segments
            segments = split_on_silence(
                audio,
                min_silence_len=500,
                silence_thresh=audio.dBFS - 14,
                keep_silence=200
            )
            
            speech_duration = 0
            animal_duration = 0
            
            for segment in segments:
                segment_duration = len(segment) / 1000.0
                
                # Export segment for analysis
                temp_segment = os.path.join(temp_dir, "temp_analyze.wav")
                segment.export(temp_segment, format="wav")
                
                if self._detect_human_speech(temp_segment, animal_name):
                    speech_duration += segment_duration
                else:
                    animal_duration += segment_duration
                
                try:
                    os.remove(temp_segment)
                except:
                    pass
            
            # Calculate ratios
            total_analyzed = speech_duration + animal_duration
            speech_ratio = speech_duration / total_analyzed if total_analyzed > 0 else 0
            animal_ratio = animal_duration / total_analyzed if total_analyzed > 0 else 0
            
            return {
                "total_duration": duration,
                "speech_duration": speech_duration,
                "animal_duration": animal_duration,
                "speech_ratio": speech_ratio,
                "animal_ratio": animal_ratio,
                "quality_score": animal_ratio * 100,  # Higher score for more animal sounds
                "recommended": animal_ratio > 0.7  # Recommend if >70% animal sounds
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio content: {e}")
            return {
                "total_duration": 0,
                "speech_duration": 0,
                "animal_duration": 0,
                "speech_ratio": 1.0,
                "animal_ratio": 0.0,
                "quality_score": 0,
                "recommended": False
            }

# Global instance
audio_processor = AnimalSoundProcessor()
