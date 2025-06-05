import os
import json
from typing import Dict, List
import speech_recognition as sr
from pydub import AudioSegment
import numpy as np
from datetime import datetime
from ffmpeg_config import FFMPEG_EXECUTABLE  # Import FFmpeg configuration

# Configure FFmpeg path
AudioSegment.converter = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffprobe.exe"

class PanelistAnalyzer:
    def __init__(self):
        self.learning_data_dir = os.getenv("LEARNING_DATA_DIR", "/app/learning_data")
        self.raw_data_dir = os.path.join(self.learning_data_dir, "raw_data")
        self.processed_data_dir = os.path.join(self.learning_data_dir, "processed_data")
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Define personality traits to analyze
        self.personality_traits = {
            "formality": 0.0,  # 0-1 scale
            "enthusiasm": 0.0,  # 0-1 scale
            "analytical": 0.0,  # 0-1 scale
            "interruptiveness": 0.0,  # 0-1 scale
            "response_delay": 0.0,  # seconds
            "speech_rate": 0.0,  # words per minute
            "vocabulary_complexity": 0.0,  # 0-1 scale
            "emotional_intensity": 0.0,  # 0-1 scale
            "tactical_focus": 0.0,  # 0-1 scale
            "statistical_reference": 0.0,  # 0-1 scale
        }
        
        # Define conversation patterns to analyze
        self.conversation_patterns = {
            "interruption_probability": 0.0,  # 0-1 scale
            "interruption_delay": 0.0,  # seconds
            "agreement_frequency": 0.0,  # 0-1 scale
            "disagreement_frequency": 0.0,  # 0-1 scale
            "question_frequency": 0.0,  # 0-1 scale
            "tactical_analysis_frequency": 0.0,  # 0-1 scale
            "statistical_reference_frequency": 0.0,  # 0-1 scale
            "emotional_reaction_frequency": 0.0,  # 0-1 scale
        }
    
    def analyze_audio_file(self, audio_file: str, panelist_type: str) -> Dict:
        """Analyze an audio file of a panelist's speech"""
        # Load audio file
        audio = AudioSegment.from_file(audio_file)
        
        # Convert to WAV for speech recognition
        wav_file = os.path.join(self.raw_data_dir, "temp.wav")
        audio.export(wav_file, format="wav")
        
        # Perform speech recognition
        with sr.AudioFile(wav_file) as source:
            audio_data = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio_data)
        
        # Analyze the text and audio characteristics
        personality_traits = self._analyze_personality_traits(text, audio)
        conversation_patterns = self._analyze_conversation_patterns(text, audio)
        
        # Save results
        results = {
            "panelist_type": panelist_type,
            "timestamp": datetime.now().isoformat(),
            "personality_traits": personality_traits,
            "conversation_patterns": conversation_patterns,
            "raw_text": text
        }
        
        self._save_analysis_results(results, panelist_type)
        return results
    
    def _analyze_personality_traits(self, text: str, audio: AudioSegment) -> Dict:
        """Analyze personality traits from text and audio"""
        traits = self.personality_traits.copy()
        
        # Analyze formality
        formal_words = ["therefore", "however", "furthermore", "consequently"]
        traits["formality"] = sum(1 for word in formal_words if word in text.lower()) / len(formal_words)
        
        # Analyze enthusiasm (based on volume and pitch variations)
        volume_std = np.std([frame.dBFS for frame in audio[::100]])
        traits["enthusiasm"] = min(volume_std / 10, 1.0)
        
        # Analyze analytical nature
        analytical_words = ["because", "therefore", "analysis", "statistics", "data"]
        traits["analytical"] = sum(1 for word in analytical_words if word in text.lower()) / len(analytical_words)
        
        # Calculate speech rate
        words = text.split()
        duration_minutes = len(audio) / (1000 * 60)  # Convert ms to minutes
        traits["speech_rate"] = len(words) / duration_minutes
        
        # Analyze vocabulary complexity
        complex_words = [word for word in words if len(word) > 6]
        traits["vocabulary_complexity"] = len(complex_words) / len(words)
        
        return traits
    
    def _analyze_conversation_patterns(self, text: str, audio: AudioSegment) -> Dict:
        """Analyze conversation patterns from text and audio"""
        patterns = self.conversation_patterns.copy()
        
        # Analyze interruption patterns
        interruption_phrases = ["excuse me", "let me interrupt", "hold on", "wait a minute"]
        patterns["interruption_probability"] = sum(1 for phrase in interruption_phrases if phrase in text.lower()) / len(interruption_phrases)
        
        # Analyze agreement/disagreement patterns
        agreement_phrases = ["I agree", "exactly", "absolutely", "that's right"]
        disagreement_phrases = ["I disagree", "not really", "I don't think so", "that's not correct"]
        
        patterns["agreement_frequency"] = sum(1 for phrase in agreement_phrases if phrase in text.lower()) / len(agreement_phrases)
        patterns["disagreement_frequency"] = sum(1 for phrase in disagreement_phrases if phrase in text.lower()) / len(disagreement_phrases)
        
        # Analyze question frequency
        questions = text.count("?")
        patterns["question_frequency"] = min(questions / 10, 1.0)  # Normalize to 0-1 scale
        
        return patterns
    
    def _save_analysis_results(self, results: Dict, panelist_type: str):
        """Save analysis results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.processed_data_dir, f"{panelist_type}_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    
    def aggregate_analysis(self, panelist_type: str) -> Dict:
        """Aggregate analysis results for a panelist type"""
        results = []
        
        # Load all analysis files for this panelist type
        for filename in os.listdir(self.processed_data_dir):
            if filename.startswith(panelist_type):
                with open(os.path.join(self.processed_data_dir, filename), 'r') as f:
                    results.append(json.load(f))
        
        if not results:
            return {
                "personality_traits": self.personality_traits,
                "conversation_patterns": self.conversation_patterns
            }
        
        # Calculate averages
        avg_personality = {}
        avg_patterns = {}
        
        for trait in self.personality_traits.keys():
            values = [r["personality_traits"][trait] for r in results]
            avg_personality[trait] = sum(values) / len(values)
        
        for pattern in self.conversation_patterns.keys():
            values = [r["conversation_patterns"][pattern] for r in results]
            avg_patterns[pattern] = sum(values) / len(values)
        
        return {
            "personality_traits": avg_personality,
            "conversation_patterns": avg_patterns
        } 