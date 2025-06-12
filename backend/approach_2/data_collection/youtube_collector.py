import os
import json
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import time
import random

class YouTubeCollector:
    def __init__(self):
        self.learning_data_dir = os.getenv("LEARNING_DATA_DIR", "learning_data")
        self.raw_data_dir = os.path.join(self.learning_data_dir, "raw_data")
        self.processed_data_dir = os.path.join(self.learning_data_dir, "processed_data")
        
        # Create directories if they don't exist
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        # Define known football analysis channels
        self.channels = {
            "tifo_football": {
                "id": "UCGYYNGmyhZ_kwBF_lqqXdAQ",
                "name": "Tifo Football",
                "panelists": ["Joe Devine", "Alex Stewart"]
            },
            "football_daily": {
                "id": "UCbWUEnTRHb3bRdrnovq8iuA",  # Updated correct ID
                "name": "Football Daily",
                "panelists": ["Patrick van Straaten", "Joe Thomlinson"]
            },
            "simply_soccer": {  # Added new channel instead of Football Made Simple
                "id": "UChsEBe5fZjkPaddgX_9uCNg",
                "name": "SimplySoccer",
                "panelists": ["Dylan", "Coach Matt"]
            }
        }

    def get_channel_feed(self, channel_id: str, max_results: int = 5) -> List[Dict]:
        """Get videos from a channel's RSS feed"""
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            print(f"\nFetching RSS feed for channel {channel_id}")
            response = requests.get(feed_url)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Define XML namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            # Extract videos
            videos = []
            for entry in root.findall('atom:entry', namespaces):
                if len(videos) >= max_results:
                    break
                
                # Get required fields with safe fallbacks
                title = entry.find('atom:title', namespaces)
                title_text = title.text if title is not None else "No title"
                
                video_id = entry.find('yt:videoId', namespaces)
                video_id_text = video_id.text if video_id is not None else None
                if not video_id_text:
                    continue
                
                published = entry.find('atom:published', namespaces)
                published_text = published.text if published is not None else datetime.now().isoformat()
                
                # Get description from media:group/media:description
                media_group = entry.find('media:group', namespaces)
                description = ""
                if media_group is not None:
                    desc_elem = media_group.find('media:description', namespaces)
                    if desc_elem is not None:
                        description = desc_elem.text or ""
                
                videos.append({
                    'id': video_id_text,
                    'title': title_text,
                    'description': description,
                    'url': f'https://www.youtube.com/watch?v={video_id_text}',
                    'published': published_text
                })
            
            if videos:
                print(f"Successfully fetched {len(videos)} videos")
            else:
                print("No videos found in feed")
            
            return videos
            
        except Exception as e:
            print(f"Error fetching channel feed: {str(e)}")
            return []

    def collect_channel_data(self, channel_name: str, max_videos: int = 5) -> List[Dict]:
        """Collect data from a specific channel"""
        if channel_name not in self.channels:
            print(f"Unknown channel: {channel_name}")
            return []
            
        channel = self.channels[channel_name]
        print(f"\nCollecting data from {channel['name']}...")
        
        try:
            # Get videos from RSS feed
            videos = self.get_channel_feed(channel['id'], max_videos)
            
            if not videos:
                print(f"No videos found for {channel['name']}")
                return []
                
            # Save video metadata
            channel_dir = os.path.join(self.raw_data_dir, channel_name)
            os.makedirs(channel_dir, exist_ok=True)
            
            results = []
            for video in videos:
                # Create metadata file
                metadata_file = os.path.join(channel_dir, f"{video['id']}_metadata.json")
                with open(metadata_file, 'w') as f:
                    json.dump({
                        'channel': channel['name'],
                        'video': video,
                        'panelists': channel['panelists'],
                        'collected_at': datetime.now().isoformat()
                    }, f, indent=2)
                    
                results.append({
                    'channel': channel['name'],
                    'video_id': video['id'],
                    'title': video['title'],
                    'url': video['url']
                })
                
                # Add delay between processing videos
                time.sleep(random.uniform(1, 3))
                
            print(f"Successfully processed {len(results)} videos from {channel['name']}")
            return results
            
        except Exception as e:
            print(f"Error collecting channel data: {str(e)}")
            return []

    def collect_all_channels(self, max_videos_per_channel: int = 5) -> Dict[str, List[Dict]]:
        """Collect data from all known channels"""
        all_results = {}
        
        for channel_name in self.channels:
            results = self.collect_channel_data(channel_name, max_videos_per_channel)
            all_results[channel_name] = results
            
            # Add delay between channels
            time.sleep(random.uniform(2, 5))
        
        return all_results

    def get_channel_statistics(self) -> Dict[str, Dict]:
        """Get statistics for all channels"""
        stats = {}
        
        for channel_name, channel in self.channels.items():
            channel_dir = os.path.join(self.raw_data_dir, channel_name)
            if not os.path.exists(channel_dir):
                continue
                
            video_count = len([f for f in os.listdir(channel_dir) if f.endswith('_metadata.json')])
            
            stats[channel_name] = {
                'name': channel['name'],
                'videos_collected': video_count,
                'panelists': channel['panelists']
            }
        
        return stats 