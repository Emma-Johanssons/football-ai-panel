"""
Test script to verify FFmpeg configuration
"""
import os
import subprocess
from pydub import AudioSegment
from ffmpeg_config import FFMPEG_EXECUTABLE

def test_ffmpeg():
    print("Testing FFmpeg configuration...")
    
    # Test 1: Direct FFmpeg command
    try:
        result = subprocess.run([FFMPEG_EXECUTABLE, "-version"], 
                              capture_output=True, 
                              text=True)
        print("\nTest 1 - Direct FFmpeg command:")
        print(result.stdout)
    except Exception as e:
        print(f"Error in Test 1: {e}")
    
    # Test 2: AudioSegment
    try:
        print("\nTest 2 - AudioSegment configuration:")
        print(f"AudioSegment.converter: {AudioSegment.converter}")
        print(f"AudioSegment.ffmpeg: {AudioSegment.ffmpeg}")
        print(f"AudioSegment.ffprobe: {AudioSegment.ffprobe}")
    except Exception as e:
        print(f"Error in Test 2: {e}")
    
    # Test 3: System PATH
    print("\nTest 3 - System PATH:")
    print(os.environ["PATH"])

if __name__ == "__main__":
    test_ffmpeg() 