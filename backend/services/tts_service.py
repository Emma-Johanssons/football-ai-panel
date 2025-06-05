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
from ffmpeg_config import FFMPEG_EXECUTABLE  # Import FFmpeg configuration

# Configure FFmpeg path
AudioSegment.converter = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\emma-\Downloads\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\ffmpeg-2025-06-02-git-688f3944ce-essentials_build\bin\ffprobe.exe"

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
        
        # Define voice configurations for each character with emotional variations
        self.voice_configs = {
            "Show Host": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - Professional female voice
                "settings": VoiceSettings(
                    stability=0.5,  # Less stable for more natural flow
                    similarity_boost=0.75,
                    style=0.7,  # More conversational
                    use_speaker_boost=True
                )
            },
            "Tactical Analyst": {
                "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George - Male voice for coach
                "settings": VoiceSettings(
                    stability=0.4,  # Less stable for more natural flow
                    similarity_boost=0.7,
                    style=0.8,  # More expressive and natural
                    use_speaker_boost=True
                ),
                "joking_settings": VoiceSettings(  # More relaxed, joking tone
                    stability=0.3,
                    similarity_boost=0.7,
                    style=0.9,
                    use_speaker_boost=True
                )
            },
            "Stats Expert": {
                "voice_id": "N2lVS1w4EtoT3dr4eOWO",  # Callum - Male voice for stats expert
                "settings": VoiceSettings(
                    stability=0.5,  # Less stable for more natural flow
                    similarity_boost=0.7,
                    style=0.7,  # More conversational
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
            
            # Generate individual audio segments
            audio_segments = []
            for point in discussion_points:
                # Map team-specific fan types to generic fan types
                speaker_type = point["type"]
                if "Paris Saint Germain" in speaker_type:
                    speaker_type = "Paris Saint Germain Fan"
                elif "Inter" in speaker_type:
                    speaker_type = "Inter Fan"
                elif "Fan" in speaker_type and not any(team in speaker_type for team in ["Paris Saint Germain", "Inter"]):
                    # For other teams, use Home/Away Fan configuration
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
                
                # Generate audio
                audio = generate(
                    text=point["text"],
                    voice=Voice(
                        voice_id=config["voice_id"],
                        settings=settings
                    )
                )
                
                # Convert to AudioSegment
                segment = AudioSegment.from_mp3(audio)
                
                # Add overlap if specified
                if point.get("overlap", 0) > 0 and audio_segments:
                    # Overlap with previous segment
                    previous_segment = audio_segments[-1]
                    overlap_ms = point["overlap"] * 1000  # Convert to milliseconds
                    if len(previous_segment) > overlap_ms:
                        # Mix the overlapping parts
                        mixed = previous_segment[-overlap_ms:].overlay(segment[:overlap_ms])
                        # Replace the end of previous segment with mixed audio
                        audio_segments[-1] = previous_segment[:-overlap_ms] + mixed
                        # Start current segment after overlap
                        segment = segment[overlap_ms:]
                
                # For fan agents, make the audio more dynamic
                if "Fan" in speaker_type:
                    # Add slight variations in pitch and speed
                    segment = segment.speedup(playback_speed=1.1)  # Slightly faster
                    segment = segment._spawn(segment.raw_data, overrides={
                        "frame_rate": int(segment.frame_rate * 1.05)  # Slightly higher pitch
                    })
                
                audio_segments.append(segment)
            
            # Combine all segments
            if not audio_segments:
                return None

            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # Save final mixed audio
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"panel_discussion_{timestamp}.mp3"
            filepath = os.path.join(output_dir, filename)
            
            final_audio.export(filepath, format="mp3")
            print(f"✅ Mixed audio saved to {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error generating mixed discussion: {e}")
            return None

    def generate_speech(self, text: str, agent_type: str) -> Optional[str]:
        """Generate speech for a single utterance and save as mp3. Synchronous version for batch processing."""
        try:
            config = self.voice_configs.get(agent_type)
            if not config:
                print(f"No voice configuration found for {agent_type}")
                return None
            settings = config["settings"]
            # Generate audio
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
            filename = f"{agent_type.replace(' ', '_')}_{timestamp}.mp3"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(audio)
            print(f"✅ Audio saved to {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Error generating speech: {e}")
            return None