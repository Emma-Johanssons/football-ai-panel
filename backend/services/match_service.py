"""Service for fetching and processing match data"""
import os
import requests
import json
from typing import Dict, Optional, List, Union
from datetime import datetime
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class MatchService:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        if not self.api_key:
            raise ValueError("FOOTBALL_API_KEY not found in environment variables")
            
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }
        
        # Configure retry settings
        self.retry_settings = {
            'max_retries': 3,
            'base_delay': 2,  # Base delay in seconds
            'max_delay': 10   # Maximum delay in seconds
        }
        
        # Initialize cache for frequently accessed data
        self.cache = {}
        
        # Test API key validity
        self._test_api_key()
    
    def _test_api_key(self):
        """Test API key validity during initialization."""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers,
                timeout=30
            )
            if response.status_code != 200:
                raise ValueError("Invalid API key")
            logger.info("API key validation successful")
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise ValueError(f"API key validation failed: {str(e)}")
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make a request to the API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.retry_settings['max_retries']):
            try:
                logger.info(f"Making API request to {url} with params: {params}")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('errors'):
                        logger.error(f"API returned errors: {data['errors']}")
                        return None
                    return data
                elif response.status_code == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', self.retry_settings['base_delay']))
                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"API request failed with status {response.status_code}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < self.retry_settings['max_retries'] - 1:
                    delay = min(self.retry_settings['base_delay'] * (2 ** attempt), self.retry_settings['max_delay'])
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                return None
    
    def get_match_info(self, match_id: str) -> Optional[Dict]:
        """Get comprehensive match information"""
        try:
            # Fetch basic match data
            match_data = self._fetch_match_data(match_id)
            if not match_data:
                print(f"❌ Failed to fetch basic match data for ID: {match_id}")
                return None
                
            # Validate core match data
            required_fields = ['fixture', 'league', 'teams', 'goals', 'score']
            missing_fields = [field for field in required_fields if field not in match_data]
            if missing_fields:
                print(f"❌ Missing required fields in match data: {missing_fields}")
                return None
            
            # Fetch additional details
            try:
                details = self._fetch_match_details(match_id, match_data)
                if details:
                    match_data.update(details)
                    print(f"✅ Successfully fetched additional match details")
                else:
                    print(f"⚠️ No additional match details available")
            except Exception as e:
                print(f"⚠️ Error fetching additional details: {e}")
            
            # Validate team data
            if not self._validate_team_data(match_data):
                print(f"❌ Invalid team data in match response")
                return None
            
            # Extract and validate statistics
            try:
                stats = self._extract_team_stats(match_data)
                if stats:
                    match_data["statistics"] = stats
                    print(f"✅ Successfully extracted team statistics")
                else:
                    print(f"⚠️ No team statistics available")
            except Exception as e:
                print(f"⚠️ Error extracting team statistics: {e}")
            
            print(f"✅ Successfully compiled match data for ID: {match_id}")
            return match_data
            
        except Exception as e:
            print(f"❌ Error in get_match_info: {e}")
            return None
    
    def _validate_team_data(self, match_data: Dict) -> bool:
        """Validate team data structure"""
        try:
            teams = match_data.get('teams', {})
            if not teams:
                return False
                
            # Check home team
            home = teams.get('home', {})
            if not all(k in home for k in ['id', 'name', 'logo']):
                print(f"❌ Missing required home team fields")
                return False
                
            # Check away team
            away = teams.get('away', {})
            if not all(k in away for k in ['id', 'name', 'logo']):
                print(f"❌ Missing required away team fields")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error validating team data: {e}")
            return False
    
    def _fetch_match_data(self, match_id: str) -> Optional[Dict]:
        """Fetch basic match data"""
        try:
            response = self._make_request(f"/fixtures?id={match_id}")
            if not response or not response.get('response'):
                print(f"❌ No response data for match ID: {match_id}")
                return None
                
            match_data = response['response'][0]
            print(f"✅ Successfully fetched basic match data")
            return match_data
            
        except Exception as e:
            print(f"❌ Error fetching match data: {e}")
            return None
    
    def _fetch_match_details(self, match_id: str, match_data: Dict) -> Optional[Dict]:
        """Fetch additional match details"""
        try:
            # Fetch events
            events_response = self._make_request(f"/fixtures/events?fixture={match_id}")
            events = events_response.get('response', []) if events_response else []
            
            # Fetch lineups with formations
            lineups_response = self._make_request(f"/fixtures/lineups?fixture={match_id}")
            lineups = []
            formations = {"home": "Unknown", "away": "Unknown"}
            
            if lineups_response and 'response' in lineups_response:
                for lineup in lineups_response['response']:
                    team_type = 'home' if lineup.get('team', {}).get('id') == match_data['teams']['home']['id'] else 'away'
                    if 'formation' in lineup:
                        formations[team_type] = lineup['formation']
                    lineups.append(lineup)
            
            details = {
                'events': events,
                'lineups': lineups,
                'formations': formations
            }
            
            # Validate details
            if not events and not lineups:
                print(f"⚠️ No additional details available")
                return None
                
            return details
            
        except Exception as e:
            print(f"❌ Error fetching match details: {e}")
            return None
    
    def _extract_team_stats(self, match_data: Dict) -> Optional[Dict]:
        """Extract and format team statistics"""
        try:
            # Fetch statistics
            stats_response = self._make_request(f"/fixtures/statistics?fixture={match_data['fixture']['id']}")
            if not stats_response or not stats_response.get('response'):
                print(f"❌ No statistics available")
                return None
                
            stats = stats_response['response']
            formatted_stats = {"home": {}, "away": {}}
            
            # Process each team's statistics
            for team_stats in stats:
                team_id = team_stats.get('team', {}).get('id')
                if not team_id:
                    continue
                    
                # Determine if home or away team
                team_type = 'home' if team_id == match_data['teams']['home']['id'] else 'away'
                
                # Format basic statistics
                formatted_stats[team_type] = {
                    "formation": match_data.get('formations', {}).get(team_type, "Unknown"),
                    "possession": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                     if stat.get('type') == 'Ball Possession'), "0"),
                    "passes": {
                        "total": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                    if stat.get('type') == 'Total passes'), "0"),
                        "accuracy": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                       if stat.get('type') == 'Passes accurate'), "0")
                    },
                    "shots": {
                        "total": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                    if stat.get('type') == 'Total Shots'), "0"),
                        "on_target": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                        if stat.get('type') == 'Shots on Goal'), "0")
                    },
                    "tackles": {
                        "total": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                    if stat.get('type') == 'Tackles'), "0"),
                        "success_rate": next((stat.get('value') for stat in team_stats.get('statistics', []) 
                                           if stat.get('type') == 'Tackles success rate'), "0")
                    }
                }
            
            print(f"✅ Successfully formatted team statistics")
            return formatted_stats
            
        except Exception as e:
            print(f"❌ Error extracting team statistics: {e}")
            return None

    def get_match_data(self, match_id: str) -> Optional[Dict]:
        """Get comprehensive match data including current rosters"""
        try:
            # Check cache first
            cache_key = f"match_{match_id}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Get basic match data
            match_data = self._fetch_match_data(match_id)
            if not match_data:
                print(f"❌ No match data found for ID: {match_id}")
                return None
            
            # Structure the match info
            match_info = {
                "teams": {
                    "home": {
                        "name": match_data["teams"]["home"]["name"],
                        "id": match_data["teams"]["home"]["id"],
                        "logo": match_data["teams"]["home"]["logo"]
                    },
                    "away": {
                        "name": match_data["teams"]["away"]["name"],
                        "id": match_data["teams"]["away"]["id"],
                        "logo": match_data["teams"]["away"]["logo"]
                    }
                },
                "home_team": match_data["teams"]["home"]["name"],
                "away_team": match_data["teams"]["away"]["name"],
                "score": {
                    "home": match_data["goals"]["home"],
                    "away": match_data["goals"]["away"]
                },
                "fixture": {
                    "date": match_data["fixture"]["date"],
                    "venue": match_data["fixture"]["venue"]["name"],
                    "status": match_data["fixture"]["status"]["long"]
                },
                "league": {
                    "name": match_data["league"]["name"],
                    "country": match_data["league"]["country"],
                    "season": match_data["league"]["season"],
                    "round": match_data["league"]["round"]
                }
            }
            
            # Get team IDs
            team_ids = [
                match_data["teams"]["home"]["id"],
                match_data["teams"]["away"]["id"]
            ]
            
            # Get detailed team statistics
            team_statistics = {"home": {}, "away": {}}
            for i, team_id in enumerate(team_ids):
                team_type = "home" if i == 0 else "away"
                team_stats = self._get_team_statistics(
                    team_id, 
                    match_data["league"]["id"],
                    match_data["league"]["season"]
                )
                if team_stats:
                    team_statistics[team_type] = team_stats
                    
                    # Add season performance metrics
                    season_stats = self._get_season_statistics(team_id, match_data["league"]["id"])
                    if season_stats:
                        team_statistics[team_type]["season"] = season_stats
            
            # Get match events with enhanced details
            events = self._get_match_events(match_id)
            if events:
                # Process events to add context
                processed_events = []
                for event in events:
                    processed_event = {
                        "time": event.get("time", {}),
                        "team": event.get("team", {}),
                        "player": event.get("player", {}),
                        "type": event.get("type", ""),
                        "detail": event.get("detail", ""),
                        "comments": event.get("comments", ""),
                        "assist": event.get("assist", {})
                    }
                    
                    # Add context based on event type
                    if processed_event["type"] == "Goal":
                        # Add goal context (buildup, assist quality, etc.)
                        processed_event["context"] = self._get_goal_context(event)
                    elif processed_event["type"] == "Card":
                        # Add card context (reason, impact, etc.)
                        processed_event["context"] = self._get_card_context(event)
                    
                    processed_events.append(processed_event)
                
                coach_data = {
                    "events": processed_events,
                    "lineups": self._get_match_lineups(match_id),
                    "formations": self._get_team_formations(team_ids),
                    "tactics": self._analyze_team_tactics(processed_events)
                }
            else:
                coach_data = {
                    "events": [],
                    "lineups": [],
                    "formations": {"home": "Unknown", "away": "Unknown"},
                    "tactics": {}
                }
            
            # Get head-to-head history with context
            h2h_data = self._get_head_to_head_history(team_ids[0], team_ids[1])
            
            # Get player performance data
            player_data = self._get_player_performances(match_id)
            
            # Compile all data
            compiled_data = {
                "match_info": match_info,
                "team_statistics": team_statistics,
                "coach_data": coach_data,
                "h2h_data": h2h_data,
                "player_data": player_data
            }
            
            # Cache the data
            self.cache[cache_key] = compiled_data
            
            print(f"✅ Successfully compiled all match data")
            return compiled_data
            
        except Exception as e:
            print(f"❌ Error in get_match_data: {e}")
            return None
            
    def _get_goal_context(self, event: Dict) -> Dict:
        """Get detailed context for a goal event"""
        return {
            "buildup_play": self._analyze_buildup_play(event),
            "assist_quality": self._analyze_assist_quality(event),
            "goal_importance": self._analyze_goal_importance(event),
            "similar_goals": self._find_similar_goals(event)
        }
    
    def _get_card_context(self, event: Dict) -> Dict:
        """Get detailed context for a card event"""
        return {
            "reason": self._analyze_card_reason(event),
            "impact": self._analyze_card_impact(event),
            "player_history": self._get_player_card_history(event)
        }
    
    def _get_player_performances(self, match_id: str) -> Dict:
        """Get detailed player performance data"""
        try:
            response = self._make_request(f"/fixtures/players?fixture={match_id}")
            if not response or "response" not in response:
                return {}
                
            performances = {}
            for team_data in response["response"]:
                for player in team_data.get("players", []):
                    player_id = player.get("player", {}).get("id")
                    if player_id:
                        performances[player_id] = {
                            "statistics": player.get("statistics", []),
                            "rating": player.get("statistics", [{}])[0].get("games", {}).get("rating", 0),
                            "minutes_played": player.get("statistics", [{}])[0].get("games", {}).get("minutes", 0),
                            "position": player.get("statistics", [{}])[0].get("games", {}).get("position", ""),
                            "is_substitute": player.get("statistics", [{}])[0].get("games", {}).get("substitute", False)
                        }
            
            return performances
            
        except Exception as e:
            print(f"❌ Error getting player performances: {e}")
            return {}

    def _get_team_statistics(self, team_id: int, league_id: int, season: Union[int, str]) -> Optional[Dict]:
        """Get detailed team statistics"""
        try:
            # Convert season to integer
            season_int = int(season) if season and season != "current" else datetime.now().year
            
            response = self._make_request(
                'teams/statistics',
                {
                    "team": team_id,
                    "league": league_id,
                    "season": season_int
                }
            )
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting team statistics: {e}")
            return None

    def _get_season_statistics(self, team_id: int, league_id: int) -> Optional[Dict]:
        """Get season performance statistics"""
        try:
            # Get current season
            current_season = datetime.now().year
            
            response = self._make_request(
                'teams/statistics',
                {
                    "team": team_id,
                    "league": league_id,
                    "season": current_season
                }
            )
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting season statistics: {e}")
            return None

    def _get_match_events(self, match_id: str) -> Optional[List]:
        """Get match events with enhanced details"""
        try:
            response = self._make_request(f"/fixtures/events?fixture={match_id}")
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting match events: {e}")
            return None

    def _get_match_lineups(self, match_id: str) -> Optional[List]:
        """Get match lineups"""
        try:
            response = self._make_request(f"/fixtures/lineups?fixture={match_id}")
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting match lineups: {e}")
            return None

    def _get_team_formations(self, team_ids: List) -> Dict:
        """Get team formations"""
        try:
            formations = {"home": "Unknown", "away": "Unknown"}
            for team_id in team_ids:
                response = self._make_request(f"/fixtures/lineups?fixture={team_id}")
                if response and "response" in response:
                    for lineup in response["response"]:
                        team_type = 'home' if lineup.get('team', {}).get('id') == team_ids[0] else 'away'
                        if 'formation' in lineup:
                            formations[team_type] = lineup['formation']
            return formations
            
        except Exception as e:
            print(f"❌ Error getting team formations: {e}")
            return None

    def _analyze_team_tactics(self, events: List) -> Dict:
        """Analyze team tactics based on match events"""
        try:
            # Implementation of tactic analysis logic
            return {}
            
        except Exception as e:
            print(f"❌ Error analyzing team tactics: {e}")
            return None

    def _get_head_to_head_history(self, team_id1: int, team_id2: int) -> Optional[Dict]:
        """Get head-to-head history between two teams"""
        try:
            response = self._make_request(
                'fixtures/headtohead',
                {"h2h": f"{team_id1}-{team_id2}"}
            )
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting head-to-head history: {e}")
            return None

    def _analyze_buildup_play(self, event: Dict) -> Dict:
        """Analyze buildup play for a goal event"""
        # Implementation of buildup play analysis logic
        return {}

    def _analyze_assist_quality(self, event: Dict) -> Dict:
        """Analyze assist quality for a goal event"""
        # Implementation of assist quality analysis logic
        return {}

    def _analyze_goal_importance(self, event: Dict) -> Dict:
        """Analyze goal importance for a goal event"""
        # Implementation of goal importance analysis logic
        return {}

    def _find_similar_goals(self, event: Dict) -> Dict:
        """Find similar goals in the match"""
        # Implementation of similar goals analysis logic
        return {}

    def _analyze_card_reason(self, event: Dict) -> Dict:
        """Analyze reason for a card event"""
        # Implementation of card reason analysis logic
        return {}

    def _analyze_card_impact(self, event: Dict) -> Dict:
        """Analyze impact of a card event"""
        # Implementation of card impact analysis logic
        return {}

    def _get_player_card_history(self, event: Dict) -> Dict:
        """Get player card history for a card event"""
        # Implementation of player card history retrieval logic
        return {}

        return None 