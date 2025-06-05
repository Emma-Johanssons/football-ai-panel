import os
import yt_dlp
from typing import List, Dict
import json
from datetime import datetime
from .panelist_analyzer import PanelistAnalyzer

class YouTubeCollector:
    def __init__(self):
        self.learning_data_dir = os.getenv("LEARNING_DATA_DIR", "/app/learning_data")
        self.raw_data_dir = os.path.join(self.learning_data_dir, "raw_data")
        self.processed_data_dir = os.path.join(self.learning_data_dir, "processed_data")
        self.analyzer = PanelistAnalyzer()
        
        # Define known football panel shows and their panelists
        self.panel_shows = {
            "match_of_the_day": {
                "url": "https://www.youtube.com/@matchoftheday",
                "panelists": {
                    "host": ["Gary Lineker"],
                    "expert": ["Alan Shearer", "Ian Wright", "Micah Richards"],
                    "analyst": ["Jermaine Jenas", "Danny Murphy"]
                }
            },
            "monday_night_football": {
                "url": "https://www.youtube.com/@SkySportsPL",
                "panelists": {
                    "host": ["David Jones"],
                    "expert": ["Jamie Carragher", "Gary Neville"],
                    "analyst": ["Micah Richards", "Roy Keane"]
                }
            },
            "champions_league": {
                "url": "https://www.youtube.com/@UEFA",
                "panelists": {
                    "host": ["Peter Schmeichel"],
                    "expert": ["Rio Ferdinand", "Steve McManaman"],
                    "analyst": ["Owen Hargreaves", "Michael Owen"]
                }
            }
        }
    
    def download_video(self, url: str, output_path: str) -> str:
        """Download a YouTube video and extract audio"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return f"{output_path}.mp3"
    
    def collect_from_show(self, show_name: str, max_videos: int = 5) -> List[Dict]:
        """Collect data from a specific football panel show"""
        if show_name not in self.panel_shows:
            raise ValueError(f"Unknown show: {show_name}")
        
        show_info = self.panel_shows[show_name]
        results = []
        
        # Create show directory
        show_dir = os.path.join(self.raw_data_dir, show_name)
        os.makedirs(show_dir, exist_ok=True)
        
        # Download and analyze videos
        for i in range(max_videos):
            try:
                # Download video
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(show_dir, f"episode_{timestamp}")
                audio_file = self.download_video(show_info["url"], output_path)
                
                # Analyze each panelist's contribution
                for role, panelists in show_info["panelists"].items():
                    for panelist in panelists:
                        # Analyze the audio file
                        analysis = self.analyzer.analyze_audio_file(
                            audio_file,
                            f"{show_name}_{role}_{panelist.lower().replace(' ', '_')}"
                        )
                        results.append(analysis)
                
            except Exception as e:
                print(f"Error processing video {i+1}: {str(e)}")
                continue
        
        return results
    
    def collect_all_shows(self, max_videos_per_show: int = 5) -> Dict:
        """Collect data from all known football panel shows"""
        all_results = {}
        
        for show_name in self.panel_shows.keys():
            print(f"Collecting data from {show_name}...")
            results = self.collect_from_show(show_name, max_videos_per_show)
            all_results[show_name] = results
        
        return all_results
    
    def analyze_panelist(self, panelist_name: str) -> Dict:
        """Analyze a specific panelist's data across all shows"""
        results = []
        
        # Find all files containing the panelist's name
        for filename in os.listdir(self.processed_data_dir):
            if panelist_name.lower().replace(" ", "_") in filename.lower():
                with open(os.path.join(self.processed_data_dir, filename), 'r') as f:
                    results.append(json.load(f))
        
        if not results:
            return None
        
        # Aggregate the results
        return self.analyzer.aggregate_analysis(panelist_name)
    
    def get_panelist_statistics(self) -> Dict:
        """Get statistics for all panelists"""
        statistics = {}
        
        for show_name, show_info in self.panel_shows.items():
            for role, panelists in show_info["panelists"].items():
                for panelist in panelists:
                    panelist_key = f"{show_name}_{role}_{panelist.lower().replace(' ', '_')}"
                    analysis = self.analyze_panelist(panelist_key)
                    if analysis:
                        statistics[panelist_key] = analysis
        
        return statistics 