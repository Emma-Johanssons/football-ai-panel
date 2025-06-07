import requests
import json
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["ELEVENLABS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these variables in your .env file")
        return False
    return True

def test_panel_video():
    """Test the panel video generation endpoint"""
    if not check_environment():
        sys.exit(1)
        
    url = "http://localhost:5000/api/generate-panel-video"
    
    # Test data
    data = {
        "match_id": "test_match",
        "match_info": {
            "teams": {
                "home": {"name": "Manchester United", "score": 2},
                "away": {"name": "Liverpool", "score": 1}
            },
            "time": "75:00",
            "status": "in_progress"
        }
    }
    
    try:
        print("Checking if backend server is running...")
        health_check = requests.get("http://localhost:5000/api/agents")
        if health_check.status_code != 200:
            print("Error: Backend server is not responding correctly")
            print("Response:", health_check.text)
            return
            
        print("Generating panel discussion video...")
        print("Sending request with data:", json.dumps(data, indent=2))
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Save the video
            output_path = "output/test_panel_discussion.mp4"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Video generated successfully! Saved as {output_path}")
        else:
            print(f"Error: {response.status_code}")
            print("Response:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the backend server. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_panel_video() 