"""
Stats expert agent for panel discussions
"""
from typing import Dict, List, Any
from .base_agent import BaseAgent
import random
import re

class StatsAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Stats Expert"
        role = "Stats Expert"  
        system_prompt = """You are a football statistics expert. Your job is to:
1. Share relevant statistics that relate to what others are saying
2. Explain what the numbers mean in simple terms
3. Point out interesting statistical patterns
4. Keep responses short and focused on stats
5. Always mention specific player names from the actual match data
6. Never start responses with phrases like "as a stats expert" or "based on statistics"
7. Use varied introductions for statistical analysis

Always tie your statistics to what others are discussing and to specific players from the match."""
        
        personality = "analytical but clear"
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        # Initialize varied intro phrases
        self.intro_phrases = [
            "The numbers tell an interesting story here",
            "Looking at the match statistics",
            "A fascinating pattern emerges in the data",
            "Breaking down the key metrics",
            "The performance data shows",
            "Diving into the numbers",
            "What stands out in the statistics",
            "A closer look at the metrics reveals"
        ]
        
        # Track which stats we've mentioned
        self.mentioned_stats = {
            "possession": False,
            "shots": False,
            "passes": False,
            "tackles": False
        }
        
        # Initialize content tracking
        self.content_tracking = {
            "used_stats": set(),  # Track discussed statistics
            "mentioned_players": set(),  # Track discussed players
            "analyzed_events": set(),  # Track analyzed match events
            "used_comparisons": set()  # Track used statistical comparisons
        }
        
        # Initialize stat categories for organized access
        self.stat_categories = {
            "possession": ["possession", "touches", "passes"],
            "attack": ["shots", "goals", "xG", "big_chances"],
            "defense": ["tackles", "interceptions", "clearances"],
            "individual": ["player_stats", "heatmaps", "ratings"],
            "tactical": ["formation_success", "pressing_stats", "buildup_stats"]
        }
        
    def _get_intro_phrase(self) -> str:
        """Get a random introduction phrase"""
        return random.choice(self.intro_phrases)
        
    def _get_player_by_stat(self, match_data: dict, team: str, stat_name: str) -> tuple:
        """Get player with highest stat value and their stat value"""
        try:
            # Get player stats from match data
            player_stats = match_data.get("match_info", {}).get("player_stats", {}).get(team, [])
            if not player_stats:
                return None, 0
                
            # Find player with highest stat
            best_player = None
            best_value = 0
            
            for player in player_stats:
                stats = player.get("statistics", [{}])[0]  # Get first statistics entry
                
                # Handle nested stats (e.g., shots.total, passes.accuracy)
                if "." in stat_name:
                    category, substat = stat_name.split(".")
                    value = stats.get(category, {}).get(substat, 0)
                else:
                    value = stats.get(stat_name, 0)
                    
                # Convert string numbers to float
                try:
                    value = float(value) if value else 0
                except (ValueError, TypeError):
                    value = 0
                    
                if value > best_value:
                    best_value = value
                    best_player = player.get("name")
                    
            return best_player, best_value
            
        except Exception as e:
            print(f"Error getting player by stat: {e}")
            return None, 0
            
    async def analyze_match(self, match_data: dict) -> str:
        """Analyze match from a statistical perspective"""
        try:
            # Start with a varied intro
            analysis = self._get_intro_phrase() + ". "
            
            # Get team info
            teams = match_data.get("match_info", {}).get("teams", {})
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            
            # Get key statistics
            stats = match_data.get("details", {}).get("team_stats", {})
            possession = stats.get("possession", {"home": 50, "away": 50})
            shots = stats.get("shots", {"home": 0, "away": 0})
            shots_on_target = stats.get("shots_on_target", {"home": 0, "away": 0})
            
            # Get key players with their stats
            top_shooter_name, top_shots = self._get_player_by_stat(match_data, "home", "shots.total")
            top_passer_name, top_passes = self._get_player_by_stat(match_data, "home", "passes.total")
            top_rating_name, top_rating = self._get_player_by_stat(match_data, "home", "games.rating")
            
            # Build analysis with player names
            if top_shooter_name and top_passer_name:
                analysis += (
                    f"{home_team} dominated possession with {possession['home']}%, "
                    f"led by {top_passer_name}'s {int(top_passes)} completed passes. "
                    f"{top_shooter_name} was particularly active with {int(top_shots)} shots "
                    f"as {home_team} recorded {shots['home']} attempts ({shots_on_target['home']} on target)."
                )
                
                if top_rating_name:
                    analysis += f" {top_rating_name} was outstanding with a rating of {top_rating}."
            else:
                analysis += (
                    f"{home_team} controlled {possession['home']}% of possession "
                    f"and created {shots['home']} shooting opportunities "
                    f"({shots_on_target['home']} on target)."
                )
            
            # Add away team stats with player names
            away_shooter_name, away_shots = self._get_player_by_stat(match_data, "away", "shots.total")
            away_rating_name, away_rating = self._get_player_by_stat(match_data, "away", "games.rating")
            
            if away_shooter_name:
                analysis += f" For {away_team}, {away_shooter_name} managed {int(away_shots)} attempts"
                if away_rating_name:
                    analysis += f", while {away_rating_name} showed good form with a {away_rating} rating."
                else:
                    analysis += "."
                    
            return analysis
            
        except Exception as e:
            print(f"Error in statistical analysis: {e}")
            return self.get_fallback_response()
            
    def _analyze_performance_metrics(self, match_data: dict) -> str:
        """Analyze detailed performance metrics"""
        try:
            teams = match_data.get("match_info", {}).get("teams", {})
            home_team = teams.get("home", {}).get("name", "Home Team")
            
            # Get passing stats and key players
            top_passer_name, passes = self._get_player_by_stat(match_data, "home", "passes.total")
            accurate_passer_name, accuracy = self._get_player_by_stat(match_data, "home", "passes.accuracy")
            key_passer_name, key_passes = self._get_player_by_stat(match_data, "home", "passes.key")
            
            if top_passer_name and accurate_passer_name:
                analysis = (
                    f"In the passing department, {top_passer_name} led with {int(passes)} completed passes, "
                    f"while {accurate_passer_name} maintained an impressive {int(accuracy)}% accuracy"
                )
                if key_passer_name:
                    analysis += f", and {key_passer_name} created {int(key_passes)} key chances."
                else:
                    analysis += "."
            else:
                analysis = f"Both teams showed varying levels of passing efficiency throughout the match."
                
            return analysis
            
        except Exception as e:
            print(f"Error analyzing performance metrics: {e}")
            return ""
            
    def _analyze_defensive_stats(self, match_data: dict) -> str:
        """Analyze defensive statistics"""
        try:
            teams = match_data.get("match_info", {}).get("teams", {})
            home_team = teams.get("home", {}).get("name", "Home Team")
            
            # Get defensive stats and key players
            top_tackler_name, tackles = self._get_player_by_stat(match_data, "home", "tackles.total")
            top_intercept_name, interceptions = self._get_player_by_stat(match_data, "home", "tackles.interceptions")
            top_blocks_name, blocks = self._get_player_by_stat(match_data, "home", "tackles.blocks")
            
            if top_tackler_name and top_intercept_name:
                analysis = (
                    f"Defensively, {top_tackler_name} stood out with {int(tackles)} successful tackles, "
                    f"while {top_intercept_name} made {int(interceptions)} crucial interceptions"
                )
                if top_blocks_name:
                    analysis += f", and {top_blocks_name} contributed {int(blocks)} important blocks."
                else:
                    analysis += "."
            else:
                analysis = f"Both teams maintained solid defensive structures throughout the match."
                
            return analysis
            
        except Exception as e:
            print(f"Error analyzing defensive stats: {e}")
            return ""
