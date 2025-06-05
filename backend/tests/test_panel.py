import asyncio
import os
from datetime import datetime
from services.football_service import FootballService
from services.panel_service import PanelService

async def main():
    # Initialize services
    football_service = FootballService()
    panel_service = PanelService()
    
    # Get match data
    match_id = "1374812"  # PSG vs Inter
    match_data = await football_service.update_match_data(match_id)
    
    if not match_data:
        raise ValueError("No match data available")
    
    # Print match info
    home_team = match_data["match_info"]["teams"]["home"]["name"]
    away_team = match_data["match_info"]["teams"]["away"]["name"]
    print(f"\nStarting panel discussion for {home_team} vs {away_team}\n")
    
    # Start the discussion
    discussion_task = asyncio.create_task(panel_service.start_discussion(match_id, match_data))
    
    # Let the discussion run for a while
    await asyncio.sleep(30)
    
    # Stop the discussion
    panel_service.stop_discussion()
    
    # Get the discussion history
    history = await panel_service.get_discussion_history()
    
    # Print the discussion
    print("\nPanel Discussion:")
    print("=" * 80)
    
    for point in history:
        timestamp = datetime.fromisoformat(point["timestamp"]).strftime("%H:%M:%S")
        agent_type = point["agent_type"].upper()
        content = point["content"]
        is_interruption = point.get("is_interruption", False)
        responding_to = point.get("responding_to", "")
        
        if is_interruption:
            print(f"\n[{timestamp}] {agent_type} (interrupting {responding_to.upper()}):")
        else:
            print(f"\n[{timestamp}] {agent_type}:")
        
        print(content)
        print("-" * 80)
    
    # Print audio file information
    print("\nAudio Files Generated:")
    print("=" * 80)
    for point in history:
        if "audio_file" in point:
            print(f"{point['agent_type'].upper()}: {point['audio_file']}")

if __name__ == "__main__":
    asyncio.run(main()) 