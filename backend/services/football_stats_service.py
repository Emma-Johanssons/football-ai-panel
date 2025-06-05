import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FootballStatsService:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        if not self.api_key:
            raise ValueError("FOOTBALL_API_KEY not found in environment variables")
            
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }
    
    def get_fixture_details(self, fixture_id: int) -> Dict:
        """Get comprehensive fixture details including lineups and events"""
        response = requests.get(
            f"{self.base_url}/fixtures",
            headers=self.headers,
            params={
                "id": fixture_id
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [{}])[0]
        return {}
    
    def get_fixture_lineups(self, fixture_id: int) -> Dict:
        """Get detailed lineups for a specific fixture"""
        response = requests.get(
            f"{self.base_url}/fixtures/lineups",
            headers=self.headers,
            params={
                "fixture": fixture_id
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        """Get all events from a specific fixture"""
        response = requests.get(
            f"{self.base_url}/fixtures/events",
            headers=self.headers,
            params={
                "fixture": fixture_id
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Dict:
        """Get comprehensive team statistics for a specific season"""
        response = requests.get(
            f"{self.base_url}/teams/statistics",
            headers=self.headers,
            params={
                "team": team_id,
                "league": league_id,
                "season": season
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", {})
        return {}
    
    def get_team_form(self, team_id: int, last: int = 5) -> List[Dict]:
        """Get team's recent form and results"""
        response = requests.get(
            f"{self.base_url}/fixtures",
            headers=self.headers,
            params={
                "team": team_id,
                "last": last,
                "status": "FT"
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_head_to_head(self, team1_id: int, team2_id: int, last: int = 5) -> List[Dict]:
        """Get head to head matches between two teams"""
        response = requests.get(
            f"{self.base_url}/fixtures/headtohead",
            headers=self.headers,
            params={
                "h2h": f"{team1_id}-{team2_id}",
                "last": last
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_player_statistics(self, player_id: int, season: int) -> Dict:
        """Get comprehensive player statistics for a season"""
        response = requests.get(
            f"{self.base_url}/players",
            headers=self.headers,
            params={
                "id": player_id,
                "season": season
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [{}])[0]
        return {}
    
    def get_player_form(self, player_id: int, last: int = 5) -> List[Dict]:
        """Get player's recent form and performances"""
        response = requests.get(
            f"{self.base_url}/fixtures",
            headers=self.headers,
            params={
                "player": player_id,
                "last": last
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_team_players(self, team_id: int, season: int) -> List[Dict]:
        """Get all players from a team for a specific season"""
        response = requests.get(
            f"{self.base_url}/players",
            headers=self.headers,
            params={
                "team": team_id,
                "season": season
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """Get detailed statistics for a specific fixture"""
        response = requests.get(
            f"{self.base_url}/fixtures/statistics",
            headers=self.headers,
            params={
                "fixture": fixture_id
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", [])
        return []
    
    def get_comprehensive_match_data(self, fixture_id: int) -> Dict:
        """Get all relevant data for a specific match"""
        # Get basic fixture details
        fixture_details = self.get_fixture_details(fixture_id)
        if not fixture_details:
            return {}
            
        # Extract team and league info
        teams = fixture_details.get("teams", {})
        league = fixture_details.get("league", {})
        
        home_team_id = teams.get("home", {}).get("id")
        away_team_id = teams.get("away", {}).get("id")
        league_id = league.get("id")
        season = league.get("season")
        
        # Get all relevant data
        return {
            "fixture": fixture_details,
            "lineups": self.get_fixture_lineups(fixture_id),
            "events": self.get_fixture_events(fixture_id),
            "statistics": self.get_fixture_statistics(fixture_id),
            "team_stats": {
                "home": self.get_team_statistics(home_team_id, league_id, season),
                "away": self.get_team_statistics(away_team_id, league_id, season)
            },
            "team_form": {
                "home": self.get_team_form(home_team_id),
                "away": self.get_team_form(away_team_id)
            },
            "h2h_history": self.get_head_to_head(home_team_id, away_team_id),
            "players": {
                "home": self.get_team_players(home_team_id, season),
                "away": self.get_team_players(away_team_id, season)
            }
        }
    
    def get_match_statistics(self, match_id: str) -> Optional[Dict]:
        """Get detailed match statistics"""
        try:
            # Get match statistics
            response = requests.get(
                f"{self.base_url}/fixtures/statistics",
                headers=self.headers,
                params={"fixture": match_id}
            )
            
            if response.status_code != 200:
                print(f"Error fetching match statistics: {response.status_code}")
                return None
                
            data = response.json()
            if not data.get("response"):
                print("No statistics data found in response")
                return None
            
            # Process and structure the statistics
            stats = {"home": {}, "away": {}}
            
            # The response is a list of team statistics
            for team_stats in data["response"]:
                # Determine if this is home or away team
                team_type = "home" if team_stats.get("team", {}).get("id") == data["response"][0].get("team", {}).get("id") else "away"
                
                # Extract statistics from the response
                team_statistics = {}
                for stat in team_stats.get("statistics", []):
                    if stat.get("type") == "Ball Possession":
                        team_statistics["possession"] = stat.get("value", "0%").replace("%", "")
                    elif stat.get("type") == "Total Shots":
                        team_statistics["shots"] = {"total": stat.get("value", 0)}
                    elif stat.get("type") == "Shots on Goal":
                        if "shots" not in team_statistics:
                            team_statistics["shots"] = {"total": 0}
                        team_statistics["shots"]["on"] = stat.get("value", 0)
                    elif stat.get("type") == "Total Passes":
                        team_statistics["passes"] = {"total": stat.get("value", 0)}
                    elif stat.get("type") == "Passes Accurate":
                        if "passes" not in team_statistics:
                            team_statistics["passes"] = {"total": 0}
                        team_statistics["passes"]["accuracy"] = stat.get("value", 0)
                    elif stat.get("type") == "Corner Kicks":
                        team_statistics["corners"] = stat.get("value", 0)
                    elif stat.get("type") == "Fouls":
                        team_statistics["fouls"] = stat.get("value", 0)
                    elif stat.get("type") == "Yellow Cards":
                        team_statistics["cards"] = {"yellow": stat.get("value", 0), "red": 0}
                    elif stat.get("type") == "Red Cards":
                        if "cards" not in team_statistics:
                            team_statistics["cards"] = {"yellow": 0}
                        team_statistics["cards"]["red"] = stat.get("value", 0)
                    elif stat.get("type") == "Formation":
                        team_statistics["formation"] = stat.get("value", "Unknown")
                    elif stat.get("type") == "Goals":
                        team_statistics["goals"] = {"total": stat.get("value", 0)}
                
                # Ensure all required fields exist with default values
                if "shots" not in team_statistics:
                    team_statistics["shots"] = {"total": 0, "on": 0}
                if "passes" not in team_statistics:
                    team_statistics["passes"] = {"total": 0, "accuracy": 0}
                if "cards" not in team_statistics:
                    team_statistics["cards"] = {"yellow": 0, "red": 0}
                if "goals" not in team_statistics:
                    team_statistics["goals"] = {"total": 0}
                if "possession" not in team_statistics:
                    team_statistics["possession"] = "0"
                if "corners" not in team_statistics:
                    team_statistics["corners"] = 0
                if "fouls" not in team_statistics:
                    team_statistics["fouls"] = 0
                if "formation" not in team_statistics:
                    team_statistics["formation"] = "Unknown"
                
                stats[team_type] = team_statistics
            
            return stats
            
        except Exception as e:
            print(f"Error in get_match_statistics: {e}")
            return None 