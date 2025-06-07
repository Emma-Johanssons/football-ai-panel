"""
Test script for trying out different agent voices
"""
import asyncio
from services.tts_service import TTSService
from elevenlabs import voices

async def test_voices():
    # First, let's list available voices
    print("\n🔍 Available voices:")
    available_voices = voices()
    for voice in available_voices:
        print(f"- {voice.name} (ID: {voice.voice_id})")
    
    tts = TTSService()
    
    # Short test phrases for each agent
    test_phrases = [
        {
            "type": "Show Host",
            "text": "Welcome to today's match analysis. Let's hear from our expert panel."
        },
        {
            "type": "Tactical Analyst",
            "text": "The tactical battle in midfield was fascinating to watch today."
        },
        {
            "type": "Stats Expert",
            "text": "Looking at the statistics, possession was 60-40 in favor of the home team."
        },
        {
            "type": "Home Fan",
            "text": "What a brilliant performance from our team today! The atmosphere was electric!"
        },
        {
            "type": "Away Fan",
            "text": "I can't believe that penalty decision! The referee has lost the plot!"
        }
    ]
    
    # Generate audio for each phrase
    print("\n🎤 Testing different agent voices...")
    for phrase in test_phrases:
        print(f"\nGenerating audio for {phrase['type']}...")
        audio_file = tts.generate_speech(phrase["text"], phrase["type"])
        if audio_file:
            print(f"✅ Audio saved to {audio_file}")
        else:
            print(f"❌ Failed to generate audio for {phrase['type']}")

if __name__ == "__main__":
    asyncio.run(test_voices()) 