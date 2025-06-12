"""
Dynamic RAG service for real-time football data and news
"""
import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
import tweepy
from dotenv import load_dotenv

class DynamicFootballRAG:
    def __init__(self):
        load_dotenv()
        self.football_api_key = os.getenv("FOOTBALL_API_KEY")
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        
        # Initialize Twitter client
        self.twitter_client = tweepy.Client(bearer_token=self.twitter_bearer_token) if self.twitter_bearer_token else None
        
        # Cache settings
        self.cache_dir = "backend/data/cache"
        self.cache_duration = timedelta(hours=1)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    async def get_match_context(self, home_team: str, away_team: str, match_id: str) -> Dict:
        """Get comprehensive match context including news, transfers, and history"""
        context = {
            "news": await self.get_team_news(home_team, away_team),
            "transfers": await self.get_transfer_updates(home_team, away_team),
            "head_to_head": await self.get_head_to_head(match_id),
            "social_buzz": await self.get_social_media_buzz(home_team, away_team),
            "historical_drama": await self.get_historical_drama(home_team, away_team)
        }
        return context
        
    async def get_team_news(self, home_team: str, away_team: str) -> List[Dict]:
        """Fetch latest news about both teams"""
        cache_file = os.path.join(self.cache_dir, f"news_{home_team}_{away_team}.json")
        
        # Check cache
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if datetime.fromisoformat(cached_data['timestamp']) + self.cache_duration > datetime.now():
                    return cached_data['news']
        
        news = []
        
        # NewsAPI
        if self.news_api_key:
            query = f"({home_team} OR {away_team}) AND football"
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={self.news_api_key}"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    news.extend([{
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'source': article['source']['name'],
                        'published': article['publishedAt']
                    } for article in articles[:10]])
            except Exception as e:
                print(f"Error fetching news: {e}")
        
        # Cache results
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'news': news
            }, f)
            
        return news
        
    async def get_transfer_updates(self, home_team: str, away_team: str) -> Dict:
        """Get latest transfer information for both teams"""
        if not self.football_api_key:
            return {}
            
        transfers = {"home": [], "away": []}
        current_season = datetime.now().year
        
        for team, team_name in [("home", home_team), ("away", away_team)]:
            try:
                # Get team ID first
                team_response = requests.get(
                    "https://v3.football.api-sports.io/teams",
                    headers={"x-apisports-key": self.football_api_key},
                    params={"name": team_name}
                )
                
                if team_response.status_code == 200:
                    team_data = team_response.json()
                    if team_data.get("response"):
                        team_id = team_data["response"][0]["team"]["id"]
                        
                        # Get transfers
                        transfer_response = requests.get(
                            "https://v3.football.api-sports.io/transfers",
                            headers={"x-apisports-key": self.football_api_key},
                            params={"team": team_id}
                        )
                        
                        if transfer_response.status_code == 200:
                            transfers[team] = transfer_response.json().get("response", [])
                            
            except Exception as e:
                print(f"Error fetching transfers for {team_name}: {e}")
                
        return transfers
        
    async def get_head_to_head(self, match_id: str) -> Dict:
        """Get head-to-head history and statistics"""
        if not self.football_api_key:
            return {}
            
        try:
            response = requests.get(
                f"https://v3.football.api-sports.io/fixtures/headtohead",
                headers={"x-apisports-key": self.football_api_key},
                params={"fixture": match_id}
            )
            
            if response.status_code == 200:
                h2h_data = response.json()
                if h2h_data.get("response"):
                    return {
                        "matches": h2h_data["response"],
                        "summary": self._analyze_h2h(h2h_data["response"])
                    }
                    
        except Exception as e:
            print(f"Error fetching head-to-head: {e}")
            
        return {}
        
    async def get_social_media_buzz(self, home_team: str, away_team: str) -> List[Dict]:
        """Get recent social media discussions about the match"""
        tweets = []
        
        if self.twitter_client:
            try:
                # Search for recent tweets about both teams
                query = f"({home_team} {away_team}) (match OR game OR fixture) -is:retweet"
                tweets_response = self.twitter_client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['created_at', 'public_metrics']
                )
                
                if tweets_response.data:
                    tweets = [{
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'metrics': tweet.public_metrics
                    } for tweet in tweets_response.data]
                    
            except Exception as e:
                print(f"Error fetching tweets: {e}")
                
        return tweets
        
    async def get_historical_drama(self, home_team: str, away_team: str) -> List[Dict]:
        """Find historical dramatic moments or controversies between teams"""
        drama_points = []
        
        # Check cached dramatic moments
        cache_file = os.path.join(self.cache_dir, f"drama_{home_team}_{away_team}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
                
        try:
            # Search for dramatic matches in head-to-head history
            if self.football_api_key:
                response = requests.get(
                    "https://v3.football.api-sports.io/fixtures/headtohead",
                    headers={"x-apisports-key": self.football_api_key},
                    params={
                        "h2h": f"{home_team}-{away_team}",
                        "last": 20
                    }
                )
                
                if response.status_code == 200:
                    matches = response.json().get("response", [])
                    
                    for match in matches:
                        # Look for red cards, penalties, or high-scoring games
                        events = match.get("events", [])
                        red_cards = [e for e in events if e["type"] == "Card" and e["detail"] == "Red Card"]
                        penalties = [e for e in events if e["type"] == "Penalty"]
                        
                        if red_cards or penalties or (match["goals"]["home"] + match["goals"]["away"] >= 5):
                            drama_points.append({
                                "match_date": match["fixture"]["date"],
                                "score": f"{match['goals']['home']}-{match['goals']['away']}",
                                "red_cards": len(red_cards),
                                "penalties": len(penalties),
                                "description": self._generate_drama_description(match, red_cards, penalties)
                            })
                            
            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump(drama_points, f)
                
        except Exception as e:
            print(f"Error fetching historical drama: {e}")
            
        return drama_points
        
    def _analyze_h2h(self, matches: List[Dict]) -> Dict:
        """Analyze head-to-head matches for patterns and statistics"""
        if not matches:
            return {}
            
        total_matches = len(matches)
        home_wins = sum(1 for m in matches if m["teams"]["home"]["winner"])
        away_wins = sum(1 for m in matches if m["teams"]["away"]["winner"])
        draws = total_matches - home_wins - away_wins
        
        total_goals = sum(m["goals"]["home"] + m["goals"]["away"] for m in matches)
        
        return {
            "total_matches": total_matches,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "avg_goals_per_match": total_goals / total_matches if total_matches > 0 else 0,
            "recent_form": self._analyze_recent_form(matches[:5])
        }
        
    def _analyze_recent_form(self, recent_matches: List[Dict]) -> str:
        """Analyze recent form between the teams"""
        if not recent_matches:
            return "No recent matches"
            
        form_guide = []
        for match in recent_matches:
            if match["teams"]["home"]["winner"]:
                form_guide.append("H")  # Home win
            elif match["teams"]["away"]["winner"]:
                form_guide.append("A")  # Away win
            else:
                form_guide.append("D")  # Draw
                
        return "".join(form_guide)
        
    def _generate_drama_description(self, match: Dict, red_cards: List[Dict], penalties: List[Dict]) -> str:
        """Generate a description of dramatic events in a match"""
        events = []
        
        if red_cards:
            events.append(f"{len(red_cards)} red card{'s' if len(red_cards) > 1 else ''}")
            
        if penalties:
            events.append(f"{len(penalties)} penalty{'ies' if len(penalties) > 1 else 'y'}")
            
        score = f"{match['goals']['home']}-{match['goals']['away']}"
        if match['goals']['home'] + match['goals']['away'] >= 5:
            events.append(f"high-scoring game ({score})")
            
        if events:
            return f"Match featured {', '.join(events)}"
        return "Regular match" 