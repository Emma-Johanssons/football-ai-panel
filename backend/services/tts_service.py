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
import subprocess
import shutil
import json

# Explicitly set FFmpeg paths at module level
load_dotenv()
ffmpeg_path = os.getenv("FFMPEG_PATH")
ffprobe_path = os.getenv("FFPROBE_PATH")

if ffmpeg_path and os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    if ffprobe_path and os.path.exists(ffprobe_path):
        AudioSegment.ffprobe = ffprobe_path
    else:
        # Try to find ffprobe in the same directory as ffmpeg
        ffprobe_dir = os.path.dirname(ffmpeg_path)
        ffprobe_path = os.path.join(ffprobe_dir, 'ffprobe.exe')
        if os.path.exists(ffprobe_path):
            AudioSegment.ffprobe = ffprobe_path

def configure_ffmpeg():
    """Configure FFmpeg paths for pydub"""
    # Load environment variables
    load_dotenv()
    
    # Try to get FFmpeg paths from environment variables
    ffmpeg_path = os.getenv('FFMPEG_PATH')
    ffprobe_path = os.getenv('FFPROBE_PATH')
    
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        # Configure pydub with FFmpeg paths
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        
        # Use ffprobe path if provided, otherwise try to find it
        if ffprobe_path and os.path.exists(ffprobe_path):
            AudioSegment.ffprobe = ffprobe_path
            print(f"✅ FFmpeg configured from .env:")
            print(f"   - FFmpeg: {ffmpeg_path}")
            print(f"   - FFprobe: {ffprobe_path}")
            return True
        else:
            # Try to find ffprobe in the same directory as ffmpeg
            ffprobe_dir = os.path.dirname(ffmpeg_path)
            ffprobe_path = os.path.join(ffprobe_dir, 'ffprobe.exe')
            if os.path.exists(ffprobe_path):
                AudioSegment.ffprobe = ffprobe_path
                print(f"✅ FFmpeg configured from .env:")
                print(f"   - FFmpeg: {ffmpeg_path}")
                print(f"   - FFprobe: {ffprobe_path}")
                return True
            else:
                print("❌ ffprobe not found. Please ensure ffprobe.exe is in the same directory as ffmpeg.exe")
                return False
    
    system = platform.system().lower()
    
    if system == 'windows':
        # Common Windows FFmpeg paths
        common_paths = [
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
            os.path.join(os.environ.get('USERPROFILE', ''), 'ffmpeg\\bin\\ffmpeg.exe'),
            'ffmpeg.exe'  # If in PATH
        ]
        
        # Try to find FFmpeg
        for path in common_paths:
            if os.path.exists(path):
                # Configure pydub with FFmpeg paths
                AudioSegment.converter = path
                AudioSegment.ffmpeg = path
                
                # Try to find ffprobe in the same directory
                ffprobe_dir = os.path.dirname(path)
                ffprobe_path = os.path.join(ffprobe_dir, 'ffprobe.exe')
                if os.path.exists(ffprobe_path):
                    AudioSegment.ffprobe = ffprobe_path
                    print(f"✅ FFmpeg configured from system:")
                    print(f"   - FFmpeg: {path}")
                    print(f"   - FFprobe: {ffprobe_path}")
                    return True
                else:
                    print(f"❌ ffprobe not found in {ffprobe_dir}")
                    continue
                
        print("❌ FFmpeg not found. Please install FFmpeg and ensure it's in your PATH")
        return False
    else:
        AudioSegment.converter = 'ffmpeg'
        AudioSegment.ffmpeg = 'ffmpeg'
        AudioSegment.ffprobe = 'ffprobe'
        return True

# Configure FFmpeg at module level
if not configure_ffmpeg():
    print("⚠️ Warning: FFmpeg configuration failed. Audio processing may not work correctly.")

class TTSService:
    def __init__(self, audio_dir: str = None):
        """Initialize the TTS service"""
        # Get the absolute path to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_dir, '.env')
        
        # Load environment variables from the .env file
        load_dotenv(env_path)
        
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
            
        set_api_key(self.api_key)
        
        # Configure FFmpeg paths
        if not configure_ffmpeg():
            raise ValueError("FFmpeg configuration failed. Please ensure FFmpeg and ffprobe are properly installed.")
        
        # Set audio directory
        self.audio_dir = audio_dir if audio_dir else os.path.join(backend_dir, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Create temp directory for segments
        self.temp_dir = os.path.join(self.audio_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def _normalize_audio(self, audio_segment: AudioSegment) -> AudioSegment:
        """Normalize audio levels with special handling for the first part"""
        try:
            # Get the average volume of the main part of the segment (after first second)
            if len(audio_segment) > 1000:  # If segment is longer than 1 second
                main_part = audio_segment[1000:]  # Get everything after first second
                target_volume = main_part.dBFS
                
                # Normalize first second to match the target volume
                first_second = audio_segment[:1000]
                first_second = first_second.normalize(headroom=0.01)
                volume_diff = target_volume - first_second.dBFS
                first_second = first_second + volume_diff
                
                # Combine the normalized first second with the rest
                return first_second + main_part
            else:
                # If segment is too short, just normalize the whole thing
                return audio_segment.normalize(headroom=0.01)
        except Exception as e:
            print(f"❌ Error in segment normalization: {e}")
            return audio_segment.normalize(headroom=0.01)

    def _add_speaker_transition(self, audio_segment: AudioSegment, is_new_speaker: bool) -> AudioSegment:
        """Add minimal transition effects between speakers"""
        if is_new_speaker:
            # Add a very short silence buffer (25ms) before new speaker
            silence = AudioSegment.silent(duration=25)
            return silence + audio_segment
        return audio_segment

    async def generate_speech(self, text: str, speaker: str, voice_settings: VoiceSettings) -> Optional[str]:
        """Generate speech with provided voice settings"""
        try:
            # Generate audio with provided settings
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_settings.voice_id,
                    settings=voice_settings
                )
            )
            
            # Save audio with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{speaker.replace(' ', '_')}_{timestamp}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(audio)
            print(f"✅ Audio saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error generating speech: {e}")
            return None

    async def generate_segments(self, segments: List[Dict]) -> List[str]:
        """Generate individual audio segments for each part of the discussion"""
        segment_files = []
        
        for i, segment in enumerate(segments):
            try:
                # Generate audio for this segment
                audio_file = await self.generate_speech(
                    text=segment["text"],
                    speaker=segment["type"],
                    voice_settings=segment["voice_settings"]
                )
                
                if audio_file:
                    # Rename to segment_X.mp3 format
                    segment_number = str(i+1).zfill(3)  # 001, 002, etc.
                    new_filename = f"segment_{segment_number}.mp3"
                    new_path = os.path.join(self.audio_dir, "temp", new_filename)
                    
                    # Move the file to temp directory
                    os.rename(audio_file, new_path)
                    segment_files.append(new_path)
                    
            except Exception as e:
                print(f"❌ Error generating segment {i+1}: {e}")
                continue
        
        return segment_files