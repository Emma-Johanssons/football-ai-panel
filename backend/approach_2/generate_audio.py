"""
Script to generate audio from panel discussion using ElevenLabs TTS
"""
import asyncio
import os
import platform
import subprocess
from dotenv import load_dotenv
import argparse
from elevenlabs import VoiceSettings
from pydub import AudioSegment
import shutil

# Update paths to reflect new structure
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to reach backend
APPROACH_DIR = os.path.dirname(os.path.abspath(__file__))  # Current approach_2 directory
SERVICES_DIR = os.path.join(BACKEND_DIR, "services")
AUDIO_DIR = os.path.join(APPROACH_DIR, "audio")
SCRIPTS_DIR = os.path.join(APPROACH_DIR, "scripts")
GENERATED_SCRIPTS_DIR = os.path.join(APPROACH_DIR, "generated_scripts")

# Add the new directories to Python path
import sys
sys.path.append(BACKEND_DIR)
sys.path.append(SERVICES_DIR)

# Now import services after adding the path
from services.tts_service import TTSService

# Ensure required directories exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(GENERATED_SCRIPTS_DIR, exist_ok=True)

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
            
            # Test FFmpeg configuration
            try:
                test_cmd = [ffmpeg_path, "-version"]
                result = subprocess.run(test_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ FFmpeg test successful")
                else:
                    print("❌ FFmpeg test failed")
                    return False
            except Exception as e:
                print(f"❌ Error testing FFmpeg: {e}")
                return False
                
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
                
                # Test FFmpeg configuration
                try:
                    test_cmd = [ffmpeg_path, "-version"]
                    result = subprocess.run(test_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ FFmpeg test successful")
                    else:
                        print("❌ FFmpeg test failed")
                        return False
                except Exception as e:
                    print(f"❌ Error testing FFmpeg: {e}")
                    return False
                    
                return True
            else:
                print("❌ ffprobe not found. Please ensure ffprobe.exe is in the same directory as ffmpeg.exe")
                return False
    
    # Fallback to system detection if .env paths not found
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
                    
                    # Test FFmpeg configuration
                    try:
                        test_cmd = [path, "-version"]
                        result = subprocess.run(test_cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            print("✅ FFmpeg test successful")
                        else:
                            print("❌ FFmpeg test failed")
                            continue
                    except Exception as e:
                        print(f"❌ Error testing FFmpeg: {e}")
                        continue
                        
                    return True
                else:
                    print(f"❌ ffprobe not found in {ffprobe_dir}")
                    continue
                
        print("❌ FFmpeg not found. Please install FFmpeg and ensure it's in your PATH")
        return False
    else:
        # For macOS and Linux, assume FFmpeg is in PATH
        AudioSegment.converter = 'ffmpeg'
        AudioSegment.ffmpeg = 'ffmpeg'
        AudioSegment.ffprobe = 'ffprobe'
        
        # Test FFmpeg configuration
        try:
            test_cmd = ['ffmpeg', "-version"]
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ FFmpeg test successful")
                return True
            else:
                print("❌ FFmpeg test failed")
                return False
        except Exception as e:
            print(f"❌ Error testing FFmpeg: {e}")
            return False

async def parse_discussion_file(filename: str):
    """Parse the discussion file into segments for TTS processing"""
    segments = []
    current_segment = None
    current_speaker = None
    current_text = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Check for segment headers
        if line.startswith("==="):
            if current_speaker and current_text:
                segments.append({
                    "type": current_speaker,
                    "text": " ".join(current_text),
                    "segment": current_segment
                })
            current_segment = line.strip("= ")
            current_text = []
            current_speaker = None
            continue
            
        # Check for speaker lines
        if line.endswith(":"):
            if current_speaker and current_text:
                segments.append({
                    "type": current_speaker,
                    "text": " ".join(current_text),
                    "segment": current_segment
                })
            current_speaker = line.strip(":")
            current_text = []
            continue
            
        # Add content to current text if we have a speaker
        if current_speaker:
            current_text.append(line)
            
    # Add the last segment if exists
    if current_speaker and current_text:
        segments.append({
            "type": current_speaker,
            "text": " ".join(current_text),
            "segment": current_segment
        })
        
    return segments

class VoiceConfigManager:
    def __init__(self):
        # Define emotion-triggering words with more dynamic and emotional content
        self.EXCITED_WORDS = [
            "wow", "incredible", "amazing", "fantastic", "brilliant", "unbelievable", "stunning",
            "spectacular", "outstanding", "magnificent", "superb", "excellent", "phenomenal",
            "exceptional", "marvelous", "splendid", "wonderful", "terrific", "awesome",
            "incredible", "stunning", "remarkable", "extraordinary", "mind-blowing", "game-changing",
            "decisive", "crucial", "pivotal", "game-changing", "match-winning", "spectacular"
        ]
        
        self.ANALYTICAL_WORDS = [
            "statistics", "expected goals", "xG", "possession", "analysis", "passing percentage",
            "data", "shows", "numbers", "figures", "percentage", "accuracy", "efficiency",
            "metrics", "performance", "indicators", "trends", "patterns", "breakdown",
            "tactical", "strategy", "formation", "positioning", "movement", "coordination",
            "structure", "system", "approach", "methodology", "technique", "execution"
        ]
        
        self.CASUAL_WORDS = [
            "you know", "like", "sort of", "kind of", "well", "actually", "basically",
            "literally", "honestly", "anyway", "right", "so", "now", "look", "see",
            "think", "mean", "guess", "suppose", "obviously", "clearly", "evidently",
            "naturally", "certainly", "definitely", "absolutely", "indeed", "surely"
        ]

        self.voice_configs = {
            "Show Host": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah
                "base_settings": VoiceSettings(
                    stability=0.08,  # Even lower stability for more natural variation
                    similarity_boost=0.2,  # Lower similarity for more natural sound
                    style=0.9,  # Higher style for more expressiveness
                    use_speaker_boost=True
                ),
                "emotion_settings": {
                    "excited": VoiceSettings(
                        stability=0.03,  # Ultra low stability for excitement
                        similarity_boost=0.15,
                        style=0.95,  # Maximum style for expressiveness
                        use_speaker_boost=True
                    ),
                    "analytical": VoiceSettings(
                        stability=0.1,  # Low stability for analysis
                        similarity_boost=0.25,
                        style=0.85,  # Very expressive
                        use_speaker_boost=True
                    ),
                    "casual": VoiceSettings(
                        stability=0.05,  # Very low stability for casual conversation
                        similarity_boost=0.18,
                        style=0.92,  # Maximum expressiveness for casual talk
                        use_speaker_boost=True
                    )
                }
            },
            "Tactical Analyst": {
                "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George
                "base_settings": VoiceSettings(
                    stability=0.03,  # Ultra low stability for maximum natural variation
                    similarity_boost=0.15,  # Very low similarity for more natural sound
                    style=0.95,  # Maximum style for expressiveness
                    use_speaker_boost=True
                ),
                "emotion_settings": {
                    "excited": VoiceSettings(
                        stability=0.02,  # Extreme low stability for excitement
                        similarity_boost=0.12,
                        style=0.98,  # Maximum style for expressiveness
                        use_speaker_boost=True
                    ),
                    "analytical": VoiceSettings(
                        stability=0.05,  # Very low stability for analysis
                        similarity_boost=0.2,
                        style=0.9,  # Very expressive
                        use_speaker_boost=True
                    ),
                    "casual": VoiceSettings(
                        stability=0.03,  # Ultra low stability for casual conversation
                        similarity_boost=0.15,
                        style=0.95,  # Maximum expressiveness for casual talk
                        use_speaker_boost=True
                    )
                }
            },
            "Stats Expert": {
                "voice_id": "N2lVS1w4EtoT3dr4eOWO",  # Callum
                "base_settings": VoiceSettings(
                    stability=0.03,  # Ultra low stability for maximum natural variation
                    similarity_boost=0.15,  # Very low similarity for more natural sound
                    style=0.95,  # Maximum style for expressiveness
                    use_speaker_boost=True
                ),
                "emotion_settings": {
                    "excited": VoiceSettings(
                        stability=0.02,  # Extreme low stability for excitement
                        similarity_boost=0.12,
                        style=0.98,  # Maximum style for expressiveness
                        use_speaker_boost=True
                    ),
                    "analytical": VoiceSettings(
                        stability=0.05,  # Very low stability for analysis
                        similarity_boost=0.2,
                        style=0.9,  # Very expressive
                        use_speaker_boost=True
                    ),
                    "casual": VoiceSettings(
                        stability=0.03,  # Ultra low stability for casual conversation
                        similarity_boost=0.15,
                        style=0.95,  # Maximum expressiveness for casual talk
                        use_speaker_boost=True
                    )
                }
            }
        }

    def get_voice_settings(self, speaker: str, text: str, emotion: str = "neutral") -> VoiceSettings:
        """Get voice settings based on speaker and content"""
        if speaker not in self.voice_configs:
            return None

        config = self.voice_configs[speaker]
        text_lower = text.lower()
        
        # Enhanced emotion detection
        excited_count = sum(1 for word in self.EXCITED_WORDS if word in text_lower)
        analytical_count = sum(1 for word in self.ANALYTICAL_WORDS if word in text_lower)
        casual_count = sum(1 for word in self.CASUAL_WORDS if word in text_lower)
        
        # Determine emotion based on word counts and content
        if excited_count > 2 or any(word in text_lower for word in ["!", "amazing", "incredible", "fantastic"]):
            emotion = "excited"
        elif analytical_count > 3 or any(word in text_lower for word in ["analysis", "statistics", "data"]):
            emotion = "analytical"
        elif casual_count > 2 or any(word in text_lower for word in ["you know", "like", "well"]):
            emotion = "casual"
            
        # If emotion-specific settings exist, use them
        if emotion in config["emotion_settings"]:
            return config["emotion_settings"][emotion]

        return config["base_settings"]

async def combine_segments(segment_files: list, output_dir: str):
    """Combine audio segments into a single file"""
    try:
        # Create temp directory for processing
        temp_processing_dir = os.path.join(output_dir, "temp", "processing")
        os.makedirs(temp_processing_dir, exist_ok=True)
        
        # Get FFmpeg path from environment
        ffmpeg_path = os.getenv('FFMPEG_PATH')
        if not ffmpeg_path or not os.path.exists(ffmpeg_path):
            print("❌ FFmpeg path not found in environment variables")
            return None
            
        print(f"Using FFmpeg from: {ffmpeg_path}")
        
        # First convert all MP3s to WAVs
        wav_files = []
        for segment_file in segment_files:
            print(f"\nProcessing {os.path.basename(segment_file)}...")
            wav_path = os.path.join(temp_processing_dir, f"{os.path.basename(segment_file)[:-4]}.wav")
            
            try:
                # Convert MP3 to WAV using FFmpeg
                ffmpeg_cmd = [
                    ffmpeg_path, "-y",
                    "-i", segment_file,
                    "-acodec", "pcm_s16le",
                    "-ar", "44100",
                    "-ac", "2",
                    wav_path
                ]
                
                print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
                result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                if result.stderr:
                    print(f"FFmpeg output: {result.stderr}")
                
                if os.path.exists(wav_path):
                    wav_files.append(wav_path)
                    print(f"✅ Successfully converted to WAV")
                else:
                    print(f"❌ Failed to convert to WAV")
                    
            except Exception as e:
                print(f"❌ Error processing file: {e}")
                continue

        if not wav_files:
            print("❌ No WAV files were successfully created")
            return None

        # Create a file list for FFmpeg that includes silence between segments
        file_list_path = os.path.join(temp_processing_dir, "file_list.txt")
        with open(file_list_path, "w", encoding="utf-8") as f:
            for i, wav_file in enumerate(wav_files):
                # Add the segment
                f.write(f"file '{wav_file}'\n")
                
                # Add silence after each segment except the last one
                if i < len(wav_files) - 1:
                    silence_path = os.path.join(temp_processing_dir, f"silence_{i}.wav")
                    # Generate silence
                    silence_cmd = [
                        ffmpeg_path, "-y",
                        "-f", "lavfi",
                        "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", "1.0",  # 1.0 second of silence
                        silence_path
                    ]
                    
                    print(f"Generating silence segment {i}...")
                    result = subprocess.run(silence_cmd, check=True, capture_output=True, text=True)
                    
                    if os.path.exists(silence_path):
                        f.write(f"file '{silence_path}'\n")
                    else:
                        print(f"❌ Failed to create silence segment {i}")

        # Combine all segments with silence
        temp_combined_wav = os.path.join(temp_processing_dir, "combined.wav")
        print(f"\nCombining all segments with silence...")
        
        try:
            ffmpeg_cmd = [
                ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c:a", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                temp_combined_wav
            ]
            
            print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            if result.stderr:
                print(f"FFmpeg output: {result.stderr}")
                
            if not os.path.exists(temp_combined_wav):
                print("❌ Failed to create combined WAV file")
                return None
                
            # Convert the combined WAV to MP3
            output_file = os.path.join(output_dir, "combined_segments.mp3")
            print(f"\nConverting to MP3: {output_file}")
            
            ffmpeg_cmd = [
                ffmpeg_path, "-y",
                "-i", temp_combined_wav,
                "-c:a", "libmp3lame",
                "-q:a", "0",
                "-b:a", "320k",
                output_file
            ]
            
            print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            if result.stderr:
                print(f"FFmpeg output: {result.stderr}")
                
            if os.path.exists(output_file):
                print("✅ Successfully created combined MP3 file")
                return output_file
            else:
                print("❌ Failed to create final MP3 file")
                return None
                
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            return None

    except Exception as e:
        print(f"❌ Error combining segments: {e}")
        return None

async def generate_discussion_audio(discussion_file: str, output_dir: str = None):
    """Generate audio segments for the discussion and combine them"""
    try:
        # Initialize voice config manager
        voice_manager = VoiceConfigManager()
        
        # Set the correct audio directory
        audio_dir = os.path.join(APPROACH_DIR, "audio")
        if output_dir:
            audio_dir = output_dir
            
        # Initialize TTS service with the correct audio directory
        tts_service = TTSService(audio_dir=audio_dir)
        
        # Parse discussion file
        print(f"Parsing discussion file: {discussion_file}")
        segments = await parse_discussion_file(discussion_file)
        
        # Process each segment with voice configuration
        segment_files = []
        for segment in segments:
            # Get voice settings based on content
            voice_settings = voice_manager.get_voice_settings(
                speaker=segment["type"],
                text=segment["text"]
            )
            
            if voice_settings:
                # Generate audio for this segment
                audio_file = await tts_service.generate_speech(
                    text=segment["text"],
                    speaker=segment["type"]
                )
                
                if audio_file:
                    # Rename to segment_X.mp3 format
                    segment_number = str(len(segment_files) + 1).zfill(3)  # 001, 002, etc.
                    new_filename = f"segment_{segment_number}.mp3"
                    new_path = os.path.join(audio_dir, "temp", new_filename)
                    
                    # Move the file to temp directory using shutil.move
                    shutil.move(audio_file, new_path)
                    segment_files.append(new_path)
        
        if segment_files:
            print(f"✅ Successfully generated {len(segment_files)} audio segments")
            
            # Combine segments into a single file
            print("\nCombining audio segments...")
            combined_file = await combine_segments(segment_files, audio_dir)
            
            if combined_file:
                print(f"✅ Successfully created combined audio file: {combined_file}")
                return combined_file
            else:
                print("❌ Failed to combine audio segments")
                return None
        else:
            print("❌ Failed to generate audio segments")
            return None
            
    except Exception as e:
        print(f"❌ Error generating discussion audio: {e}")
        return None

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate audio from a discussion script')
    parser.add_argument('--script', type=str, required=True,
                      help='Path to the discussion script file')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Directory to save audio files (optional)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get the absolute path to the script
    script_path = os.path.abspath(args.script)
    
    print(f"\nChecking file path: {script_path}")
    print(f"Current working directory: {os.getcwd()}")
    
    if not os.path.exists(script_path):
        print(f"❌ Discussion file not found: {script_path}")
        print("\nPlease ensure:")
        print("1. The file exists and the path is correct")
        print("2. The file is not being ignored by .gitignore")
        print("\nYou can:")
        print("1. Check the file path")
        print("2. Create a new discussion file with the correct format")
        return
        
    # Verify file is readable
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ Successfully read file: {len(content)} characters")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
        
    # Configure FFmpeg first
    print("\nConfiguring FFmpeg...")
    if not configure_ffmpeg():
        print("\n❌ FFmpeg configuration failed. Please ensure:")
        print("1. FFmpeg is installed on your system")
        print("2. The FFMPEG_PATH in your .env file points to the correct ffmpeg.exe")
        print("3. ffprobe.exe is in the same directory as ffmpeg.exe")
        return
        
    # Set output directory if provided
    if args.output_dir:
        global AUDIO_DIR
        AUDIO_DIR = os.path.abspath(args.output_dir)
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
    # Generate audio
    print("\nGenerating audio...")
    combined_file = await generate_discussion_audio(script_path, args.output_dir)
    
    if combined_file:
        print("\nAudio generation complete!")
        print(f"Combined audio file saved to: {combined_file}")
        print("\nVoice assignments used:")
        print("- Show Host: Sarah (Professional female voice)")
        print("- Tactical Analyst: George (Male voice)")
        print("- Stats Expert: Callum (Male voice)")
    else:
        print("\n❌ Audio generation failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 