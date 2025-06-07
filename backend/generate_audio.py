"""
Script to generate audio from panel discussion using ElevenLabs TTS
"""
import asyncio
import os
from services.tts_service import TTSService

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

async def generate_discussion_audio(discussion_file: str):
    """Generate audio for the entire discussion"""
    try:
        # Initialize TTS service
        tts_service = TTSService()
        
        # Parse discussion file
        print(f"Parsing discussion file: {discussion_file}")
        segments = await parse_discussion_file(discussion_file)
        
        # Add emotion hints based on content
        for segment in segments:
            text = segment["text"].lower()
            
            # Add emotion hints for more dynamic voice generation
            if any(word in text for word in ["incredible", "amazing", "fantastic", "remarkable"]):
                segment["emotion"] = "excited"
            elif any(word in text for word in ["unfortunately", "struggled", "failed"]):
                segment["emotion"] = "disappointed"
            elif "tactical analysis" in text or "formation" in text:
                segment["emotion"] = "analytical"
            
            # Add slight overlap for more natural conversation flow
            if segment["segment"] in ["Turning Points", "Historical Context"]:
                segment["overlap"] = 0.5  # 0.5 second overlap
            
        # Generate mixed audio
        print("Generating audio...")
        audio_file = await tts_service.generate_mixed_discussion(segments)
        
        if audio_file:
            print(f"✅ Successfully generated audio: {audio_file}")
            return audio_file
        else:
            print("❌ Failed to generate audio")
            return None
            
    except Exception as e:
        print(f"❌ Error generating discussion audio: {e}")
        return None

async def main():
    # Get the discussion file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    discussion_file = os.path.join(script_dir, "generated_scripts", "match_1374812_discussion_gooood.txt")
    
    if not os.path.exists(discussion_file):
        print(f"❌ Discussion file not found: {discussion_file}")
        return
        
    # Generate audio
    audio_file = await generate_discussion_audio(discussion_file)
    
    if audio_file:
        print("\nAudio generation complete!")
        print(f"Audio file saved to: {audio_file}")
        print("\nVoice assignments used:")
        print("- Show Host: Sarah (Professional female voice)")
        print("- Tactical Analyst: George (Male voice)")
        print("- Stats Expert: Callum (Male voice)")
        
if __name__ == "__main__":
    asyncio.run(main()) 