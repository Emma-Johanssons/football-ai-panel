from typing import Dict, List, Optional
import requests
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

class FootballService:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        if not self.api_key:
            raise ValueError("FOOTBALL_API_KEY not found in environment variables")
            
        self.base_url = os.getenv("API_BASE_URL", "https://v3.football.api-sports.io")
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        self.match_data = {}
        self.last_update = None
        self.update_interval = 60  # seconds
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the API-Football endpoint"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def _extract_team_stats(self, stats_data: Dict) -> Dict:
        """Extract relevant team statistics from API response"""
        if not stats_data.get("response"):
            return {}
            
        stats = stats_data["response"]
        return {
            "form": stats.get("form", ""),
            "fixtures": stats.get("fixtures", {}),
            "goals": stats.get("goals", {}),
            "clean_sheet": stats.get("clean_sheet", {}),
            "failed_to_score": stats.get("failed_to_score", {}),
            "lineups": stats.get("lineups", []),
            "cards": stats.get("cards", {})
        }
    
    def _extract_match_stats(self, stats_data: Dict) -> Dict:
        """Extract relevant match statistics from API response"""
        if not stats_data.get("response"):
            return {}
            
        stats = stats_data["response"]
        return {
            "possession": stats.get("possession", {}),
            "shots": stats.get("shots", {}),
            "expected_goals": stats.get("expected_goals", {}),
            "passes": stats.get("passes", {}),
            "pressures": stats.get("pressures", {}),
            "cards": stats.get("cards", {}),
            "fouls": stats.get("fouls", {})
        }
    
    def get_match_info(self, match_id: int) -> Dict:
        """Get basic match information"""
        endpoint = f"fixtures?id={match_id}"
        return self._make_request(endpoint)
    
    def get_match_statistics(self, match_id: int) -> Dict:
        """Get detailed match statistics"""
        endpoint = f"fixtures/statistics?fixture={match_id}"
        return self._make_request(endpoint)
    
    def get_lineups(self, match_id: int) -> Dict:
        """Get team lineups"""
        endpoint = f"fixtures/lineups?fixture={match_id}"
        return self._make_request(endpoint)
    
    def get_h2h(self, team1_id: int, team2_id: int) -> Dict:
        """Get head-to-head statistics"""
        endpoint = f"fixtures/headtohead?h2h={team1_id}-{team2_id}"
        return self._make_request(endpoint)
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Dict:
        """Get team statistics for a specific season"""
        endpoint = f"teams/statistics?team={team_id}&league={league_id}&season={season}"
        return self._make_request(endpoint)
    
    def get_team_last_matches(self, team_id: int, last: int = 5) -> Dict:
        """Get team's last N matches"""
        endpoint = f"fixtures?team={team_id}&last={last}"
        return self._make_request(endpoint)
    
    def get_player_statistics(self, player_id: int, season: int) -> Dict:
        """Get player statistics for a specific season"""
        endpoint = f"players/statistics?player={player_id}&season={season}"
        return self._make_request(endpoint)
    
    def get_team_players(self, team_id: int, season: int) -> Dict:
        """Get all players in a team for a specific season"""
        endpoint = f"players?team={team_id}&season={season}"
        return self._make_request(endpoint)
    
    def update_match_data(self, match_id: int) -> None:
        """Update all match data"""
        current_time = time.time()
        
        # Only update if enough time has passed since last update
        if (self.last_update is None or 
            current_time - self.last_update > self.update_interval):
            
            try:
                # Get basic match info first
                match_info = self.get_match_info(match_id)
                if not match_info.get("response"):
                    raise ValueError("No match data found")
                
                match_data = match_info["response"][0]
                home_team_id = match_data["teams"]["home"]["id"]
                away_team_id = match_data["teams"]["away"]["id"]
                season = match_data["league"]["season"]
                league_id = match_data["league"]["id"]
                
                # Get all relevant data
                raw_data = {
                    "match_info": match_info,
                    "statistics": self.get_match_statistics(match_id),
                    "lineups": self.get_lineups(match_id),
                    "h2h": self.get_h2h(home_team_id, away_team_id),
                    "home_team_stats": self.get_team_statistics(home_team_id, league_id, season),
                    "away_team_stats": self.get_team_statistics(away_team_id, league_id, season),
                    "home_team_last_matches": self.get_team_last_matches(home_team_id),
                    "away_team_last_matches": self.get_team_last_matches(away_team_id),
                    "home_team_players": self.get_team_players(home_team_id, season),
                    "away_team_players": self.get_team_players(away_team_id, season)
                }
                
                # Process and format the data
                self.match_data = {
                    "match_info": match_data,
                    "statistics": self._extract_match_stats(raw_data["statistics"]),
                    "lineups": raw_data["lineups"].get("response", []),
                    "h2h": raw_data["h2h"].get("response", []),
                    "home_team_stats": self._extract_team_stats(raw_data["home_team_stats"]),
                    "away_team_stats": self._extract_team_stats(raw_data["away_team_stats"]),
                    "home_team_last_matches": raw_data["home_team_last_matches"].get("response", []),
                    "away_team_last_matches": raw_data["away_team_last_matches"].get("response", []),
                    "home_team_players": raw_data["home_team_players"].get("response", []),
                    "away_team_players": raw_data["away_team_players"].get("response", [])
                }
                
                self.last_update = current_time
                
            except Exception as e:
                print(f"Error updating match data: {e}")
                raise
    
    def get_data_for_agent(self, agent_type: str) -> Dict:
        """Get relevant data for a specific agent type"""
        if not self.match_data:
            return {}
            
        data_mapping = {
            "stats": {
                "match_statistics": self.match_data["statistics"],
                "home_team_stats": self.match_data["home_team_stats"],
                "away_team_stats": self.match_data["away_team_stats"],
                "h2h": self.match_data["h2h"],
                "home_team_last_matches": self.match_data["home_team_last_matches"],
                "away_team_last_matches": self.match_data["away_team_last_matches"]
            },
            "coach": {
                "formation": self.match_data["lineups"],
                "team_stats": {
                    "home": self.match_data["home_team_stats"],
                    "away": self.match_data["away_team_stats"]
                },
                "player_stats": {
                    "home": self.match_data["home_team_players"],
                    "away": self.match_data["away_team_players"]
                },
                "h2h": self.match_data["h2h"],
                "recent_form": {
                    "home": self.match_data["home_team_last_matches"],
                    "away": self.match_data["away_team_last_matches"]
                }
            },
            "referee": {
                "match_info": self.match_data["match_info"],
                "statistics": self.match_data["statistics"],
                "h2h": self.match_data["h2h"]
            },
            "fan": {
                "match_info": self.match_data["match_info"],
                "statistics": self.match_data["statistics"],
                "h2h": self.match_data["h2h"],
                "team_stats": {
                    "home": self.match_data["home_team_stats"],
                    "away": self.match_data["away_team_stats"]
                },
                "recent_form": {
                    "home": self.match_data["home_team_last_matches"],
                    "away": self.match_data["away_team_last_matches"]
                }
            }
        }
        
        return data_mapping.get(agent_type, {}) 