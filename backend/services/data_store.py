"""
Data storage and retrieval service for match data
"""
import os
import json
from typing import Dict, Optional, List

class DataStore:
    def __init__(self):
        # Use match_data folder in the root directory
        self.data_dir = os.path.join("match_data")
        self.cache_dir = os.path.join("cache")
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
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
            # Try root directory first
            file_path = os.path.join(self.data_dir, f"match_{match_id}.json")
            
            # If not found, try backend directory
            if not os.path.exists(file_path):
                file_path = os.path.join("backend", "match_data", f"match_{match_id}.json")
                
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
        # Check both root and backend directories
        root_path = os.path.join(self.data_dir, f"match_{match_id}.json")
        backend_path = os.path.join("backend", "match_data", f"match_{match_id}.json")
        return os.path.exists(root_path) or os.path.exists(backend_path)

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