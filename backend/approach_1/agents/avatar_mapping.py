"""
Mapping of agent roles to their D-ID avatar URLs and voice settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AVATAR_MAPPING = {
    "Show Host": {
        "image_url": os.getenv('HOST_AVATAR_URL', 'https://i.imgur.com/p1reirZ.jpeg'),
        "s3_url": os.getenv('HOST_AVATAR_S3_URL'),
        "voice_id": "en-US-JennyNeural"
    },
    "Football Coach": {
        "image_url": os.getenv('COACH_AVATAR_URL', 'https://i.imgur.com/z4CH5gt.jpeg'),
        "s3_url": os.getenv('COACH_AVATAR_S3_URL'),
        "voice_id": "en-AU-WilliamNeural"  # Australian English voice for the coach
    },
    "Stats Analyst": {
        "image_url": os.getenv('STATS_AVATAR_URL', 'https://i.imgur.com/FgSDbBC.png'),
        "s3_url": os.getenv('STATS_AVATAR_S3_URL'),
        "voice_id": "en-GB-RyanNeural"  # British accent for the analyst
    },
    "Home Fan": {
        "image_url": os.getenv('HOME_FAN_AVATAR_URL', 'https://i.imgur.com/DDIfv5v.png'),
        "s3_url": os.getenv('HOME_FAN_AVATAR_S3_URL'),
        "voice_id": "en-US-GuyNeural"  # American accent for home fan
    },
    "Away Fan": {
        "image_url": os.getenv('AWAY_FAN_AVATAR_URL', 'https://i.imgur.com/W1uJkwm.png'),
        "s3_url": os.getenv('AWAY_FAN_AVATAR_S3_URL'),
        "voice_id": "en-GB-RyanNeural"  # British accent for away fan
    }
}

def get_avatar_config(role: str) -> dict:
    """Get avatar configuration for a given role"""
    config = AVATAR_MAPPING.get(role)
    if not config:
        raise ValueError(f"No avatar configuration found for role: {role}")
    return config 