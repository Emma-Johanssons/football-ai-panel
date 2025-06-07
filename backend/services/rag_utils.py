import os
import requests
import openai
import feedparser
from typing import Tuple, Dict, List

async def get_api_football_stats(match_id: str) -> Dict:
    """Get match statistics from API Football"""
    api_key = os.getenv("FOOTBALL_API_KEY")
    if not api_key:
        return {"error": "No API key set for API-Football."}
        
    try:
        # Fetch fixture info
        response = requests.get(
            f"https://v3.football.api-sports.io/fixtures?id={match_id}",
            headers={"x-apisports-key": api_key}
        )
        if response.status_code != 200:
            return {"error": f"API request failed: {response.text}"}
            
        response_data = response.json()
        if not response_data.get("response"):
            return {"error": "No response data from API."}
            
        raw_match_data = response_data["response"][0]
        
        # Extract basic match info
        home_team = raw_match_data["teams"]["home"]["name"]
        away_team = raw_match_data["teams"]["away"]["name"]
        score = raw_match_data.get("goals", {"home": 0, "away": 0})
        
        # Fetch comprehensive stats
        league_id = raw_match_data["league"]["id"]
        season = raw_match_data["league"]["season"]
        team_ids = [raw_match_data["teams"]["home"]["id"], raw_match_data["teams"]["away"]["id"]]
        
        stats = {}
        for i, team_id in enumerate(team_ids):
            team_type = "home" if i == 0 else "away"
            
            # Get team statistics
            stats_response = requests.get(
                f"https://v3.football.api-sports.io/teams/statistics",
                headers={"x-apisports-key": api_key},
                params={
                    "team": team_id,
                    "league": league_id,
                    "season": season
                }
            )
            
            if stats_response.status_code == 200:
                stats[team_type] = stats_response.json().get("response", {})
                
            # Get team form
            form_response = requests.get(
                f"https://v3.football.api-sports.io/fixtures",
                headers={"x-apisports-key": api_key},
                params={
                    "team": team_id,
                    "last": 5,
                    "status": "FT"
                }
            )
            
            if form_response.status_code == 200:
                stats[team_type]["recent_form"] = form_response.json().get("response", [])
        
        # Get head-to-head history
        h2h_response = requests.get(
            f"https://v3.football.api-sports.io/fixtures/headtohead",
            headers={"x-apisports-key": api_key},
            params={
                "h2h": f"{team_ids[0]}-{team_ids[1]}",
                "last": 5
            }
        )
        
        if h2h_response.status_code == 200:
            stats["h2h_history"] = h2h_response.json().get("response", [])
        
        return {
            "match_info": {
                "home_team": home_team,
                "away_team": away_team,
                "score": score,
                "league": raw_match_data["league"]["name"],
                "season": season
            },
            "statistics": stats
        }
        
    except Exception as e:
        print(f"Error fetching match stats: {str(e)}")
        return {}

async def get_football_rules() -> List[str]:
    """Get relevant football rules"""
    try:
        # Implement fetching rules from database or API
        return []
    except Exception as e:
        print(f"Error fetching rules: {str(e)}")
        return []

async def get_tactical_knowledge() -> List[str]:
    """Get tactical knowledge"""
    try:
        # Implement fetching tactical knowledge from database or API
        return []
    except Exception as e:
        print(f"Error fetching tactical knowledge: {str(e)}")
        return []

async def get_historical_context(home_team: str, away_team: str) -> List[str]:
    """Get historical context for teams"""
    try:
        # Implement fetching historical data from database or API
        return []
    except Exception as e:
        print(f"Error fetching historical context: {str(e)}")
        return []

async def rag_retrieve(match_id: str, query: str, role: str = None) -> Tuple[Dict, List[str], List[str], List[str]]:
    """Retrieve relevant information based on the query and role"""
    # Get match statistics
    stats = await get_api_football_stats(match_id)
    
    # Get role-specific knowledge
    rules = await get_football_rules() if role == "Stats Analyst" else []
    tactics = await get_tactical_knowledge() if role == "Football Coach" else []
    
    # Get historical context if we have team names
    historical = []
    if stats.get("match_info"):
        home_team = stats["match_info"]["home_team"]
        away_team = stats["match_info"]["away_team"]
        historical = await get_historical_context(home_team, away_team)
    
    return stats, rules, tactics, historical 