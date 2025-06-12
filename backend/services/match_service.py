"""Service for fetching and processing match data"""
import os
import requests
import json
import aiohttp
import asyncio
from typing import Dict, Optional, List, Union
from datetime import datetime
from dotenv import load_dotenv
import logging
import time
from services.data_store import DataStore

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
        
        self.data_store = DataStore()
        
    @classmethod
    async def create(cls):
        """Factory method to create and initialize a MatchService instance"""
        service = cls()
        await service._test_api_key()
        return service
    
    async def _test_api_key(self):
        """Test API key validity during initialization."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status",
                    headers=self.headers,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        raise ValueError("Invalid API key")
                    logger.info("API key validation successful")
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise ValueError(f"API key validation failed: {str(e)}")
    
    async def _make_request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make a request to the API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.retry_settings['max_retries']):
            try:
                logger.info(f"Making API request to {url} with params: {params}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers, params=params, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('errors'):
                                logger.error(f"API returned errors: {data['errors']}")
                                return None
                            return data
                        elif response.status == 429:  # Rate limit exceeded
                            retry_after = int(response.headers.get('Retry-After', self.retry_settings['base_delay']))
                            logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            logger.error(f"API request failed with status {response.status}")
                            return None
                    
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < self.retry_settings['max_retries'] - 1:
                    delay = min(self.retry_settings['base_delay'] * (2 ** attempt), self.retry_settings['max_delay'])
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                return None

    async def get_match_data(self, match_id: str) -> Optional[Dict]:
        """Get comprehensive match data"""
        try:
            # Get basic match data
            response = await self._make_request(f"fixtures?id={match_id}")
            if not response or not response.get("response"):
                print("❌ No match data found")
                return None
                
            # Get the main fixture data
            fixture_data = response.get("response", [{}])[0]
            
            # Get team IDs for h2h
            home_team_id = fixture_data.get("teams", {}).get("home", {}).get("id")
            away_team_id = fixture_data.get("teams", {}).get("away", {}).get("id")
            
            # Fetch head-to-head data
            h2h_data = None
            if home_team_id and away_team_id:
                h2h_data = await self._get_head_to_head_history(home_team_id, away_team_id)
            
            # Get lineups
            lineups_response = await self._make_request(f"fixtures/lineups?fixture={match_id}")
            lineups = lineups_response.get("response", []) if lineups_response else []
            
            # Get events
            events_response = await self._make_request(f"fixtures/events?fixture={match_id}")
            events = events_response.get("response", []) if events_response else []
            
            # Get player statistics
            players_response = await self._make_request(f"fixtures/players?fixture={match_id}")
            player_statistics = players_response.get("response", []) if players_response else []
            
            # Get team statistics
            stats_response = await self._make_request(f"fixtures/statistics?fixture={match_id}")
            team_statistics = stats_response.get("response", []) if stats_response else []
            
            # Combine all data
            raw_data = {
                "response": [fixture_data],
                "lineups": lineups,
                "events": events,
                "player_statistics": player_statistics,
                "team_statistics": team_statistics,
                "h2h": h2h_data or {}
            }
            
            # Process the raw data
            match_data = self._process_match_data(raw_data)
            
            # Validate the processed data
            if not self._validate_match_data(match_data):
                print("❌ Invalid match data structure")
                return None
                
            # Get additional match details
            match_details = await self._fetch_match_details(match_id)
            if match_details:
                match_data.update(match_details)
                
            return match_data
            
        except Exception as e:
            print(f"❌ Error getting match data: {e}")
            return None
            
    def _process_match_data(self, raw_data: Dict) -> Dict:
        """Process and format raw match data"""
        try:
            # Get the main fixture data
            fixture_data = raw_data.get("response", [{}])[0]
            
            # Extract required core data
            fixture = fixture_data.get("fixture", {})
            teams = fixture_data.get("teams", {})
            goals = fixture_data.get("goals", {})
            score = fixture_data.get("score", {})
            
            # Get additional data
            lineups = raw_data.get("lineups", [])
            events = raw_data.get("events", [])
            player_statistics = raw_data.get("player_statistics", [])
            team_statistics = raw_data.get("team_statistics", [])
            h2h_data = raw_data.get("h2h", {})
            
            # Process player statistics
            player_stats = {
                "home": [],
                "away": []
            }
            
            # Process lineups and player stats
            for lineup in lineups:
                team_id = lineup.get("team", {}).get("id")
                side = "home" if team_id == teams.get("home", {}).get("id") else "away"
                
                # Add starting XI with their statistics
                for player in lineup.get("startXI", []):
                    player_data = player.get("player", {})
                    # Find player's statistics
                    player_match_stats = next(
                        (stats for stats in player_statistics 
                         if stats.get("player", {}).get("id") == player_data.get("id")),
                        {}
                    )
                    
                    player_stats[side].append({
                        "id": player_data.get("id"),
                        "name": player_data.get("name"),
                        "number": player_data.get("number"),
                        "position": player_data.get("pos", player_data.get("position")),
                        "is_starter": True,
                        "statistics": player_match_stats.get("statistics", []),
                        "rating": player_match_stats.get("statistics", [{}])[0].get("games", {}).get("rating", 0)
                    })
                
                # Add substitutes with their statistics
                for player in lineup.get("substitutes", []):
                    player_data = player.get("player", {})
                    # Find player's statistics
                    player_match_stats = next(
                        (stats for stats in player_statistics 
                         if stats.get("player", {}).get("id") == player_data.get("id")),
                        {}
                    )
                    
                    player_stats[side].append({
                        "id": player_data.get("id"),
                        "name": player_data.get("name"),
                        "number": player_data.get("number"),
                        "position": player_data.get("pos", player_data.get("position")),
                        "is_starter": False,
                        "statistics": player_match_stats.get("statistics", []),
                        "rating": player_match_stats.get("statistics", [{}])[0].get("games", {}).get("rating", 0)
                    })
            
            # Process team statistics
            formatted_team_stats = {"home": {}, "away": {}}
            for team_stat in team_statistics:
                team_id = team_stat.get("team", {}).get("id")
                side = "home" if team_id == teams.get("home", {}).get("id") else "away"
                
                stats = {}
                for stat in team_stat.get("statistics", []):
                    stat_type = stat.get("type")
                    stat_value = stat.get("value")
                    
                    # Convert percentage strings to numbers
                    if isinstance(stat_value, str) and "%" in stat_value:
                        try:
                            stat_value = float(stat_value.strip("%"))
                        except ValueError:
                            pass
                            
                    stats[stat_type] = stat_value
                    
                formatted_team_stats[side] = stats
            
            # Create the properly structured match data
            processed_data = {
                "fixture": fixture,  # Required field
                "teams": teams,      # Required field
                "goals": goals,      # Required field
                "score": score,      # Required field
                "match_info": {
                    "fixture": fixture,
                    "teams": teams,
                    "goals": goals,
                    "score": score,
                    "league": fixture_data.get("league", {}),
                    "venue": fixture.get("venue", {}),
                    "referee": fixture.get("referee"),
                    "status": fixture.get("status", {})
                },
                "lineups": lineups,
                "events": events,
                "player_stats": player_stats,
                "team_stats": formatted_team_stats,
                "h2h": {
                    "history": h2h_data.get("matches", []),
                    "summary": h2h_data.get("stats", {})
                },
                "details": {
                    "formations": self._extract_formations(lineups),
                    "possession": self._extract_possession(formatted_team_stats),
                    "key_stats": {
                        "shots": {
                            "home": formatted_team_stats.get("home", {}).get("Total Shots", 0),
                            "away": formatted_team_stats.get("away", {}).get("Total Shots", 0)
                        },
                        "shots_on_target": {
                            "home": formatted_team_stats.get("home", {}).get("Shots on Goal", 0),
                            "away": formatted_team_stats.get("away", {}).get("Shots on Goal", 0)
                        },
                        "passes": {
                            "home": formatted_team_stats.get("home", {}).get("Total Passes", 0),
                            "away": formatted_team_stats.get("away", {}).get("Total Passes", 0)
                        },
                        "pass_accuracy": {
                            "home": formatted_team_stats.get("home", {}).get("Passes %", 0),
                            "away": formatted_team_stats.get("away", {}).get("Passes %", 0)
                        }
                    }
                }
            }
            
            return processed_data
            
        except Exception as e:
            print(f"Error processing match data: {e}")
            return {}
            
    def _extract_formations(self, lineups: list) -> Dict:
        """Extract team formations from lineups data"""
        formations = {"home": None, "away": None}
        for lineup in lineups:
            team = lineup.get("team", {})
            side = "home" if team.get("id") == lineup.get("team_id") else "away"
            formations[side] = lineup.get("formation")
        return formations
        
    def _extract_possession(self, team_stats: Dict) -> Dict:
        """Extract possession stats from team statistics"""
        try:
            home_possession = team_stats.get("home", {}).get("Ball Possession", 0)
            away_possession = team_stats.get("away", {}).get("Ball Possession", 0)
            
            # Handle percentage strings
            if isinstance(home_possession, str):
                home_possession = float(home_possession.strip("%"))
            if isinstance(away_possession, str):
                away_possession = float(away_possession.strip("%"))
                
            # If we only have one value, calculate the other
            if home_possession and not away_possession:
                away_possession = 100 - home_possession
            elif away_possession and not home_possession:
                home_possession = 100 - away_possession
            # If we have neither, default to 50-50
            elif not home_possession and not away_possession:
                home_possession = away_possession = 50
                
            return {
                "home": home_possession,
                "away": away_possession
            }
            
        except Exception as e:
            print(f"Error extracting possession stats: {e}")
            return {"home": 50, "away": 50}  # Default to 50-50

    async def get_match_info(self, match_id: str) -> Optional[Dict]:
        """Get comprehensive match information"""
        try:
            # Fetch basic match data
            match_data = await self.get_match_data(match_id)
            if not match_data:
                print(f"❌ Failed to fetch basic match data for ID: {match_id}")
                return None
                
            # Validate core match data
            required_fields = ['fixture', 'teams', 'goals', 'score']
            missing_fields = [field for field in required_fields if field not in match_data]
            if missing_fields:
                print(f"❌ Missing required fields in match data: {missing_fields}")
                return None
            
            # Fetch additional details
            try:
                details = await self._fetch_match_details(match_id)
                if details:
                    match_data.update(details)
                    print(f"✅ Successfully fetched additional match details")
                else:
                    print(f"⚠️ No additional match details available")
            except Exception as e:
                print(f"⚠️ Error fetching additional details: {e}")
            
            # Extract and validate statistics
            try:
                stats = await self._extract_team_stats(match_data)
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
        
    async def _fetch_match_details(self, match_id: str) -> Optional[Dict]:
        """Fetch detailed match information"""
        try:
            # Get lineups and formations
            lineup_response = await self._make_request(f"fixtures/lineups?fixture={match_id}")
            formations = {"home": "Unknown", "away": "Unknown"}
            lineups = []
            
            if lineup_response and lineup_response.get('response'):
                lineups = lineup_response['response']
                # Process formations
                for lineup in lineups:
                    team = lineup.get('team', {})
                    team_id = team.get('id')
                    formation = lineup.get('formation')
                    
                    # Determine if home or away based on team ID
                    is_home = team.get('name') == lineup_response['response'][0]['team']['name']
                    team_type = 'home' if is_home else 'away'
                    formations[team_type] = formation
            
            # Get player statistics
            player_stats_response = await self._make_request(f"fixtures/players?fixture={match_id}")
            player_stats = {}
            if player_stats_response and player_stats_response.get('response'):
                for team_stats in player_stats_response['response']:
                    team = team_stats.get('team', {})
                    team_id = team.get('id')
                    if team_id:
                        player_stats[team_id] = team_stats.get('players', [])
            
            # Get team statistics
            stats_response = await self._make_request(f"fixtures/statistics?fixture={match_id}")
            team_stats = {"home": [], "away": []}
            if stats_response and stats_response.get('response'):
                for team_stat in stats_response['response']:
                    team = team_stat.get('team', {})
                    team_id = team.get('id')
                    # Determine if home or away based on first team in response
                    is_home = team.get('name') == stats_response['response'][0]['team']['name']
                    team_type = 'home' if is_home else 'away'
                    team_stats[team_type] = team_stat.get('statistics', [])
            
            # Get events
            events_response = await self._make_request(f"fixtures/events?fixture={match_id}")
            events = []
            if events_response and events_response.get('response'):
                events = events_response['response']
            
            # Compile details
            details = {
                "formations": formations,
                "lineups": lineups,
                "player_statistics": player_stats,
                "team_statistics": team_stats,
                "events": events,
                "venue": await self._get_venue_details(match_id),
                "weather": await self._get_weather_details(match_id),
                "referee": await self._get_referee_details(match_id)
            }
            
            return details
            
        except Exception as e:
            print(f"❌ Error in _fetch_match_details: {e}")
            return None
        
    async def _format_team_statistics(self, basic_data: Dict, details: Dict) -> Optional[Dict]:
        """Format team statistics"""
        try:
            # Get team statistics from details
            team_stats = details.get('team_statistics', {})
            if not team_stats:
                print("❌ No team statistics available")
                return None
            
            # Format statistics for each team
            formatted_stats = {"home": {}, "away": {}}
            for team_type, stats in team_stats.items():
                formatted_team_stats = {}
                for stat in stats:
                    stat_type = stat.get('type')
                    stat_value = stat.get('value')
                    
                    # Convert percentage strings to numbers
                    if isinstance(stat_value, str) and '%' in stat_value:
                        try:
                            stat_value = float(stat_value.rstrip('%'))
                        except ValueError:
                            pass
                    
                    formatted_team_stats[stat_type] = stat_value
                
                # Add expected goals if available
                team_id = basic_data.get('teams', {}).get(team_type, {}).get('id')
                if team_id:
                    xg_data = await self._get_expected_goals(basic_data['fixture']['id'], team_id)
                    if xg_data:
                        formatted_team_stats.update(xg_data)
                
                formatted_stats[team_type] = formatted_team_stats
            
            return formatted_stats
            
        except Exception as e:
            print(f"❌ Error formatting team statistics: {e}")
            return None
        
    async def _extract_statistics(self, team_stats: Dict) -> Optional[Dict]:
        """Extract and format statistics"""
        try:
            # Get base statistics
            home_stats = team_stats.get("home", {})
            away_stats = team_stats.get("away", {})
            
            if not home_stats or not away_stats:
                print("❌ Missing team statistics")
                return None
            
            # Get shots and shots on target
            home_shots = float(home_stats.get("Total Shots", 0) or 0)
            home_shots_on_target = float(home_stats.get("Shots on Goal", 0) or 0)
            away_shots = float(away_stats.get("Total Shots", 0) or 0)
            away_shots_on_target = float(away_stats.get("Shots on Goal", 0) or 0)
            
            # Calculate shot accuracy and conversion
            home_shot_accuracy = round(home_shots_on_target / max(1, home_shots) * 100, 1)
            away_shot_accuracy = round(away_shots_on_target / max(1, away_shots) * 100, 1)
            
            # Return formatted statistics
            return {
                "home": {
                    **home_stats,
                    "shot_accuracy": home_shot_accuracy
                },
                "away": {
                    **away_stats,
                    "shot_accuracy": away_shot_accuracy
                }
            }
            
        except Exception as e:
            print(f"❌ Error extracting statistics: {e}")
            return None

    async def _extract_team_stats(self, match_data: Dict) -> Optional[Dict]:
        """Extract and format team statistics"""
        try:
            # Fetch statistics
            stats_response = await self._make_request(f"fixtures/statistics?fixture={match_data['fixture']['id']}")
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
                
                # Extract all available statistics
                team_statistics = {}
                for stat in team_stats.get('statistics', []):
                    stat_type = stat.get('type')
                    stat_value = stat.get('value')
                    
                    # Convert percentage strings to numbers
                    if isinstance(stat_value, str) and '%' in stat_value:
                        try:
                            stat_value = float(stat_value.rstrip('%'))
                        except ValueError:
                            pass
                            
                    team_statistics[stat_type] = stat_value
                
                # Add expected goals and goals prevented if available
                xg_data = await self._get_expected_goals(match_data['fixture']['id'], team_id)
                if xg_data:
                    team_statistics.update(xg_data)
                
                formatted_stats[team_type] = team_statistics
            
            print(f"✅ Successfully formatted team statistics")
            return formatted_stats
            
        except Exception as e:
            print(f"❌ Error extracting team statistics: {e}")
            return None

    async def _get_expected_goals(self, fixture_id: int, team_id: int) -> Dict:
        """Get expected goals data for a team"""
        try:
            response = await self._make_request(f"fixtures/statistics", params={
                "fixture": fixture_id,
                "team": team_id
            })
            
            if not response or not response.get('response'):
                print(f"⚠️ No expected goals data available")
                return {
                    "expected_goals": "0",
                    "goals_prevented": "0"
                }
            
            # Get the statistics array for this team
            team_stats = response['response'][0].get('statistics', [])
            
            # Find expected goals in the statistics
            expected_goals = "0"
            goals_prevented = "0"
            
            for stat in team_stats:
                if stat.get('type') == 'expected_goals':
                    expected_goals = str(stat.get('value', '0'))
                elif stat.get('type') == 'goals_prevented':
                    goals_prevented = str(stat.get('value', '0'))
            
            return {
                "expected_goals": expected_goals,
                "goals_prevented": goals_prevented
            }
            
        except Exception as e:
            print(f"❌ Error getting expected goals: {e}")
            return {
                "expected_goals": "0",
                "goals_prevented": "0"
            }

    async def _get_player_performances(self, match_id: str) -> Dict:
        """Get detailed player statistics"""
        try:
            response = await self._make_request(f"fixtures/players?fixture={match_id}")
            if not response or not response.get('response'):
                return {}
                
            player_stats = {}
            for team_stats in response['response']:
                team_id = team_stats.get('team', {}).get('id')
                if team_id:
                    player_stats[team_id] = team_stats.get('players', [])
                    
            return player_stats
            
        except Exception as e:
            print(f"❌ Error getting player performances: {e}")
            return {}

    async def _get_head_to_head_history(self, team_id1: int, team_id2: int) -> Optional[Dict]:
        """Get head-to-head history between two teams"""
        try:
            response = await self._make_request(f"fixtures/headtohead?h2h={team_id1}-{team_id2}")
            if not response or not response.get('response'):
                return None
                
            matches = response['response']
            
            # Calculate statistics
            home_wins = 0
            away_wins = 0
            for match in matches:
                goals = match.get('goals', {})
                if goals.get('home', 0) > goals.get('away', 0):
                    home_wins += 1
                elif goals.get('away', 0) > goals.get('home', 0):
                    away_wins += 1
                    
            return {
                'matches': matches,
                'stats': {
                    'total_matches': len(matches),
                    'home_wins': home_wins,
                    'away_wins': away_wins,
                    'draws': len(matches) - home_wins - away_wins
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting head-to-head history: {e}")
            return None

    async def _get_match_lineups(self, match_id: str) -> Optional[List]:
        """Get match lineups"""
        try:
            response = await self._make_request(f"fixtures/lineups?fixture={match_id}")
            if not response or "response" not in response:
                return None
                
            return response["response"]
            
        except Exception as e:
            print(f"❌ Error getting match lineups: {e}")
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

    async def _get_match_events(self, match_id: str) -> Optional[List]:
        """Get match events with enhanced details"""
        try:
            response = await self._make_request(f"fixtures/events?fixture={match_id}")
            if not response or "response" not in response:
                return None
                
            events = response["response"]
            enhanced_events = []
            
            for event in events:
                if event.get('type') == 'Goal':
                    event['context'] = await self._get_goal_context(event)
                elif event.get('type') in ['Yellow Card', 'Red Card']:
                    event['context'] = await self._get_card_context(event)
                enhanced_events.append(event)
                
            return enhanced_events
            
        except Exception as e:
            print(f"❌ Error getting match events: {e}")
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

    async def _get_venue_details(self, match_id: str) -> Dict:
        """Get venue details"""
        try:
            response = await self._make_request(f"fixtures?id={match_id}")
            if response and response.get('response'):
                fixture = response['response'][0].get('fixture', {})
                venue = fixture.get('venue', {})
                return {
                    "name": venue.get('name'),
                    "city": venue.get('city'),
                    "capacity": venue.get('capacity'),
                    "surface": venue.get('surface'),
                    "attendance": fixture.get('attendance')
                }
        except Exception as e:
            print(f"⚠️ Error getting venue details: {e}")
        return {}

    async def _get_weather_details(self, match_id: str) -> Dict:
        """Get weather details"""
        try:
            response = await self._make_request(f"fixtures?id={match_id}")
            if response and response.get('response'):
                return response['response'][0].get('fixture', {}).get('weather', {})
        except Exception as e:
            print(f"⚠️ Error getting weather details: {e}")
        return {}

    async def _get_referee_details(self, match_id: str) -> Dict:
        """Get referee details"""
        try:
            response = await self._make_request(f"fixtures?id={match_id}")
            if response and response.get('response'):
                return response['response'][0].get('fixture', {}).get('referee', {})
        except Exception as e:
            print(f"⚠️ Error getting referee details: {e}")
        return {}

    def _validate_match_data(self, match_data: Dict) -> bool:
        """Validate that all required fields are present in match data"""
        try:
            # Check for required root level fields
            required_fields = ['fixture', 'teams', 'goals', 'score']
            for field in required_fields:
                if field not in match_data:
                    print(f"❌ Missing required field: {field}")
                    return False
                    
            # Validate teams data
            teams = match_data.get('teams', {})
            for team_type in ['home', 'away']:
                team = teams.get(team_type, {})
                if not all(k in team for k in ['id', 'name']):
                    print(f"❌ Missing required team fields for {team_type}")
                    return False
                    
            # Validate goals data
            goals = match_data.get('goals', {})
            if not all(k in goals for k in ['home', 'away']):
                print("❌ Missing required goals fields")
                return False
                
            # Validate score data
            score = match_data.get('score', {})
            if not all(k in score for k in ['halftime', 'fulltime']):
                print("❌ Missing required score fields")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error validating match data: {e}")
            return False

        return None 