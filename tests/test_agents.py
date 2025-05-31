import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.football_service import FootballService
from agents.stats_agent import StatsAgent
from agents.coach_agent import CoachAgent
from agents.referee_agent import RefereeAgent
from agents.fan_agent import FanAgent
from agents.host_agent import HostAgent

def log_data(data: dict, agent_type: str):
    """Log data to a file for debugging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    filename = f"{log_dir}/{agent_type}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Logged data to {filename}")

def test_agents():
    # Initialize the football service
    football_service = FootballService()
    
    # Champions League final match ID
    match_id = 1374812
    
    try:
        # Update match data
        print("Fetching match data...")
        football_service.update_match_data(match_id)
        
        # Initialize all agents
        stats_agent = StatsAgent()
        coach_agent = CoachAgent()
        referee_agent = RefereeAgent()
        fan_agent = FanAgent()
        host_agent = HostAgent()
        
        # Get data for each agent
        stats_data = football_service.get_data_for_agent("stats")
        coach_data = football_service.get_data_for_agent("coach")
        referee_data = football_service.get_data_for_agent("referee")
        fan_data = football_service.get_data_for_agent("fan")
        
        # Log the data for each agent
        print("\nLogging data for each agent...")
        log_data(stats_data, "stats")
        log_data(coach_data, "coach")
        log_data(referee_data, "referee")
        log_data(fan_data, "fan")
        
        # Test each agent
        print("\n=== Testing Stats Agent ===")
        stats_response = stats_agent.analyze(stats_data)
        print(stats_response)
        
        print("\n=== Testing Coach Agent ===")
        coach_response = coach_agent.analyze(coach_data)
        print(coach_response)
        
        print("\n=== Testing Referee Agent ===")
        referee_response = referee_agent.analyze(referee_data)
        print(referee_response)
        
        print("\n=== Testing Fan Agent ===")
        fan_response = fan_agent.analyze(fan_data)
        print(fan_response)
        
        # Test host agent with panel context
        panel_context = {
            "current_topic": "Match Analysis",
            "time_elapsed": "45 minutes",
            "last_speaker": "Stats Agent",
            "key_points": [stats_response, coach_response, referee_response, fan_response],
            "panel_members": ["Stats Agent", "Coach Agent", "Referee Agent", "Fan Agent"]
        }
        
        print("\n=== Testing Host Agent ===")
        host_response = host_agent.analyze(panel_context)
        print(host_response)
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_agents() 