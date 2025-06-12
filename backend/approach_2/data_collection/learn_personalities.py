"""
Script to run the learning agent and analyze football panel shows
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from agents.learning_agent import LearningAgent
from data_collection.youtube_collector import YouTubeCollector

async def main():
    """Run the learning agent"""
    print("🎓 Starting personality learning process...")
    
    # Create learning data directories
    os.makedirs("learning_data/personalities", exist_ok=True)
    os.makedirs("learning_data/raw_data", exist_ok=True)
    os.makedirs("learning_data/processed_data", exist_ok=True)
    
    # Initialize and run learning agent
    collector = YouTubeCollector()
    agent = LearningAgent(collector)
    await agent.learn_from_shows(max_videos=5)
    
    print("\n✅ Learning process complete!")
    print("Personality profiles have been saved to learning_data/personalities/")

if __name__ == "__main__":
    asyncio.run(main()) 