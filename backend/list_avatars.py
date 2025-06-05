import os
import requests
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Define role-based voice recommendations
VOICE_RECOMMENDATIONS = {
    "host": ["en-US-JennyNeural", "en-US-AriaNeural"],  # Professional female voices
    "coach": ["en-US-GuyNeural", "en-US-RogerNeural"],  # Experienced male voices
    "referee": ["en-US-RogerNeural", "en-US-GuyNeural"],  # Authoritative male voices
    "home_fan": ["en-US-AriaNeural", "en-US-JennyNeural"],  # Passionate female voices
    "away_fan": ["en-US-EricNeural", "en-US-GuyNeural"],  # Defensive male voices
    "stats": ["en-US-SaraNeural", "en-US-JennyNeural"]  # Analytical female voices
}

def list_available_avatars():
    """List all available avatars from D-ID API"""
    # Get D-ID API credentials
    api_key = os.environ.get("DID_API_KEY")
    if not api_key or ":" not in api_key:
        raise ValueError("DID_API_KEY is not set correctly or missing ':'")
    
    username, password = api_key.split(":", 1)

    # Create Basic Auth header
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }

    # Send GET request to list available avatars
    response = requests.get(
        "https://api.d-id.com/avatars",
        headers=headers
    )

    # Debug info
    print("Status code:", response.status_code)
    print("Response body:", response.text)

    # Check response
    if response.status_code != 200:
        print("❌ Could not fetch avatars.")
        return

    # Parse response
    data = response.json()
    avatars = data.get('avatars', [])
    
    if not avatars:
        print("\n❌ No avatars found in the library.")
        return

    # Print avatars
    print("\n📋 Available Avatars:")
    print("====================")
    for avatar in avatars:
        print(f"ID: {avatar.get('id')}")
        print(f"Name: {avatar.get('name')}")
        print(f"Gender: {avatar.get('gender', 'N/A')}")
        print(f"Age: {avatar.get('age', 'N/A')}")
        print(f"Style: {avatar.get('style', 'N/A')}")
        print("--------------------")

    # Group avatars by gender
    male_avatars = []
    female_avatars = []
    
    for avatar in avatars:
        if avatar.get('gender', '').lower() == 'male':
            male_avatars.append(avatar)
        elif avatar.get('gender', '').lower() == 'female':
            female_avatars.append(avatar)

    # Print role-based recommendations
    print("\n🎭 Role-Based Avatar Recommendations:")
    print("===================================")
    
    print("\n👨 Male Avatars (for Coach, Referee, Away Fan):")
    print("----------------------------------------")
    for avatar in male_avatars:
        print(f"ID: {avatar.get('id')}")
        print(f"Name: {avatar.get('name')}")
        print(f"Age: {avatar.get('age', 'N/A')}")
        print(f"Style: {avatar.get('style', 'N/A')}")
        print("--------------------")

    print("\n👩 Female Avatars (for Host, Home Fan, Stats):")
    print("----------------------------------------")
    for avatar in female_avatars:
        print(f"ID: {avatar.get('id')}")
        print(f"Name: {avatar.get('name')}")
        print(f"Age: {avatar.get('age', 'N/A')}")
        print(f"Style: {avatar.get('style', 'N/A')}")
        print("--------------------")

    print("\n🗣️ Recommended Voice Configurations:")
    print("=================================")
    for role, voices in VOICE_RECOMMENDATIONS.items():
        print(f"\n{role.upper()}:")
        print(f"  Recommended voices: {', '.join(voices)}")

if __name__ == "__main__":
    list_available_avatars()
