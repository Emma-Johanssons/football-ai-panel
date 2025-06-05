"""Service for storing and retrieving match data"""
import os
import json
from typing import Dict, Optional

class DataStore:
    def __init__(self):
        self.data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_match_data(self, match_id: str, data: Dict) -> None:
        """Save match data to a JSON file"""
        try:
            file_path = os.path.join(self.data_dir, f"match_{match_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Match data saved to {file_path}")
        except Exception as e:
            print(f"❌ Error saving match data: {e}")
    
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