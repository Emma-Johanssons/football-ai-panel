"""
Service for fetching and processing match statistics
"""
import aiohttp
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class StatsService:
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_API_KEY')
        self.base_url = "https://v3.football.api-sports.io"
        
    async def get_match_stats(self, match_id: str) -> Optional[Dict]:
        """Fetch match statistics from the API"""
        try:
            headers = {
                'x-apisports-key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                # Fetch match statistics
                async with session.get(
                    f"{self.base_url}/fixtures/statistics?fixture={match_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return None
                    stats_data = await response.json()
                    
                # Fetch player statistics
                async with session.get(
                    f"{self.base_url}/fixtures/players?fixture={match_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        players_data = await response.json()
                        stats_data["players"] = players_data.get("response", [])
                        
            return self._process_stats_data(stats_data)
            
        except Exception as e:
            print(f"Error fetching match statistics: {e}")
            return None
            
    def _process_stats_data(self, raw_data: Dict) -> Dict:
        """Process and format raw statistics data"""
        try:
            stats = raw_data.get("response", [])
            processed_stats = {"home": {}, "away": {}}
            
            for team_stats in stats:
                team_id = team_stats.get("team", {}).get("id")
                side = "home" if team_stats.get("team", {}).get("name") == team_stats.get("team", {}).get("name") else "away"
                
                # Process team statistics
                for stat in team_stats.get("statistics", []):
                    stat_type = stat.get("type")
                    stat_value = stat.get("value")
                    
                    # Convert percentage strings to numbers
                    if isinstance(stat_value, str) and "%" in stat_value:
                        stat_value = float(stat_value.strip("%"))
                        
                    processed_stats[side][stat_type] = stat_value
                    
            # Add player statistics if available
            if "players" in raw_data:
                for side in ["home", "away"]:
                    processed_stats[side]["player_stats"] = self._process_player_stats(
                        raw_data["players"],
                        side
                    )
                    
            # Calculate additional metrics
            for side in ["home", "away"]:
                team_stats = processed_stats[side]
                
                # Calculate shot accuracy
                total_shots = team_stats.get("Total Shots", 0)
                shots_on_target = team_stats.get("Shots on Goal", 0)
                if total_shots and total_shots > 0:
                    team_stats["shot_accuracy"] = (shots_on_target / total_shots) * 100
                    
                # Calculate pass accuracy
                total_passes = team_stats.get("Total Passes", 0)
                accurate_passes = team_stats.get("Accurate Passes", 0)
                if total_passes and total_passes > 0:
                    team_stats["pass_accuracy"] = (accurate_passes / total_passes) * 100
                    
                # Calculate expected goals (xG) - simplified version
                shots_inside_box = team_stats.get("Shots insidebox", 0)
                shots_outside_box = team_stats.get("Shots outsidebox", 0)
                if shots_inside_box is not None and shots_outside_box is not None:
                    team_stats["expected_goals"] = round(
                        (shots_inside_box * 0.12) + (shots_outside_box * 0.03),
                        2
                    )
                    
                # Calculate goals prevented (for goalkeepers)
                saves = team_stats.get("Goalkeeper Saves", 0)
                goals_conceded = team_stats.get("Goals Conceded", 0)
                if saves is not None and goals_conceded is not None:
                    team_stats["goals_prevented"] = round(
                        saves - goals_conceded,
                        2
                    )
                    
            return processed_stats
            
        except Exception as e:
            print(f"Error processing statistics data: {e}")
            return {}
            
    def _process_player_stats(self, players_data: list, side: str) -> Dict:
        """Process individual player statistics"""
        player_stats = {}
        
        for player in players_data:
            if player.get("team", {}).get("side") != side:
                continue
                
            player_id = player.get("player", {}).get("id")
            if not player_id:
                continue
                
            stats = player.get("statistics", [{}])[0]
            player_stats[player_id] = {
                "name": player.get("player", {}).get("name"),
                "position": stats.get("games", {}).get("position"),
                "minutes_played": stats.get("games", {}).get("minutes", 0),
                "rating": stats.get("games", {}).get("rating"),
                "goals": stats.get("goals", {}).get("total", 0),
                "assists": stats.get("goals", {}).get("assists", 0),
                "shots": stats.get("shots", {}).get("total", 0),
                "passes": stats.get("passes", {}).get("total", 0),
                "key_passes": stats.get("passes", {}).get("key", 0),
                "tackles": stats.get("tackles", {}).get("total", 0),
                "duels_won": stats.get("duels", {}).get("won", 0)
            }
            
        return player_stats 