import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DID_API_KEY = os.getenv('DID_API_KEY')
DID_BASE_URL = "https://api.d-id.com"

def get_avatar_result(clip_id):
    """Get the result of your created avatar"""
    headers = {
        'Authorization': f'Basic {DID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{DID_BASE_URL}/clips/{clip_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("🎬 Avatar Details:")
            print(f"ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            print(f"Created: {result.get('created_at')}")
            
            if result.get('result_url'):
                print(f"\n📺 VIDEO URL: {result.get('result_url')}")
                print("👆 Click this link to view your coach avatar!")
            
            if result.get('audio_url'):
                print(f"\n🔊 AUDIO URL: {result.get('audio_url')}")
            
            # Show full response for debugging
            print(f"\n📋 Full Response:")
            import json
            print(json.dumps(result, indent=2))
            
            return result
        else:
            print(f"❌ Error getting avatar: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Your avatar ID from the previous creation
    avatar_id = "clp_vTLVNjnQvJz7I6XmY2oAw"
    
    print(f"Getting your avatar result for ID: {avatar_id}")
    get_avatar_result(avatar_id)