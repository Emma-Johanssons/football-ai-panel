import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AvatarCreator:
    def __init__(self):
        self.did_api_key = os.getenv('DID_API_KEY')
        self.did_base_url = "https://api.d-id.com"
        
    def download_and_save_image(self, image_url: str) -> str:
        """Download image from URL and save locally"""
        try:
            # Try different user agents to bypass blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Save the image locally
                local_path = 'temp_avatar.jpg'
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print("✅ Downloaded image successfully!")
                return local_path
            else:
                print(f"❌ Failed to download: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return None
    
    def create_avatar(self, image_url: str, voice_id: str = "sv-SE-MattiasNeural") -> str:
        """Create a new avatar using D-ID API and return the S3 URL"""
        if not self.did_api_key:
            raise ValueError("DID_API_KEY is not set in environment variables")
            
        # First download the image
        print(f"Downloading image from: {image_url}")
        local_image = self.download_and_save_image(image_url)
        if not local_image:
            raise ValueError("Failed to download image")
            
        # Upload to D-ID
        print("Uploading image to D-ID...")
        headers = {
            'Authorization': f'Basic {self.did_api_key}'
        }
        
        try:
            with open(local_image, 'rb') as f:
                files = {
                    'image': ('avatar.jpg', f, 'image/jpeg')
                }
                upload_response = requests.post(
                    f"{self.did_base_url}/images",
                    headers=headers,
                    files=files
                )
            
            # Clean up local file
            if os.path.exists(local_image):
                os.remove(local_image)
            
            if upload_response.status_code not in [200, 201]:
                raise ValueError(f"Failed to upload image: {upload_response.text}")
                
            # Get the S3 URL from the response
            s3_url = upload_response.json().get('url')
            if not s3_url:
                raise ValueError("No URL in upload response")
                
            print(f"✅ Image uploaded successfully to: {s3_url}")
            return s3_url
            
        except Exception as e:
            # Clean up local file in case of error
            if os.path.exists(local_image):
                os.remove(local_image)
            raise e
        
    def create_video(self, source_url: str, text: str, voice_id: str = "sv-SE-MattiasNeural") -> str:
        """Create a video using the avatar"""
        if not self.did_api_key:
            return None
            
        headers = {
            'Authorization': f'Basic {self.did_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id
                },
                "input": text
            }
        }
        
        try:
            print("Creating video response...")
            response = requests.post(f"{self.did_base_url}/talks", headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                talk_id = result.get('id')
                
                if talk_id:
                    # Wait for video to be ready
                    video_url = self.wait_for_video(talk_id)
                    if video_url:
                        return video_url
            
            print(f"❌ Failed to create video: {response.text}")
            return None
            
        except Exception as e:
            print(f"❌ Error creating video: {e}")
            return None
    
    def wait_for_video(self, talk_id: str, max_attempts: int = 30) -> str:
        """Wait for the video to be ready"""
        headers = {
            'Authorization': f'Basic {self.did_api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.did_base_url}/talks/{talk_id}", headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'done':
                        return result.get('result_url')
                    elif status in ['created', 'started']:
                        print(f"⏳ Video processing... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(5)
                    else:
                        print(f"❌ Unexpected status: {status}")
                        return None
                        
            except Exception as e:
                print(f"❌ Error checking video status: {e}")
                return None
        
        return None

def main():
    creator = AvatarCreator()
    
    # Avatar configurations for fans only
    avatars = [
        {
            "role": "Home Fan",
            "image_url": "https://i.imgur.com/DDIfv5v.png",
            "voice_id": "en-US-GuyNeural",
            "test_text": "Come on lads! We've got this! Our team is looking strong today!"
        },
        {
            "role": "Away Fan",
            "image_url": "https://i.imgur.com/W1uJkwm.png",
            "voice_id": "en-GB-RyanNeural",
            "test_text": "We're the away support and we're making ourselves heard! Come on you blues!"
        }
    ]
    
    # Create each avatar
    for avatar in avatars:
        try:
            print(f"\n=== Creating {avatar['role']} Avatar ===")
            s3_url = creator.create_avatar(avatar['image_url'])
            print(f"{avatar['role']} avatar S3 URL: {s3_url}")
            
            # Test video creation
            print(f"\n=== Testing {avatar['role']} Video Creation ===")
            video_url = creator.create_video(
                s3_url,
                avatar['test_text'],
                avatar['voice_id']
            )
            
            if video_url:
                print(f"\n✅ Success! Your {avatar['role']} avatar is ready!")
                print(f"📺 Watch the test video here: {video_url}")
                
                # Update avatar_mapping.py with the new S3 URL
                print(f"\nℹ️ Please update the S3 URL in avatar_mapping.py for {avatar['role']}:")
                print(f"\"s3_url\": \"{s3_url}\",")
            
        except Exception as e:
            print(f"❌ Error creating {avatar['role']} avatar: {e}")
            continue

if __name__ == "__main__":
    main() 