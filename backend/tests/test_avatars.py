import os
import time
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import sys

def generate_video():
    load_dotenv()
    
    api_key = os.environ.get("DID_API_KEY")
    if not api_key or ":" not in api_key:
        raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")
    
    username, password = api_key.split(":", 1)

    data = {
        "script": {
            "type": "text",
            "input": "Hello! I'm generated using the D-ID API."
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("🔄 Skickar POST till /talks ...")
    response = requests.post(
        "https://api.d-id.com/talks",
        auth=HTTPBasicAuth(username, password),
        headers=headers,
        json=data
    )

    if response.status_code != 201:
        print("❌ Fel vid skapande:", response.status_code, response.text)
        return

    talk_id = response.json()["id"]
    print(f"✅ Talk skapad med ID: {talk_id}")

    status_url = f"https://api.d-id.com/talks/{talk_id}"
    while True:
        time.sleep(2)
        status_response = requests.get(status_url, auth=HTTPBasicAuth(username, password))
        status_data = status_response.json()

        status = status_data.get("status")
        print(f"⏳ Status: {status}")

        if status == "done":
            video_url = status_data["result_url"]
            print(f"✅ Video klar! Hämtas från: {video_url}")

            video_data = requests.get(video_url).content
            with open("output_video.mp4", "wb") as f:
                f.write(video_data)
            print("🎬 Video sparad som output_video.mp4")
            break

        elif status == "error":
            print("❌ Fel vid generering:", status_data.get("error", "Okänt fel"))
            break

def create_avatar_from_image(image_path: str, name: str = "coach"):
    """Create a new D-ID avatar from an image"""
    try:
        # Get API credentials
        api_key = os.environ.get("DID_API_KEY")
        if not api_key or ":" not in api_key:
            raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")
        
        username, password = api_key.split(":", 1)
        
        # First upload the image
        print(f"📤 Uploading image: {image_path}")
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            upload_response = requests.post(
                "https://api.d-id.com/images",
                auth=HTTPBasicAuth(username, password),
                files=files
            )
            
        if upload_response.status_code != 201:
            print(f"❌ Error uploading image: {upload_response.text}")
            return None
            
        image_url = upload_response.json()['url']
        print(f"✅ Image uploaded successfully: {image_url}")
        
        # Create a talk with the uploaded image and a script
        print("🎭 Creating avatar...")
        talk_response = requests.post(
            "https://api.d-id.com/talks",
            auth=HTTPBasicAuth(username, password),
            headers={"Content-Type": "application/json"},
            json={
                "script": {
                    "type": "text",
                    "input": "Hej! Jag är din fotbollstränare."
                },
                "source_url": image_url,
                "name": name
            }
        )
        
        if talk_response.status_code != 201:
            print(f"❌ Error creating avatar: {talk_response.text}")
            return None
            
        talk_id = talk_response.json()['id']
        print(f"✅ Avatar created successfully with ID: {talk_id}")
        return talk_id
        
    except Exception as e:
        print(f"Error creating avatar: {str(e)}")
        return None

def create_persistent_avatar(image_path: str, name: str = "coach"):
    """Create a persistent D-ID avatar from an image (will appear in Studio)"""
    try:
        # Get API credentials
        api_key = os.environ.get("DID_API_KEY")
        if not api_key or ":" not in api_key:
            raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")
        
        username, password = api_key.split(":", 1)
        
        # First upload the image
        print(f"📤 Uploading image: {image_path}")
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            upload_response = requests.post(
                "https://api.d-id.com/images",
                auth=HTTPBasicAuth(username, password),
                files=files
            )
            
        if upload_response.status_code != 201:
            print(f"❌ Error uploading image: {upload_response.text}")
            return None
            
        image_url = upload_response.json()['url']
        print(f"✅ Image uploaded successfully: {image_url}")
        
        # Create persistent avatar
        print("🎭 Creating persistent avatar...")
        avatar_response = requests.post(
            "https://api.d-id.com/avatars",
            auth=HTTPBasicAuth(username, password),
            headers={"Content-Type": "application/json"},
            json={
                "source_url": image_url,
                "name": name
            }
        )
        
        if avatar_response.status_code != 201:
            print(f"❌ Error creating persistent avatar: {avatar_response.text}")
            return None
            
        avatar_id = avatar_response.json()['id']
        print(f"✅ Persistent avatar created successfully with ID: {avatar_id}")
        print("You can now reuse this avatar for all panel discussions!")
        return avatar_id
        
    except Exception as e:
        print(f"Error creating persistent avatar: {str(e)}")
        return None

def list_did_avatars():
    """List all available D-ID avatars"""
    try:
        # Get API credentials
        api_key = os.environ.get("DID_API_KEY")
        if not api_key or ":" not in api_key:
            raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")
        
        username, password = api_key.split(":", 1)
        
        # First try the talks endpoint
        response = requests.get(
            "https://api.d-id.com/talks",
            auth=HTTPBasicAuth(username, password),
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Error fetching avatars from talks: {response.text}")
            return
            
        data = response.json()
        print("\n📸 Available D-ID Avatars (Talks):")
        
        # Look specifically for the coach avatar
        coach_found = False
        for talk in data.get('talks', []):
            if talk.get('name', '').lower() == 'coach':
                print("\n🎯 Found Coach Avatar:")
                print(f"ID: {talk.get('id')}")
                print(f"Name: {talk.get('name')}")
                print(f"Created: {talk.get('created_at')}")
                print("---")
                coach_found = True
                break
        
        if not coach_found:
            print("\n❌ Coach avatar not found in talks!")
            
        # List all avatars for reference
        print("\n📋 All Available Avatars:")
        for talk in data.get('talks', []):
            print(f"ID: {talk.get('id')}")
            print(f"Name: {talk.get('name', 'Unnamed')}")
            print(f"Created: {talk.get('created_at')}")
            print("---")
            
    except Exception as e:
        print(f"Error listing avatars: {str(e)}")

def list_persistent_avatars():
    """List all persistent D-ID avatars (including those created in Studio)"""
    try:
        api_key = os.environ.get("DID_API_KEY")
        if not api_key or ":" not in api_key:
            raise ValueError("DID_API_KEY är inte korrekt satt eller saknar ':'")
        username, password = api_key.split(":", 1)

        response = requests.get(
            "https://api.d-id.com/avatars",
            auth=HTTPBasicAuth(username, password),
            headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            print(f"❌ Error fetching persistent avatars: {response.text}")
            return
        data = response.json()
        print("\n📋 Persistent Avatars in your account:")
        for avatar in data.get('avatars', []):
            print(f"ID: {avatar.get('id')}")
            print(f"Name: {avatar.get('name', 'Unnamed')}")
            print(f"Created: {avatar.get('created_at')}")
            print("---")
    except Exception as e:
        print(f"Error listing persistent avatars: {str(e)}")

def create_agent_with_bearer(image_url: str, name: str = "Coach"):
    """Create a D-ID agent using Bearer token authentication (for /agents endpoint)"""
    load_dotenv()
    bearer_token = os.environ.get("DID_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("DID_BEARER_TOKEN is not set in .env")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    data = {
        "presenter": {
            "type": "talk",
            "voice": {
                "type": "microsoft",
                "voice_id": "sv-SE-MattiasNeural"
            },
            "source_url": image_url
        },
        "llm": {
            "type": "openai",
            "provider": "openai",
            "model": "gpt-4",
            "instructions": "You are a football coach in a panel."
        },
        "preview_name": name
    }

    response = requests.post(
        "https://api.d-id.com/agents",
        headers=headers,
        json=data
    )
    print(response.status_code, response.text)
    if response.status_code == 201:
        print("Agent created! ID:", response.json()["id"])
        return response.json()["id"]
    else:
        print("Error creating agent.")
        return None

def get_agent_with_bearer(agent_id: str):
    """Get a D-ID agent using Bearer token authentication (for /agents endpoint)"""
    load_dotenv()
    bearer_token = os.environ.get("DID_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("DID_BEARER_TOKEN is not set in .env")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(
        f"https://api.d-id.com/agents/{agent_id}",
        headers=headers
    )
    print(response.status_code, response.text)
    if response.status_code == 200:
        print("Agent details:", response.json())
        return response.json()
    else:
        print("Error getting agent.")
        return None

def create_persistent_avatar_with_bearer(image_url: str, name: str = "Coach"):
    """Create a persistent D-ID avatar using Bearer token authentication (for /avatars endpoint)"""
    load_dotenv()
    bearer_token = os.environ.get("DID_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("DID_BEARER_TOKEN is not set in .env")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    data = {
        "source_url": image_url,
        "name": name
    }

    response = requests.post(
        "https://api.d-id.com/avatars",
        headers=headers,
        json=data
    )
    print(response.status_code, response.text)
    if response.status_code == 201:
        print("✅ Persistent avatar created! ID:", response.json()["id"])
        return response.json()["id"]
    else:
        print("❌ Error creating persistent avatar.")
        return None

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Usage example for Bearer token endpoints:
    if len(sys.argv) > 2 and sys.argv[1] == "create_agent_bearer":
        image_url = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else "Coach"
        print(f"🎨 Creating agent with Bearer token from image URL: {image_url}")
        agent_id = create_agent_with_bearer(image_url, name)
        if agent_id:
            print(f"\n✨ New agent created with ID: {agent_id}")
            print("Use this ID to interact with your agent!")
    elif len(sys.argv) > 2 and sys.argv[1] == "get_agent_bearer":
        agent_id = sys.argv[2]
        print(f"🔍 Getting agent with ID: {agent_id}")
        get_agent_with_bearer(agent_id)
    elif len(sys.argv) > 2 and sys.argv[1] == "create_persistent_bearer":
        image_url = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else "Coach"
        print(f"🎨 Creating persistent avatar with Bearer token from image URL: {image_url}")
        avatar_id = create_persistent_avatar_with_bearer(image_url, name)
        if avatar_id:
            print(f"\n✨ New persistent avatar created with ID: {avatar_id}")
            print("Use this ID in your avatar_mapping.py file")
    elif len(sys.argv) > 1 and sys.argv[1] == "list_persistent":
        print("🔍 Listing persistent avatars...")
        list_persistent_avatars()
    elif len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"🎨 Creating new avatar from image: {image_path}")
        avatar_id = create_avatar_from_image(image_path)
        if avatar_id:
            print(f"\n✨ New avatar created with ID: {avatar_id}")
            print("Use this ID in your avatar_mapping.py file")
    else:
        # List available avatars
        print("🔍 Checking available D-ID avatars...")
        list_did_avatars()
