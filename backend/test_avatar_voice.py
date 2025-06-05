import os
import requests
from dotenv import load_dotenv
import json
import base64
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

# Define our agents with their configurations
AGENT_CONFIGS = {
    "host": {
        "avatar_url": "https://render.readyplayer.me/avatar/683c9cd1dec9915150935ef7?scale=1&blendShapes[head]=0.5&frame=full",  # Your RPM avatar
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # ElevenLabs voice ID for Rachel
        "style": "professional",
        "position": "center"
    },
    "coach": {
        "avatar_url": "https://render.readyplayer.me/avatar/683c9cd1dec9915150935ef7?scale=1&blendShapes[head]=0.5&frame=full",  # Using same avatar for now
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # ElevenLabs voice ID for Adam
        "style": "analytical",
        "position": "left"
    },
    "referee": {
        "avatar_url": "https://render.readyplayer.me/avatar/683c9cd1dec9915150935ef7?scale=1&blendShapes[head]=0.5&frame=full",  # Using same avatar for now
        "voice_id": "AZnzlk1XvdvUeBnXmlld",  # ElevenLabs voice ID for Domi
        "style": "authoritative",
        "position": "right"
    }
}

def get_avatar_image(avatar_url):
    """Get avatar image from Ready Player Me"""
    try:
        # Convert render URL to image URL
        image_url = avatar_url.replace("render.readyplayer.me/avatar", "models.readyplayer.me/avatar") + ".png"
        response = requests.get(image_url)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error getting avatar image: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting avatar image: {str(e)}")
        return None

def generate_voice(text: str, voice_id: str) -> bytes:
    """Generate voice using ElevenLabs API with proper error handling"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.text}")
            
        return response.content
        
    except Exception as e:
        print(f"Error generating voice: {str(e)}")
        raise

def test_avatar_voice():
    """Test generating audio with ElevenLabs and displaying Ready Player Me avatars"""
    print("\n🎭 Testing Avatar and Voice Generation")
    print("====================================")
    
    for agent_type, config in AGENT_CONFIGS.items():
        print(f"\nTesting {agent_type}...")
        
        # Get avatar image
        avatar_image = get_avatar_image(config["avatar_url"])
        if avatar_image:
            print(f"✅ Got avatar image for {agent_type}")
        
        # Generate audio with ElevenLabs
        try:
            audio = generate_voice(
                text="Hello! I'm your football analyst. Let me share my thoughts on the match.",
                voice_id=config["voice_id"]
            )
            
            # Save audio to file
            audio_filename = f"audio_{agent_type}.mp3"
            with open(audio_filename, "wb") as f:
                f.write(audio)
            print(f"✅ Generated audio for {agent_type}")
            
            # Display avatar information
            print(f"Avatar URL: {config['avatar_url']}")
            print(f"Voice ID: {config['voice_id']}")
            print(f"Style: {config['style']}")
            print(f"Position: {config['position']}")
            
        except Exception as e:
            print(f"❌ Error generating audio for {agent_type}: {str(e)}")

def create_avatar():
    """Create a new avatar using Ready Player Me"""
    print("\n🎨 Creating New Avatar")
    print("====================")
    
    # RPM API endpoint for creating avatars
    url = "https://api.readyplayer.me/v1/avatars"
    
    # Example avatar configuration
    avatar_config = {
        "model": "full-body",
        "style": "realistic",
        "pose": "T-pose"
    }
    
    try:
        response = requests.post(url, json=avatar_config)
        if response.status_code == 200:
            avatar_data = response.json()
            print("✅ Avatar created successfully!")
            print(f"Avatar URL: {avatar_data['url']}")
            return avatar_data['url']
        else:
            print(f"❌ Error creating avatar: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    # First, create a new avatar
    avatar_url = create_avatar()
    if avatar_url:
        # Update one of our agent configs with the new avatar
        AGENT_CONFIGS["host"]["avatar_url"] = avatar_url
    
    # Then test the avatar and voice generation
    test_avatar_voice() 