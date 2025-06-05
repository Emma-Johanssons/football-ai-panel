"""
Video manager for handling dynamic avatar transitions and video generation using VisionStory
"""
import os
import subprocess
import json
from typing import List, Dict
from datetime import datetime
import time
from services.visionstory_service import VisionStoryService
from ffmpeg_config import FFMPEG_EXECUTABLE  # Import FFmpeg configuration

class VideoManager:
    def __init__(self):
        self.segments = []
        # Convert temp_dir to absolute path
        self.temp_dir = os.path.abspath("temp_videos")
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create progress directory
        self.progress_dir = os.path.abspath("progress")
        os.makedirs(self.progress_dir, exist_ok=True)
        
        # Create checkpoint file
        self.checkpoint_file = os.path.join(self.progress_dir, "video_checkpoint.json")
        self._load_checkpoint()
        
        # Initialize VisionStory service
        self.visionstory = VisionStoryService()
        
        print(f"Initialized VideoManager with temp directory: {self.temp_dir}")
        
    def _load_checkpoint(self):
        """Load progress from checkpoint if it exists"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                    self.segments = checkpoint.get('segments', [])
                    print(f"✅ Restored {len(self.segments)} segments from checkpoint")
        except Exception as e:
            print(f"⚠️ Could not load checkpoint: {e}")
    
    def _save_checkpoint(self):
        """Save current progress to checkpoint"""
        try:
            checkpoint = {
                'segments': self.segments,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save checkpoint: {e}")
            
    def _save_progress(self, filepath: str, data: Dict):
        """Save progress data to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save progress: {e}")
            
    async def add_segment(self, speaker: str, content: str, avatar_config: Dict) -> str:
        """Create a video segment for a speaker with checkpointing"""
        # Check if this segment was already created
        for segment in self.segments:
            if (segment["speaker"] == speaker and 
                segment["content"] == content and 
                os.path.exists(segment["video_path"])):
                print(f"✅ Segment already exists for {speaker}, skipping...")
                return segment["video_path"]
        
        print(f"\n🎬 Creating video segment for {speaker}")
        print(f"Using avatar: {avatar_config['image_url']}")
        print(f"Using voice: {avatar_config['voice_id']}")
        
        progress_file = os.path.join(self.progress_dir, f"{speaker}_{int(time.time())}.json")
        
        if not isinstance(content, str):
            if isinstance(content, dict) and 'text' in content:
                content = content['text']
            else:
                raise ValueError(f"Content must be a string or a dict with 'text' key, got {type(content)}")
        
        try:
            # Save progress before starting
            self._save_progress(progress_file, {
                "speaker": speaker,
                "content": content,
                "avatar_config": avatar_config,
                "status": "starting",
                "timestamp": datetime.now().isoformat()
            })
            
            # Create video using VisionStory
            video_path = await self.visionstory.create_video(content, speaker)
            if not video_path:
                raise Exception("Failed to create video")
            
            # Add to segments list and save checkpoint
            segment_info = {
                "speaker": speaker,
                "content": content,
                "video_path": video_path,
                "timestamp": datetime.now().isoformat()
            }
            self.segments.append(segment_info)
            self._save_checkpoint()
            
            # Save successful progress
            self._save_progress(progress_file, {
                **segment_info,
                "status": "completed"
            })
            
            return video_path
            
        except Exception as e:
            print(f"❌ Error creating video segment: {e}")
            self._save_progress(progress_file, {
                "speaker": speaker,
                "content": content,
                "avatar_config": avatar_config,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
            
    def combine_videos(self, output_path: str) -> bool:
        """Combine all video segments into a single video"""
        if not self.segments:
            print("No segments to combine")
            return False
            
        try:
            # Create list of video files in chronological order
            video_files = []
            for segment in self.segments:
                if os.path.exists(segment["video_path"]):
                    video_files.append({
                        "path": segment["video_path"],
                        "speaker": segment["speaker"]
                    })
            
            if not video_files:
                print("No valid video files to combine")
                return False
                
            # Create file list for FFmpeg with speaker labels
            list_file = os.path.join(self.temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for video in video_files:
                    # Add speaker label as metadata
                    f.write(f"file '{video['path']}'\n")
                    f.write(f"metadata speaker={video['speaker']}\n")
                    
            # Combine videos using FFmpeg with metadata
            cmd = [
                FFMPEG_EXECUTABLE, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-map_metadata", "0",  # Keep metadata
                "-c", "copy",
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ Combined video saved to: {output_path}")
            
            # Save speaker timeline for reference
            timeline = {
                "segments": [
                    {
                        "speaker": v["speaker"],
                        "file": os.path.basename(v["path"])
                    } for v in video_files
                ]
            }
            with open(f"{output_path}.timeline.json", "w") as f:
                json.dump(timeline, f, indent=2)
            
            # Clean up list file
            os.remove(list_file)
            return True
            
        except Exception as e:
            print(f"❌ Error combining videos: {e}")
            return False 