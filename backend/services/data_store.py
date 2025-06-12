"""
Data storage and retrieval service for match data
"""
import os
import json
from typing import Dict, Optional, List

class DataStore:
    def __init__(self, data_dir: str = None):
        # Get the absolute path to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if data_dir:
            self.data_dir = data_dir
        else:
            # If no data_dir provided, use the default in approach_2 directory
            self.data_dir = os.path.join(backend_dir, "approach_2", "match_data")
            
        # Cache directory is always in the backend directory
        self.cache_dir = os.path.join(backend_dir, "cache")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print(f"Data directory: {self.data_dir}")
        print(f"Cache directory: {self.cache_dir}")
    
    def save_match_data(self, match_id: str, data: Dict) -> bool:
        """Save match data to JSON file"""
        try:
            file_path = os.path.join(self.data_dir, f"match_{match_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Successfully saved match data to {file_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving match data: {e}")
            return False
    
    def load_match_data(self, match_id: str) -> Optional[Dict]:
        """Load match data from JSON file"""
        try:
            file_path = os.path.join(self.data_dir, f"match_{match_id}.json")
            
            if not os.path.exists(file_path):
                print(f"❌ No data file found for match {match_id}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Match data loaded from {file_path}")
            return data
        except Exception as e:
            print(f"❌ Error loading match data: {e}")
            return None
    
    def match_data_exists(self, match_id: str) -> bool:
        """Check if match data exists"""
        file_path = os.path.join(self.data_dir, f"match_{match_id}.json")
        return os.path.exists(file_path)

    def save_cache_data(self, cache_type: str, teams: List[str], data: Dict) -> bool:
        """Save cache data (news, drama, etc)"""
        try:
            file_name = f"{cache_type}_{teams[0]}_{teams[1]}.json"
            file_path = os.path.join(self.cache_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving cache data: {e}")
            return False

    def load_cache_data(self, cache_type: str, teams: List[str]) -> Optional[Dict]:
        """Load cache data (news, drama, etc)"""
        try:
            file_name = f"{cache_type}_{teams[0]}_{teams[1]}.json"
            file_path = os.path.join(self.cache_dir, file_name)
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading cache data: {e}")
            return None

    async def get_match_data(self, match_id: str) -> dict:
        """Get match data for a specific match ID"""
        try:
            # Construct the path to the match data file
            match_file = os.path.join(self.data_dir, f"match_{match_id}.json")
            print(f"Looking for match data in: {match_file}")
            
            # Check if the file exists
            if not os.path.exists(match_file):
                print(f"❌ Match data file not found: {match_file}")
                return None
                
            # Read and parse the JSON file
            with open(match_file, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
                
            return match_data
            
        except Exception as e:
            print(f"❌ Error loading match data: {str(e)}")
            return None 