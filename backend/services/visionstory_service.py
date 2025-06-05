"""
Service for handling video generation using VisionStory API
"""
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv
import time
import json

class VisionStoryService:
    def __init__(self):
        # Get the absolute path to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_dir, '.env')
        
        # Load environment variables from the .env file
        load_dotenv(env_path)
        
        self.api_key = os.getenv("VISIONSTORY_API_KEY")
        if not self.api_key:
            raise ValueError("VISIONSTORY_API_KEY not found in environment variables")
            
        self.base_url = "https://api.visionstory.ai"
        
        # Use the same avatar configurations
        self.avatar_configs = {
            "Show Host": {
                "image_url": "https://i.imgur.com/p1reirZ.jpeg",
                "voice_id": "en-US-JennyNeural"
            },
            "Football Coach": {
                "image_url": "https://i.imgur.com/z4CH5gt.jpeg",
                "voice_id": "en-AU-WilliamNeural"
            },
            "Stats Analyst": {
                "image_url": "https://i.imgur.com/FgSDbBC.png",
                "voice_id": "en-GB-RyanNeural"
            },
            "Home Fan": {
                "image_url": "https://i.imgur.com/DDIfv5v.png",
                "voice_id": "en-US-GuyNeural"
            },
            "Away Fan": {
                "image_url": "https://readyplayer.me/gallery/63e51f6f24053a9546906543",  # Standard girl avatar
                "voice_id": "en-US-AriaNeural"  # More casual, younger-sounding voice
            }
        }
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for VisionStory API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def create_video(self, text: str, agent_type: str) -> Optional[str]:
        """Create a video using VisionStory API"""
        try:
            config = self.avatar_configs.get(agent_type)
            if not config:
                print(f"No avatar configuration found for {agent_type}")
                return None
                
            # Create video request
            response = requests.post(
                f"{self.base_url}/v1/videos",
                headers=self.get_headers(),
                json={
                    "text": text,
                    "avatar": {
                        "image_url": config["image_url"],
                        "voice": {
                            "provider": "microsoft",
                            "voice_id": config["voice_id"],
                            "settings": {
                                "rate": 1.2,  # Speak 20% faster
                                "style": "chat",  # More casual speaking style
                                "pitch": 1.1  # Slightly higher pitch for more energy
                            }
                        }
                    },
                    "output": {
                        "format": "mp4",
                        "quality": "high"
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"Error creating video: {response.text}")
                return None
                
            # Get video ID from response
            video_id = response.json().get("id")
            if not video_id:
                print("No video ID in response")
                return None
                
            # Wait for video to be ready
            video_url = await self._wait_for_video(video_id)
            if not video_url:
                print("Failed to get video URL")
                return None
                
            # Download video
            video_path = await self._download_video(video_url, agent_type)
            return video_path
            
        except Exception as e:
            print(f"Error in create_video: {e}")
            return None
            
    async def _wait_for_video(self, video_id: str, max_attempts: int = 30) -> Optional[str]:
        """Wait for video to be ready and return download URL"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/v1/videos/{video_id}",
                    headers=self.get_headers()
                )
                
                if response.status_code != 200:
                    print(f"Error checking video status: {response.text}")
                    return None
                    
                status = response.json().get("status")
                if status == "completed":
                    return response.json().get("url")
                elif status == "failed":
                    print("Video generation failed")
                    return None
                    
                print(f"Video status: {status} (attempt {attempt + 1}/{max_attempts})")
                time.sleep(5)
                
            except Exception as e:
                print(f"Error checking video status: {e}")
                return None
                
        print("Timeout waiting for video")
        return None
        
    async def _download_video(self, url: str, agent_type: str) -> Optional[str]:
        """Download video from URL and save to file"""
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error downloading video: {response.status_code}")
                return None
                
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), "videos")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save video with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{agent_type}_{timestamp}.mp4"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            print(f"Video saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None 