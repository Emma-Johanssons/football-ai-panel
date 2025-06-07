"""
Free data collection service using publicly available sources
"""
import feedparser
import praw
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import os
from datetime import datetime, timedelta
import json

class FreeDataCollector:
    def __init__(self):
        # RSS feeds for major sports news
        self.news_feeds = {
            "bbc_sport": "http://feeds.bbci.co.uk/sport/football/rss.xml",
            "goal_com": "https://www.goal.com/feeds/en/news",
            "sky_sports": "https://www.skysports.com/rss/football",
        }
        
        # Initialize Reddit client (optional - needs free Reddit API credentials)
        self.reddit = None
        if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="football-ai-panel:v1.0"
            )
            
        # Cache directory for storing scraped data
        self.cache_dir = "data/scraped_data"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_cached_data(self, cache_key: str, max_age_hours: int = 1) -> Dict:
        """Get cached data if it exists and is not too old"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if datetime.fromisoformat(cached['timestamp']) > datetime.now() - timedelta(hours=max_age_hours):
                    return cached['data']
        return None
        
    def save_to_cache(self, cache_key: str, data: Dict):
        """Save data to cache with timestamp"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f)
            
    def get_latest_news(self, team_name: str) -> List[Dict]:
        """Get latest news about a team from RSS feeds"""
        cache_key = f"news_{team_name.lower().replace(' ', '_')}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        news_items = []
        for source, feed_url in self.news_feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    if team_name.lower() in entry.title.lower() or team_name.lower() in entry.description.lower():
                        news_items.append({
                            'title': entry.title,
                            'summary': entry.description,
                            'link': entry.link,
                            'published': entry.published,
                            'source': source
                        })
            except Exception as e:
                print(f"Error fetching {source} feed: {str(e)}")
                continue
                
        self.save_to_cache(cache_key, news_items)
        return news_items
        
    def get_fan_discussions(self, team_name: str) -> List[Dict]:
        """Get fan discussions from Reddit r/soccer"""
        cache_key = f"discussions_{team_name.lower().replace(' ', '_')}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        discussions = []
        
        if self.reddit:
            try:
                # Search r/soccer for team discussions
                subreddit = self.reddit.subreddit('soccer')
                for post in subreddit.search(team_name, limit=10, sort='new'):
                    discussions.append({
                        'title': post.title,
                        'url': f"https://reddit.com{post.permalink}",
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc
                    })
            except Exception as e:
                print(f"Error fetching Reddit discussions: {str(e)}")
        
        # If no Reddit API or as backup, scrape r/soccer
        if not discussions:
            try:
                url = f"https://old.reddit.com/r/soccer/search?q={team_name}&restrict_sr=on&sort=new"
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for post in soup.find_all('div', class_='thing'):
                    if post.get('data-domain') == 'self.soccer':
                        discussions.append({
                            'title': post.find('a', class_='title').text,
                            'url': f"https://reddit.com{post.get('data-permalink')}",
                            'score': post.find('div', class_='score').get('title', '0'),
                            'num_comments': post.find('a', class_='comments').text.split()[0],
                            'created_utc': time.time()  # Approximate time
                        })
            except Exception as e:
                print(f"Error scraping Reddit: {str(e)}")
                
        self.save_to_cache(cache_key, discussions)
        return discussions
        
    def get_team_stats(self, team_name: str) -> Dict:
        """Get team statistics from public sources"""
        cache_key = f"stats_{team_name.lower().replace(' ', '_')}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        stats = {}
        try:
            # Scrape stats from a public source like WhoScored or Transfermarkt
            # This is a placeholder - implement actual scraping logic
            url = f"https://www.whoscored.com/Teams/{team_name}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example scraping logic - adjust based on actual website structure
            stats = {
                'team': team_name,
                'league_position': 'N/A',
                'points': 'N/A',
                'goals_scored': 'N/A',
                'goals_conceded': 'N/A'
            }
            
        except Exception as e:
            print(f"Error fetching team stats: {str(e)}")
            
        self.save_to_cache(cache_key, stats)
        return stats
        
    def get_head_to_head(self, team1: str, team2: str) -> Dict:
        """Get head-to-head statistics between two teams"""
        cache_key = f"h2h_{team1.lower().replace(' ', '_')}_{team2.lower().replace(' ', '_')}"
        cached = self.get_cached_data(cache_key)
        if cached:
            return cached
            
        h2h_stats = {
            'team1': team1,
            'team2': team2,
            'last_meetings': [],
            'overall_stats': {
                'wins_team1': 0,
                'wins_team2': 0,
                'draws': 0
            }
        }
        
        try:
            # Scrape head-to-head data from a public source
            # This is a placeholder - implement actual scraping logic
            url = f"https://www.worldfootball.net/teams/{team1}/{team2}/11/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example scraping logic - adjust based on actual website structure
            
        except Exception as e:
            print(f"Error fetching head-to-head stats: {str(e)}")
            
        self.save_to_cache(cache_key, h2h_stats)
        return h2h_stats
        
    def collect_all_data(self, team1: str, team2: str) -> Dict:
        """Collect all available data for two teams"""
        return {
            'team1': {
                'news': self.get_latest_news(team1),
                'discussions': self.get_fan_discussions(team1),
                'stats': self.get_team_stats(team1)
            },
            'team2': {
                'news': self.get_latest_news(team2),
                'discussions': self.get_fan_discussions(team2),
                'stats': self.get_team_stats(team2)
            },
            'head_to_head': self.get_head_to_head(team1, team2)
        } 