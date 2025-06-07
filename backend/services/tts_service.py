"""
Service for handling text-to-speech using ElevenLabs API
"""
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
import time
from pydub import AudioSegment
import asyncio
import platform

# Configure FFmpeg path
def get_ffmpeg_path():
    """Get the FFmpeg executable path based on the operating system"""
    system = platform.system().lower()
    if system == 'windows':
        # Check common Windows installation paths
        common_paths = [
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
            os.path.join(os.environ.get('USERPROFILE', ''), 'ffmpeg\\bin\\ffmpeg.exe'),
            'ffmpeg.exe'  # If in PATH
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return 'ffmpeg'  # Default to hoping it's in PATH
    elif system == 'darwin':  # macOS
        return 'ffmpeg'  # Usually installed via homebrew
    else:  # Linux and others
        return 'ffmpeg'  # Usually available in system PATH

# Set FFmpeg paths for pydub
FFMPEG_PATH = get_ffmpeg_path()
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffmpeg = FFMPEG_PATH
AudioSegment.ffprobe = FFMPEG_PATH.replace('ffmpeg', 'ffprobe')

class TTSService:
    def __init__(self):
        # Get the absolute path to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_dir, '.env')
        
        # Load environment variables from the .env file
        load_dotenv(env_path)
        
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
            
        set_api_key(self.api_key)
        
        # Define voice configurations for each character with personality-based settings
        self.voice_configs = {
            "Show Host": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - Professional female voice
                "settings": VoiceSettings(
                    stability=0.75,  # More stable for broadcast clarity
                    similarity_boost=0.85,  # Stronger voice consistency
                    style=0.7,  # Engaging but professional
                    use_speaker_boost=True
                ),
                "excited_settings": VoiceSettings(  # For key moments
                    stability=0.6,  # More dynamic for exciting moments
                    similarity_boost=0.8,
                    style=0.85,  # More animated
                    use_speaker_boost=True
                )
            },
            "Tactical Analyst": {
                "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George - Male voice for analyst
                "settings": VoiceSettings(
                    stability=0.8,  # Very stable for clear analysis
                    similarity_boost=0.8,
                    style=0.65,  # Professional but engaging
                    use_speaker_boost=True
                ),
                "detailed_settings": VoiceSettings(  # For deep tactical analysis
                    stability=0.85,
                    similarity_boost=0.75,
                    style=0.6,  # More focused
                    use_speaker_boost=True
                )
            },
            "Stats Expert": {
                "voice_id": "N2lVS1w4EtoT3dr4eOWO",  # Callum - Male voice for stats
                "settings": VoiceSettings(
                    stability=0.85,  # Very stable for precise stats
                    similarity_boost=0.8,
                    style=0.6,  # Clear and authoritative
                    use_speaker_boost=True
                ),
                "excited_settings": VoiceSettings(  # For impressive stats
                    stability=0.7,
                    similarity_boost=0.75,
                    style=0.75,  # More animated for key stats
                    use_speaker_boost=True
                )
            },
            "Home Fan": {
                "voice_id": "9BWtsMINqrJLrRacOk9x",  # Aria - Female voice for home fan
                "settings": VoiceSettings(
                    stability=0.3,  # Less stable for more natural flow
                    similarity_boost=0.7,
                    style=0.9,  # Very expressive
                    use_speaker_boost=True
                ),
                "angry_settings": VoiceSettings(  # Angry, passionate tone
                    stability=0.2,  # Even less stable for emotional outbursts
                    similarity_boost=0.7,
                    style=1.0,  # Maximum expressiveness
                    use_speaker_boost=True
                )
            },
            "Away Fan": {
                "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam - Male voice for away fan
                "settings": VoiceSettings(
                    stability=0.3,  # Less stable for more natural flow
                    similarity_boost=0.7,
                    style=0.9,  # Very expressive
                    use_speaker_boost=True
                ),
                "angry_settings": VoiceSettings(  # Angry, passionate tone
                    stability=0.2,  # Even less stable for emotional outbursts
                    similarity_boost=0.7,
                    style=1.0,  # Maximum expressiveness
                    use_speaker_boost=True
                )
            },
            "Inter Fan": {
                "voice_id": "XB0fDUnXU5powFXDhCwa",  # Charlotte - Female voice for Inter fan
                "settings": VoiceSettings(
                    stability=0.3,  # Less stable for more natural flow
                    similarity_boost=0.7,
                    style=0.9,
                    use_speaker_boost=True
                ),
                "angry_settings": VoiceSettings(  # Angry, passionate tone
                    stability=0.2,  # Even less stable for emotional outbursts
                    similarity_boost=0.7,
                    style=1.0,
                    use_speaker_boost=True
                )
            },
            "Paris Saint Germain Fan": {  # Changed from "PSG Fan" to full name
                "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - Male voice for PSG fan
                "settings": VoiceSettings(
                    stability=0.2,  # Very dynamic for emotional expression
                    similarity_boost=0.7,
                    style=1.0,  # Maximum expressiveness
                    use_speaker_boost=True
                ),
                "angry_settings": VoiceSettings(  # Angry, passionate tone
                    stability=0.1,  # Extremely dynamic for emotional outbursts
                    similarity_boost=0.7,
                    style=1.0,
                    use_speaker_boost=True
                )
            }
        }
        
    async def generate_mixed_discussion(self, discussion_points: List[Dict]) -> Optional[str]:
        """Generate a single mixed audio recording of the entire discussion"""
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), "audio")
            os.makedirs(output_dir, exist_ok=True)
            
            # Create temp directory for segments
            temp_dir = os.path.join(output_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate individual audio segments
            audio_segments = []
            previous_speaker = None
            
            for i, point in enumerate(discussion_points):
                # Add subtle background noise for radio effect
                ambient_noise = AudioSegment.silent(duration=500).overlay(
                    AudioSegment.silent(duration=500).low_pass_filter(2000)
                )
                
                # Map team-specific fan types to generic fan types
                speaker_type = point["type"]
                if "Paris Saint Germain" in speaker_type:
                    speaker_type = "Paris Saint Germain Fan"
                elif "Inter" in speaker_type:
                    speaker_type = "Inter Fan"
                elif "Fan" in speaker_type and not any(team in speaker_type for team in ["Paris Saint Germain", "Inter"]):
                    speaker_type = "Home Fan" if "Home" in speaker_type else "Away Fan"
                
                config = self.voice_configs.get(speaker_type)
                if not config:
                    print(f"No voice configuration found for {speaker_type}")
                    continue
                
                # Select appropriate voice settings based on context
                settings = config["settings"]
                if "angry" in point.get("emotion", "").lower() and "angry_settings" in config:
                    settings = config["angry_settings"]
                elif "joking" in point.get("emotion", "").lower() and "joking_settings" in config:
                    settings = config["joking_settings"]
                
                # Generate audio and save to temp file
                temp_file = os.path.join(temp_dir, f"segment_{i}.mp3")
                audio_data = generate(
                    text=point["text"],
                    voice=Voice(
                        voice_id=config["voice_id"],
                        settings=settings
                    )
                )
                
                # Save binary audio data to temp file
                with open(temp_file, "wb") as f:
                    f.write(audio_data)
                
                # Load as AudioSegment
                segment = AudioSegment.from_mp3(temp_file)
                
                # Add radio effect
                segment = segment.overlay(ambient_noise, gain_during_overlay=-30)
                
                # Add natural pause between different speakers
                if previous_speaker and previous_speaker != speaker_type:
                    # Add a pause between different speakers (500ms)
                    pause_duration = 500  # 500ms pause
                    pause = AudioSegment.silent(duration=pause_duration)
                    
                    # If the previous segment ends with a question mark, add slightly longer pause
                    if any(point.get("text", "").strip().endswith(c) for c in ["?", "..."]):
                        pause = AudioSegment.silent(duration=800)  # 800ms pause for questions
                    
                    audio_segments.append(pause)
                
                # Add crossfade between segments of the same speaker
                if audio_segments and previous_speaker == speaker_type:
                    crossfade_duration = 100  # Shorter crossfade for same speaker
                    if len(audio_segments[-1]) > crossfade_duration and len(segment) > crossfade_duration:
                        audio_segments[-1] = audio_segments[-1].append(segment, crossfade=crossfade_duration)
                    else:
                        audio_segments.append(segment)
                else:
                    audio_segments.append(segment)
                
                # Add overlap if specified (with delay)
                if point.get("overlap", 0) > 0 and audio_segments:
                    previous_segment = audio_segments[-1]
                    # Add a small delay before overlap (200ms)
                    overlap_delay = 200
                    overlap_ms = (point["overlap"] * 1000) + overlap_delay
                    
                    if len(previous_segment) > overlap_ms:
                        mixed = previous_segment[-overlap_ms:].overlay(segment[:overlap_ms])
                        audio_segments[-1] = previous_segment[:-overlap_ms] + mixed
                        segment = segment[overlap_ms:]
                
                previous_speaker = speaker_type
            
            # Combine all segments
            if not audio_segments:
                return None

            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # Add subtle compression and EQ for radio effect
            final_audio = final_audio.compress_dynamic_range()
            
            # Save final mixed audio
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"panel_discussion_{timestamp}.mp3"
            filepath = os.path.join(output_dir, filename)
            
            final_audio.export(filepath, format="mp3")
            
            # Cleanup temp files
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
            
            print(f"✅ Mixed audio saved to {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error generating mixed discussion: {e}")
            return None

    async def generate_speech(self, text: str, speaker: str) -> Optional[str]:
        """Generate speech with personality-appropriate voice settings"""
        try:
            config = self.voice_configs.get(speaker)
            if not config:
                print(f"No voice configuration found for {speaker}")
                return None
                
            # Choose appropriate settings based on content
            settings = config["settings"]
            
            # Detect content type and adjust settings
            if speaker == "Show Host":
                if any(keyword in text.lower() for keyword in ["incredible", "amazing", "fantastic", "extraordinary"]):
                    settings = config["excited_settings"]
            elif speaker == "Tactical Analyst":
                if "tactical analysis" in text.lower() or "formation" in text.lower():
                    settings = config["detailed_settings"]
            elif speaker == "Stats Expert":
                if any(keyword in text.lower() for keyword in ["impressive", "significant", "remarkable"]):
                    settings = config["excited_settings"]
            
            # Generate audio with appropriate settings
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=config["voice_id"],
                    settings=settings
                )
            )
            
            # Save audio with timestamp
            output_dir = os.path.join(os.getcwd(), "audio")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{speaker.replace(' ', '_')}_{timestamp}.mp3"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(audio)
            print(f"✅ Audio saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error generating speech: {e}")
            return None