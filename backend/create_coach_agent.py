import requests
import json
import os
from dotenv import load_dotenv
import base64
import time

# Load environment variables
load_dotenv()

# D-ID API configuration
DID_API_KEY = os.getenv('DID_API_KEY')
DID_BASE_URL = "https://api.d-id.com"

def test_did_authentication():
    """Test if D-ID API key is working"""
    headers = {
        'Authorization': f'Basic {DID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{DID_BASE_URL}/talks", headers=headers)
        print(f"Auth test status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def upload_local_image(image_path):
    """Upload a local image file to D-ID"""
    headers = {
        'Authorization': f'Basic {DID_API_KEY}'
    }
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': ('avatar.jpg', f, 'image/jpeg')}
            response = requests.post(f"{DID_BASE_URL}/images", headers=headers, files=files)
            
            print(f"Upload status: {response.status_code}")
            print(f"Upload response: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Image uploaded successfully!")
                return result.get('url')
            else:
                print(f"❌ Failed to upload image")
                return None
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        return None
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return None

def create_avatar_with_image_url(image_url):
    """Create avatar using a properly hosted image URL"""
    headers = {
        'Authorization': f'Basic {DID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "source_url": image_url,
        "script": {
            "type": "text",
            "provider": {
                "type": "microsoft",
                "voice_id": "sv-SE-MattiasNeural"
            },
            "input": "Hej! Jag är din personliga coach. Hur kan jag hjälpa dig idag?"
        }
    }
    
    try:
        print(f"Creating avatar with image: {image_url}")
        response = requests.post(f"{DID_BASE_URL}/talks", headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Avatar created successfully!")
            print(f"Avatar ID: {result.get('id')}")
            
            if result.get('result_url'):
                print(f"📺 VIDEO URL: {result.get('result_url')}")
            elif result.get('status') == 'started':
                print("⏳ Processing... Check back in a few minutes")
                
            return result
        else:
            print("❌ Failed to create avatar")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def try_alternative_image_urls():
    """Try creating avatar with some test images that should work"""
    print("🧪 Testing with alternative image URLs...")
    
    # These are publicly accessible test images
    test_images = [
        "https://create-images-results.d-id.com/DefaultPresenters/Noelle_f/image.jpeg",
        "https://create-images-results.d-id.com/DefaultPresenters/William_m/image.jpeg"
    ]
    
    for img_url in test_images:
        print(f"\nTrying: {img_url}")
        result = create_avatar_with_image_url(img_url)
        if result:
            print(f"✅ Success with test image!")
            return result
    
    return None

def download_and_save_imgur_image():
    """Download your Imgur image and save it locally"""
    imgur_url = "https://i.imgur.com/z4CH5gt.jpeg"
    
    try:
        # Try different user agents to bypass blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(imgur_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Save the image locally
            with open('coach_image.jpg', 'wb') as f:
                f.write(response.content)
            print("✅ Downloaded your image successfully!")
            return 'coach_image.jpg'
        else:
            print(f"❌ Failed to download: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading image: {e}")
        return None

def check_talk_status(talk_id: str):
    """Check the status of a talk and get its video URL"""
    headers = {
        'Authorization': f'Basic {DID_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"\nChecking status for talk: {talk_id}")
        response = requests.get(f"{DID_BASE_URL}/talks/{talk_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            print(f"Status: {status}")
            
            if status == 'done':
                video_url = result.get('result_url')
                print("✅ Video is ready!")
                print(f"📺 Video URL: {video_url}")
                return video_url
            elif status == 'created' or status == 'started':
                print("⏳ Video is still processing...")
                return None
            else:
                print(f"❌ Unexpected status: {status}")
                return None
        else:
            print(f"❌ Failed to check status: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def wait_for_talk(talk_id: str, max_attempts: int = 30):
    """Wait for the talk to be ready and return the video URL"""
    print("\nWaiting for video to be ready...")
    
    for attempt in range(max_attempts):
        video_url = check_talk_status(talk_id)
        if video_url:
            return video_url
        elif attempt < max_attempts - 1:
            print(f"Waiting 5 seconds... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(5)
    
    print("❌ Timed out waiting for video")
    return None

def main():
    print("🚀 D-ID Avatar Creator - Multiple Approaches")
    
    # Check if we want to check an existing talk
    talk_id = input("\nEnter talk ID to check (or press Enter to create new): ").strip()
    
    if talk_id:
        # Check existing talk
        video_url = wait_for_talk(talk_id)
        if video_url:
            print("\n🎉 Your video is ready!")
            print(f"📺 Watch it here: {video_url}")
        return

    if not test_did_authentication():
        return
    
    print("\n=== APPROACH 1: Download and Upload Your Image ===")
    local_image = download_and_save_imgur_image()
    
    if local_image:
        print("Uploading your image to D-ID...")
        hosted_url = upload_local_image(local_image)
        
        if hosted_url:
            print("Creating avatar with your uploaded image...")
            result = create_avatar_with_image_url(hosted_url)
            if result:
                print("🎉 SUCCESS! Your custom coach avatar was created!")
                talk_id = result.get('id')
                if talk_id:
                    print("\nWaiting for your video to be ready...")
                    video_url = wait_for_talk(talk_id)
                    if video_url:
                        print("\n🎉 Your video is ready!")
                        print(f"📺 Watch it here: {video_url}")
                return

    print("\n=== APPROACH 2: Test with Working Images ===")
    result = try_alternative_image_urls()
    if result:
        print("🎉 Avatar creation working! Now you know the format works.")
        print("💡 Try uploading your image to Google Drive, Dropbox, or another service")
        print("   and make it publicly accessible, then use that URL.")
        return
    
    print("\n=== MANUAL SOLUTION ===")
    print("If both approaches failed, here's what to do:")
    print("1. Save your image from: https://i.imgur.com/z4CH5gt.jpeg")
    print("2. Upload it to Google Drive or Dropbox")
    print("3. Make it publicly shareable")
    print("4. Get the direct download link")
    print("5. Use that link in the script")
    print("\nOr place your image in this folder as 'my_coach.jpg' and run:")
    print("python create_coach_agent.py")

if __name__ == "__main__":
    main()