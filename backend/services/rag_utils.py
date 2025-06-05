import os
import requests
import openai
import feedparser
from typing import Tuple, Dict, List

def get_api_football_stats(match_id: str) -> Dict:
    """Get comprehensive football statistics from API-Football"""
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
        return {"error": f"Error fetching stats: {str(e)}"}

def get_football_rules() -> List[str]:
    """Get relevant football rules and regulations"""
    rules = [
        "Offside Rule: A player is in an offside position if they are nearer to the opponent's goal line than both the ball and the second-last opponent.",
        "Yellow Card: Given for unsporting behavior, dissent, persistent infringement, or delaying the restart of play.",
        "Red Card: Given for serious foul play, violent conduct, spitting, denying an obvious goal-scoring opportunity, or receiving a second yellow card.",
        "Penalty Kick: Awarded when a foul occurs inside the penalty area.",
        "Free Kick: Awarded for fouls and misconduct outside the penalty area.",
        "Throw-in: Awarded when the ball goes out of play over the touchline.",
        "Goal Kick: Awarded when the ball goes out of play over the goal line, last touched by an attacking player.",
        "Corner Kick: Awarded when the ball goes out of play over the goal line, last touched by a defending player.",
        "Handball: A foul when a player deliberately handles the ball.",
        "Dangerous Play: Any action that could potentially cause injury to another player."
    ]
    return rules

def get_tactical_knowledge() -> List[str]:
    """Get tactical football knowledge"""
    tactics = [
        "Formations: Common formations include 4-4-2, 4-3-3, 3-5-2, and 4-2-3-1.",
        "Pressing: A defensive tactic where players actively try to win the ball back high up the pitch.",
        "Counter-attack: A quick transition from defense to attack after winning the ball.",
        "Possession-based play: A style focused on maintaining control of the ball.",
        "High defensive line: Defenders position themselves high up the pitch to compress space.",
        "Man-to-man marking: Each defender is assigned to mark a specific opponent.",
        "Zonal marking: Defenders cover specific areas of the pitch rather than specific players.",
        "False nine: A forward who drops deep to create space for other attackers.",
        "Wing play: Attacking strategy focused on using the wide areas of the pitch.",
        "Tiki-taka: A style characterized by short passing and movement, working the ball through various channels."
    ]
    return tactics

def get_historical_context(team1: str, team2: str) -> List[str]:
    """Get historical context about matches between two teams"""
    try:
        # Search for news about the teams
        query = f"{team1} vs {team2} football rivalry history"
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(url)
        
        # Get the most relevant articles
        articles = []
        for entry in feed.entries[:5]:
            articles.append(f"{entry.title}: {entry.summary}")
            
        return articles
    except Exception as e:
        return [f"Error fetching historical context: {str(e)}"]

def rag_retrieve(match_id: str, query: str, role: str = None) -> Tuple[Dict, List[str], List[str]]:
    """Retrieve relevant information based on the query and role"""
    # Get match statistics
    stats = get_api_football_stats(match_id)
    
    # Get role-specific knowledge
    rules = get_football_rules() if role == "Stats Analyst" else []
    tactics = get_tactical_knowledge() if role == "Football Coach" else []
    
    # Get historical context if we have team names
    historical = []
    if stats.get("match_info"):
        home_team = stats["match_info"]["home_team"]
        away_team = stats["match_info"]["away_team"]
        historical = get_historical_context(home_team, away_team)
    
    return stats, rules, tactics, historical 