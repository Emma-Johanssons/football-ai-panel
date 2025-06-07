import os
from typing import Dict, List, Optional
from datetime import datetime
from .match_service import MatchService

class MatchAnalysisService:
    def __init__(self):
        self.match_service = MatchService()
    
    def get_comprehensive_match_data(self, match_id: str) -> Dict:
        """Get comprehensive match data including all relevant statistics and information"""
        try:
            # Get basic match data
            match_data = self.match_service.get_match_data(match_id)
            if not match_data or not isinstance(match_data, dict):
                print("❌ Invalid match data format")
                return {}
            
            # Ensure we have the basic structure
            if "match_info" not in match_data:
                match_data["match_info"] = {}
            
            # Get team statistics
            teams = match_data.get("teams", {})
            if not teams:
                teams = {
                    "home": {"name": "Home Team"},
                    "away": {"name": "Away Team"}
                }
            
            # Get player statistics
            player_stats = match_data.get("player_stats", {})
            if not player_stats:
                player_stats = {
                    "home": [],
                    "away": []
                }
            
            # Get match events
            events = match_data.get("events", [])
            
            # Compile comprehensive data
            comprehensive_data = {
                "match_info": {
                    "match_id": match_id,
                    "home_team": teams.get("home", {}).get("name", "Home Team"),
                    "away_team": teams.get("away", {}).get("name", "Away Team"),
                    "score": match_data.get("score", {"home": 0, "away": 0}),
                    "fixture": match_data.get("fixture", {}),
                    "league": match_data.get("league", {}),
                    "teams": teams
                },
                "statistics": {
                    "team_stats": match_data.get("match_statistics", {}),
                    "player_stats": player_stats
                },
                "events": events,
                "lineups": match_data.get("lineups", {}),
                "formations": match_data.get("formations", {}),
                "tactical_analysis": match_data.get("tactical_analysis", {})
            }
            
            print("✅ Successfully compiled comprehensive match data")
            return comprehensive_data
            
        except Exception as e:
            print(f"❌ Error compiling match data: {str(e)}")
            return {}
    
    def get_key_insights(self, match_data: Dict) -> Dict:
        """Extract key insights from match data for different perspectives"""
        insights = {
            "tactical": self._get_tactical_insights(match_data),
            "statistical": self._get_statistical_insights(match_data),
            "performance": self._get_performance_insights(match_data)
        }
        return insights
    
    def _get_tactical_insights(self, match_data: Dict) -> Dict:
        """Extract tactical insights from match data"""
        return {
            "formations": match_data.get("match_data", {}).get("formations", {}),
            "possession": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("possession", 0),
                "away": match_data.get("team_stats", {}).get("away", {}).get("possession", 0)
            },
            "passing": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("passing", {}),
                "away": match_data.get("team_stats", {}).get("away", {}).get("passing", {})
            },
            "attacking": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("attacking", {}),
                "away": match_data.get("team_stats", {}).get("away", {}).get("attacking", {})
            }
        }
    
    def _get_statistical_insights(self, match_data: Dict) -> Dict:
        """Extract statistical insights from match data"""
        return {
            "shots": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("shots", {}),
                "away": match_data.get("team_stats", {}).get("away", {}).get("shots", {})
            },
            "goals": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("goals", {}),
                "away": match_data.get("team_stats", {}).get("away", {}).get("goals", {})
            },
            "expected_goals": {
                "home": match_data.get("team_stats", {}).get("home", {}).get("expected_goals", {}),
                "away": match_data.get("team_stats", {}).get("away", {}).get("expected_goals", {})
            }
        }
    
    def _get_performance_insights(self, match_data: Dict) -> Dict:
        """Extract performance insights from match data"""
        return {
            "player_ratings": {
                player_id: {
                    "rating": perf.get("stats", {}).get("statistics", [{}])[0].get("games", {}).get("rating", 0),
                    "form": perf.get("form", [])
                }
                for player_id, perf in match_data.get("player_performances", {}).items()
            },
            "team_form": {
                "home": match_data.get("recent_form", {}).get("home", []),
                "away": match_data.get("recent_form", {}).get("away", [])
            }
        } 