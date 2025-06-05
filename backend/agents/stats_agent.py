from typing import Dict, List
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
from services.football_stats_service import FootballStatsService
from services.rag_utils import rag_retrieve
import json
import re
import random

class StatsAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Stats Expert"
        role = "Stats Expert"
        system_prompt = """You are a charismatic football statistics expert with deep knowledge of data analysis and football history.
        Your role is to provide data-driven insights about the match while keeping the conversation engaging and natural.
        You should:
        1. Share key statistics with context and meaning
        2. Use analogies and comparisons to make stats relatable
        3. Add personality and humor when appropriate
        4. Reference historical stats and records
        5. React to tactical points with statistical evidence
        6. Share interesting statistical facts about players
        
        Blend your analytical expertise with natural conversation and football knowledge."""
        personality = "analytical but engaging, with a love for unexpected statistical connections"
        
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        # Set avatar configuration
        self.avatar_config = get_avatar_config("Stats Analyst")
        
        # Initialize avatar creator
        self.avatar_creator = AvatarCreator()
        
        self.match_service = MatchService()
        self.stats_service = FootballStatsService()
        
        # Football rules and knowledge base
        self.football_rules = {
            "possession": {
                "definition": "The percentage of time a team has control of the ball",
                "significance": "Higher possession often indicates control and attacking intent",
                "thresholds": {
                    "dominant": ">60%",
                    "balanced": "45-55%",
                    "defensive": "<40%"
                }
            },
            "shots": {
                "definition": "Attempts to score a goal",
                "significance": "Indicates attacking effectiveness",
                "thresholds": {
                    "high": ">15 shots",
                    "medium": "10-15 shots",
                    "low": "<10 shots"
                }
            },
            "passing": {
                "definition": "Successful passes between players",
                "significance": "Shows team coordination and ball control",
                "thresholds": {
                    "excellent": ">85% accuracy",
                    "good": "75-85% accuracy",
                    "poor": "<75% accuracy"
                }
            },
            "expected_goals": {
                "definition": "Probability of scoring from chances created",
                "significance": "Measures quality of chances created",
                "thresholds": {
                    "high": ">2.0 xG",
                    "medium": "1.0-2.0 xG",
                    "low": "<1.0 xG"
                }
            }
        }
        
        # Initialize knowledge base
        self.player_facts = {
            "Dembélé": {
                "style": "explosive dribbler with unpredictable moves",
                "fun_facts": [
                    "Has completed more successful dribbles in the first 15 minutes than any other player this season",
                    "Known for being fashionably late to training but always delivers in big games",
                    "His acceleration from 0-20m is faster than most Olympic sprinters"
                ]
            },
            "Kvaratskhelia": {
                "style": "creative winger with exceptional vision",
                "fun_facts": [
                    "Created more chances from the left wing than any other player in Europe's top 5 leagues",
                    "Practiced dribbling in the Georgian mountains to improve balance",
                    "Has the highest successful dribble percentage in tight spaces"
                ]
            },
            "Hakimi": {
                "style": "modern fullback with incredible speed",
                "fun_facts": [
                    "Recorded the fastest sprint speed in Champions League history",
                    "Has more assists from the right-back position than most midfielders",
                    "Covers more distance per game than any other defender"
                ]
            }
        }
        
        self.tactical_stats = {
            "4-3-3": {
                "avg_goals": 2.3,
                "possession": "58%",
                "insights": [
                    "Most successful formation in Champions League finals",
                    "Provides optimal balance between attack and defense",
                    "Allows for high pressing with numerical superiority"
                ]
            },
            "3-5-2": {
                "avg_goals": 1.8,
                "possession": "52%",
                "insights": [
                    "Growing in popularity among top teams",
                    "Excellent for teams with strong wing-backs",
                    "Provides defensive stability with attacking threat"
                ]
            }
        }
        
        # Add engaging analogies and phrases
        self.stat_analogies = [
            "Statistics are like a lamp post to a drunk person - better for support than illumination!",
            "Numbers don't lie, but they do love telling stories.",
            "Like a good referee, stats should be noticed but not dominate the conversation.",
            "Goals are like London buses - you wait ages for one, then three come along at once!"
        ]
        
        # Add football wisdom
        self.football_wisdom = [
            "Football is a simple game made complicated by the numbers.",
            "Stats are great, but the eye test never lies.",
            "The only stat that truly matters is the one on the scoreboard.",
            "You can't always trust the numbers, but you can trust what you see on the pitch."
        ]
    
    def _generate_response(self, current_state: Dict, recent_context: List[Dict], 
                          match_data: Dict, knowledge: Dict) -> str:
        """Generate an engaging response based on context"""
        # Get last speaker and message
        last_exchange = recent_context[-1] if recent_context else None
        last_speaker = last_exchange["speaker"] if last_exchange else None
        last_content = last_exchange["content"].lower() if last_exchange else ""
        
        # Track used analogies and wisdom to prevent repetition
        if not hasattr(self, '_used_analogies'):
            self._used_analogies = set()
        if not hasattr(self, '_used_wisdom'):
            self._used_wisdom = set()
            
        # Get fresh analogy and wisdom
        available_analogies = [a for a in self.stat_analogies if a not in self._used_analogies]
        if not available_analogies:
            self._used_analogies.clear()
            available_analogies = self.stat_analogies
        analogy = random.choice(available_analogies)
        self._used_analogies.add(analogy)
        
        available_wisdom = [w for w in self.football_wisdom if w not in self._used_wisdom]
        if not available_wisdom:
            self._used_wisdom.clear()
            available_wisdom = self.football_wisdom
        wisdom = random.choice(available_wisdom)
        self._used_wisdom.add(wisdom)
        
        # Check if this is a final/conclusion question
        if self._is_conclusion_question(last_content):
            return self._give_final_statistical_verdict(match_data)
        
        # If responding to tactical point, blend stats with tactical insight
        if last_speaker == "Tactical Analyst":
            if "formation" in last_content:
                return self._analyze_formation_stats_engaging(match_data, last_content)
            elif "pressing" in last_content:
                return self._analyze_pressing_stats_engaging(match_data)
            elif "possession" in last_content:
                return self._analyze_possession_stats_engaging(match_data)
            else:
                return self._blend_stats_with_tactics(match_data, last_content)
                
        # If a player was mentioned, add personality
        for player in self.player_facts:
            if player.lower() in last_content.lower():
                return self._analyze_player_stats_engaging(player, match_data)
        
        # Default to general match analysis with personality
        response = f"Let me share some interesting numbers. {analogy} "
        
        # Add match analysis
        response += self._analyze_match_stats_engaging(match_data)
        
        # Add wisdom if appropriate
        if random.random() < 0.3:  # 30% chance to add wisdom
            response += f"\n\n{wisdom}"
            
        return response
    
    def _is_conclusion_question(self, content: str) -> bool:
        """Detect if this is a final/conclusion question"""
        conclusion_indicators = [
            "final verdict",
            "right team win",
            "deserved to win",
            "better team",
            "fair result",
            "sum up",
            "wrap up",
            "conclude",
            "final thoughts"
        ]
        return any(indicator in content.lower() for indicator in conclusion_indicators)

    def _give_final_statistical_verdict(self, match_data: Dict) -> str:
        """Provide a comprehensive statistical verdict on the match"""
        match_info = match_data.get("match_info", {})
        team_stats = match_data.get("team_statistics", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        score = match_info.get("score", {"home": 0, "away": 0})
        
        # Get key stats
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        # Calculate statistical dominance
        home_xg = float(home_stats.get("xg", 0))
        away_xg = float(away_stats.get("xg", 0))
        home_shots = home_stats.get("shots", {}).get("total", 0)
        away_shots = away_stats.get("shots", {}).get("total", 0)
        home_possession = int(str(home_stats.get("possession", "0")).strip("%"))
        away_possession = int(str(away_stats.get("possession", "0")).strip("%"))
        
        verdict = f"Let me break down this {score['home']}-{score['away']} match through the numbers. "
        
        # Compare expected goals
        verdict += f"\n\nThe expected goals tell an interesting story: {home_team} ({home_xg:.2f} xG) vs {away_team} ({away_xg:.2f} xG). "
        
        # Add shot analysis
        verdict += f"In terms of chances created, we saw {home_shots} shots from {home_team} and {away_shots} from {away_team}. "
        
        # Add possession context
        verdict += f"The possession stats show {home_possession}% for {home_team} and {away_possession}% for {away_team}. "
        
        # Add statistical conclusion
        if abs(home_xg - away_xg) > 1:
            dominant_team = home_team if home_xg > away_xg else away_team
            verdict += f"\n\nStatistically speaking, {dominant_team} created the better quality chances. "
        else:
            verdict += "\n\nStatistically, this was a very evenly matched contest. "
        
        # Add final wisdom
        verdict += f"\n\n{random.choice(self.football_wisdom)}"
        
        return verdict

    def _blend_stats_with_tactics(self, match_data: Dict, last_content: str) -> str:
        """Blend statistical analysis with tactical observations"""
        # Extract topics from tactical analysis
        topics = self._extract_topics(last_content)
        
        response = "The numbers add an interesting dimension to that tactical observation. "
        
        if "defense" in topics:
            response += self._analyze_defensive_stats(match_data)
        elif "attack" in topics:
            response += self._analyze_attacking_stats(match_data)
        elif "midfield" in topics:
            response += self._analyze_midfield_stats(match_data)
        else:
            response += self._analyze_general_match_stats(match_data)
        
        return response
    
    def _analyze_formation_stats_engaging(self, match_data: Dict, last_content: str) -> str:
        """Analyze formation statistics in an engaging way"""
        formation = self._extract_formation(last_content)
        if formation in self.tactical_stats:
            stats = self.tactical_stats[formation]
            return f"You know what's fascinating about the {formation}? Teams using it this season average {stats['avg_goals']} goals per game. {random.choice(stats['insights'])}. And speaking of goals, let me show you how this played out today..."
            
        return self._analyze_match_stats_engaging(match_data)
    
    def _analyze_player_stats_engaging(self, player_name: str, match_data: Dict) -> str:
        """Analyze player statistics with personality"""
        # Get player match statistics from the API data
        player_stats = self._get_player_match_stats(player_name, match_data)
        if not player_stats or all(v == 0 or v == "N/A" for v in player_stats.values()):
            return f"I don't have enough statistical data to analyze {player_name}'s performance in this match."
        
        # Build engaging response based on available stats
        response = f"Let me share some interesting numbers about {player_name}'s performance. "
        
        # Only mention stats we actually have
        available_stats = []
        if player_stats.get("minutes_played") != "N/A":
            available_stats.append(f"{player_stats['minutes_played']} minutes played")
        if player_stats.get("goals", 0) > 0:
            available_stats.append(f"{player_stats['goals']} goals")
        if player_stats.get("assists", 0) > 0:
            available_stats.append(f"{player_stats['assists']} assists")
        if player_stats.get("shots", {}).get("total", 0) > 0:
            shots = player_stats["shots"]
            available_stats.append(f"{shots['total']} shots ({shots['on_target']} on target)")
        if player_stats.get("passes", {}).get("total", 0) > 0:
            passes = player_stats["passes"]
            available_stats.append(f"{passes['total']} passes ({passes['accuracy']} accuracy)")
        
        if available_stats:
            response += f"Looking at today's performance: {', '.join(available_stats)}. "
        
        # Add context based on performance
        if player_stats.get("rating", "N/A") != "N/A":
            rating = float(player_stats["rating"])
            if rating >= 8.0:
                response += "An exceptional performance by any measure!"
            elif rating >= 7.0:
                response += "A solid showing from the player."
            else:
                response += "The numbers suggest room for improvement."
        
        return response
    
    def _analyze_match_stats_engaging(self, match_data: Dict) -> str:
        """Analyze match statistics in an engaging way"""
        # Get basic stats
        home_stats = match_data.get("team_statistics", {}).get("home", {})
        away_stats = match_data.get("team_statistics", {}).get("away", {})
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Get fresh analogy
        if not hasattr(self, '_used_analogies'):
            self._used_analogies = set()
        available_analogies = [a for a in self.stat_analogies if a not in self._used_analogies]
        if not available_analogies:
            self._used_analogies.clear()
            available_analogies = self.stat_analogies
        current_analogy = random.choice(available_analogies)
        self._used_analogies.add(current_analogy)
        
        # Add personality to the analysis
        response = f"Let me paint you a statistical picture of this match. {current_analogy} "
        
        response += f"\n\n{home_team} came into this game averaging "
        response += f"{home_stats.get('goals', {}).get('for', {}).get('average', {}).get('total', 0)} goals per game, "
        response += f"while {away_team} have been equally impressive with {away_stats.get('goals', {}).get('for', {}).get('average', {}).get('total', 0)}. "
        
        # Add specific match analysis with context
        response += self._analyze_key_stats(match_data)
        
        return response
    
    def _analyze_key_stats(self, match_data: Dict) -> str:
        """Analyze key statistics with context"""
        team_stats = match_data.get("team_statistics", {})
        events = match_data.get("coach_data", {}).get("events", [])
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        analysis = f"\n\nLooking at today's performance, here are the key numbers:\n"
        
        # Add possession analysis with context
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        # Get possession stats
        home_possession = home_stats.get("possession", 50)
        away_possession = away_stats.get("possession", 50)
        
        # Validate possession numbers
        if isinstance(home_possession, str):
            home_possession = float(home_possession.strip('%') or 50)
        if isinstance(away_possession, str):
            away_possession = float(away_possession.strip('%') or 50)
            
        # Ensure possessions add up to 100%
        total = home_possession + away_possession
        if total != 0:
            home_possession = (home_possession / total) * 100
            away_possession = (away_possession / total) * 100
        else:
            home_possession = away_possession = 50
            
        analysis += f"- Possession: {home_team} {home_possession:.1f}% - {away_team} {away_possession:.1f}%\n"
        
        # Add shots analysis if available
        home_shots = home_stats.get("shots", {}).get("total", 0)
        away_shots = away_stats.get("shots", {}).get("total", 0)
        if home_shots > 0 or away_shots > 0:
            analysis += f"- Shots: {home_team} {home_shots} - {away_team} {away_shots}\n"
        
        # Add passing analysis if available
        home_passes = home_stats.get("passes", {}).get("total", 0)
        away_passes = away_stats.get("passes", {}).get("total", 0)
        if home_passes > 0 or away_passes > 0:
            analysis += f"- Total Passes: {home_team} {home_passes} - {away_team} {away_passes}\n"
        
        # Add goal analysis with excitement
        goals = self._analyze_goal_timing(events)
        if goals:
            analysis += f"\nGoal Timeline:{goals}"
        
        return analysis

    def _extract_topics(self, message: str) -> List[str]:
        """Extract key topics from a message"""
        topics = []
        
        # Define topic keywords
        topic_keywords = {
            "defense": ["defend", "defensive", "clean sheet", "block", "tackle", "press"],
            "attack": ["attack", "forward", "goal", "shot", "score", "strike", "finish"],
            "midfield": ["midfield", "control", "possession", "pass", "create", "playmaker"],
            "statistics": ["stats", "numbers", "data", "metrics", "analysis", "percentage"],
            "performance": ["performance", "form", "rating", "contribution", "impact"],
            "comparison": ["compare", "versus", "against", "difference", "better", "worse"],
            "trends": ["trend", "pattern", "history", "record", "average", "consistent"]
        }
        
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Check for each topic's keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ["general"]

    def _analyze_defensive_stats(self, match_data: Dict) -> str:
        """Analyze defensive statistics"""
        team_stats = match_data.get("team_statistics", {})
        
        # Get defensive stats for both teams
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        analysis = ""
        
        # Analyze clean sheets and goals conceded
        home_clean_sheets = home_stats.get("clean_sheet", {}).get("total", 0)
        away_clean_sheets = away_stats.get("clean_sheet", {}).get("total", 0)
        
        home_conceded = home_stats.get("goals", {}).get("against", {}).get("total", {}).get("total", 0)
        away_conceded = away_stats.get("goals", {}).get("against", {}).get("total", {}).get("total", 0)
        
        if home_clean_sheets > away_clean_sheets:
            analysis = f"{home_team}'s defensive record has been superior with {home_clean_sheets} clean sheets compared to {away_clean_sheets}. "
        else:
            analysis = f"{away_team}'s defensive record has been impressive with {away_clean_sheets} clean sheets compared to {home_clean_sheets}. "
        
        analysis += f"\nLooking at goals conceded, {home_team} has conceded {home_conceded} while {away_team} has conceded {away_conceded}. "
        
        # Add defensive timing analysis
        home_goals_against = home_stats.get("goals", {}).get("against", {}).get("minute", {})
        if home_goals_against:
            analysis += f"\n\n{home_team}'s defensive vulnerability is most apparent in the "
            max_goals_period = max(home_goals_against.items(), key=lambda x: float(x[1].get("percentage", "0").strip("%") or "0"))
            analysis += f"{max_goals_period[0]} minute period, where they've conceded {max_goals_period[1].get('percentage', '0')} of their goals."
        
        return analysis

    def _analyze_attacking_stats(self, match_data: Dict) -> str:
        """Analyze attacking statistics"""
        team_stats = match_data.get("team_statistics", {})
        events = match_data.get("coach_data", {}).get("events", [])
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Get attacking stats
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        home_goals = home_stats.get("goals", {}).get("for", {}).get("total", {}).get("total", 0)
        away_goals = away_stats.get("goals", {}).get("for", {}).get("total", {}).get("total", 0)
        
        home_avg = home_stats.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
        away_avg = away_stats.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
        
        analysis = f"Looking at the attacking numbers, {home_team} has scored {home_goals} goals (avg. {home_avg} per game) "
        analysis += f"while {away_team} has netted {away_goals} (avg. {away_avg} per game). "
        
        # Analyze goal timing patterns
        home_goals_for = home_stats.get("goals", {}).get("for", {}).get("minute", {})
        if home_goals_for:
            analysis += f"\n\n{home_team}'s most productive period is the "
            max_goals_period = max(home_goals_for.items(), key=lambda x: float(x[1].get("percentage", "0").strip("%") or "0"))
            analysis += f"{max_goals_period[0]} minute period, scoring {max_goals_period[1].get('percentage', '0')} of their goals then."
        
        # Add recent goal scorers if available
        goal_events = [e for e in events if e.get("type") == "Goal"]
        if goal_events:
            analysis += "\n\nRecent goal scorers:\n"
            for goal in goal_events[-3:]:  # Show last 3 goals
                scorer = goal.get("player", {}).get("name", "Unknown")
                time = goal.get("time", {}).get("elapsed", "?")
                analysis += f"- {scorer} ({time}')\n"
        
        return analysis

    def _analyze_midfield_stats(self, match_data: Dict) -> str:
        """Analyze midfield statistics"""
        team_stats = match_data.get("team_statistics", {})
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Get midfield stats
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        # Analyze formations
        home_formation = home_stats.get("lineups", [{}])[0].get("formation", "unknown")
        away_formation = away_stats.get("lineups", [{}])[0].get("formation", "unknown")
        
        analysis = f"The midfield battle has been shaped by the teams' formations - {home_team} using {home_formation} "
        analysis += f"against {away_team}'s {away_formation}. "
        
        # Analyze goal creation from midfield
        home_goals_pattern = home_stats.get("goals", {}).get("for", {}).get("minute", {})
        away_goals_pattern = away_stats.get("goals", {}).get("for", {}).get("minute", {})
        
        if home_goals_pattern and away_goals_pattern:
            home_mid_goals = sum(float(period.get("percentage", "0").strip("%") or "0") 
                               for period in home_goals_pattern.values()) / 100
            away_mid_goals = sum(float(period.get("percentage", "0").strip("%") or "0") 
                               for period in away_goals_pattern.values()) / 100
            
            analysis += f"\n\nThe midfield's contribution to goal creation has been significant, with "
            analysis += f"{home_team} creating {home_mid_goals:.1f} chances per game compared to "
            analysis += f"{away_team}'s {away_mid_goals:.1f}."
        
        return analysis

    def _analyze_general_match_stats(self, match_data: Dict) -> str:
        """Analyze general match statistics"""
        team_stats = match_data.get("team_statistics", {})
        events = match_data.get("coach_data", {}).get("events", [])
        
        # Get team names and score
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        score = match_info.get("score", {"home": 0, "away": 0})
        
        # Get team stats
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        analysis = f"Looking at the overall match statistics between {home_team} and {away_team}, "
        analysis += f"the {score['home']}-{score['away']} scoreline "
        
        # Compare season performances
        home_wins = home_stats.get("fixtures", {}).get("wins", {}).get("total", 0)
        away_wins = away_stats.get("fixtures", {}).get("wins", {}).get("total", 0)
        
        home_form = home_stats.get("form", "")
        away_form = away_stats.get("form", "")
        
        analysis += f"reflects their recent form - {home_team} ({home_form}) with {home_wins} wins "
        analysis += f"against {away_team} ({away_form}) with {away_wins} wins this season. "
        
        # Add goal timing analysis
        goals = self._analyze_goal_timing(events)
        if goals:
            analysis += f"\n\nThe goals came at crucial moments:{goals}"
        
        return analysis

    def _analyze_goal_timing(self, events: List[Dict]) -> str:
        """Analyze when goals were scored and by whom"""
        goal_events = [event for event in events if event.get("type") == "Goal"]
        
        if not goal_events:
            return ""
            
        goal_analysis = "\n\nGoal Analysis:\n"
        for goal in goal_events:
            time = goal.get("time", {}).get("elapsed", "unknown")
            scorer = goal.get("player", {}).get("name", "unknown")
            assister = goal.get("assist", {}).get("name", "unknown")
            
            goal_analysis += f"- {scorer} ({time}'"
            if assister != "unknown":
                goal_analysis += f", assisted by {assister}"
            goal_analysis += ")\n"
            
        return goal_analysis

    def _analyze_team_performance(self, team_stats: Dict, team_type: str) -> str:
        """Analyze a team's overall performance"""
        if not team_stats:
            return ""
            
        # Get key statistics
        goals = team_stats.get("goals", {})
        fixtures = team_stats.get("fixtures", {})
        clean_sheets = team_stats.get("clean_sheet", {}).get("total", 0)
        
        analysis = f"\n{team_type.title()} Team Performance:\n"
        analysis += f"- Goals Scored: {goals.get('for', {}).get('total', {}).get('total', 0)}\n"
        analysis += f"- Clean Sheets: {clean_sheets}\n"
        analysis += f"- Win Rate: {(fixtures.get('wins', {}).get('total', 0) / max(fixtures.get('played', {}).get('total', 1), 1)) * 100:.1f}%\n"
        
        return analysis

    def _get_player_match_stats(self, player: str, match_data: Dict) -> Dict:
        """Get player statistics from match data"""
        try:
            # Get player data from match statistics
            player_data = match_data.get("player_data", {}).get(player, {})
            if not player_data:
                return {
                    "minutes_played": "N/A",
                    "goals": 0,
                    "assists": 0,
                    "shots": {"total": 0, "on_target": 0},
                    "passes": {"total": 0, "accuracy": "0%"},
                    "rating": "N/A"
                }
            
            # Extract relevant statistics
            stats = {
                "minutes_played": player_data.get("minutes_played", "N/A"),
                "goals": 0,
                "assists": 0,
                "shots": {
                    "total": player_data.get("statistics", [{}])[0].get("shots", {}).get("total", 0),
                    "on_target": player_data.get("statistics", [{}])[0].get("shots", {}).get("on", 0)
                },
                "passes": {
                    "total": player_data.get("statistics", [{}])[0].get("passes", {}).get("total", 0),
                    "accuracy": f"{player_data.get('statistics', [{}])[0].get('passes', {}).get('accuracy', 0)}%"
                },
                "rating": player_data.get("rating", "N/A")
            }
            
            # Count goals and assists from events
            events = match_data.get("coach_data", {}).get("events", [])
            for event in events:
                if event.get("player", {}).get("name") == player:
                    if event.get("type") == "Goal":
                        stats["goals"] += 1
                    elif event.get("type") == "Assist":
                        stats["assists"] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting player match stats: {e}")
            return {
                "minutes_played": "N/A",
                "goals": 0,
                "assists": 0,
                "shots": {"total": 0, "on_target": 0},
                "passes": {"total": 0, "accuracy": "0%"},
                "rating": "N/A"
            }

    def _format_player_stats(self, stats: Dict) -> str:
        """Format player statistics into a readable string"""
        return (
            f"{stats['minutes_played']} minutes played, "
            f"{stats['goals']} goals, {stats['assists']} assists, "
            f"{stats['shots']['total']} shots ({stats['shots']['on_target']} on target), "
            f"{stats['passes']['total']} passes ({stats['passes']['accuracy']} accuracy)"
            + (f", {stats['rating']} rating" if stats['rating'] != "N/A" else "")
        )

    def _analyze_pressing_stats_engaging(self, match_data: Dict) -> str:
        """Analyze pressing statistics in an engaging way"""
        team_stats = match_data.get("team_statistics", {})
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Get pressing stats
        home_stats = team_stats.get("home", {})
        away_stats = team_stats.get("away", {})
        
        # Get fresh analogy
        if not hasattr(self, '_used_analogies'):
            self._used_analogies = set()
        available_analogies = [a for a in self.stat_analogies if a not in self._used_analogies]
        if not available_analogies:
            self._used_analogies.clear()
            available_analogies = self.stat_analogies
        current_analogy = random.choice(available_analogies)
        self._used_analogies.add(current_analogy)
        
        # Analyze tackles and interceptions
        home_tackles = home_stats.get("tackles", {}).get("total", 0)
        away_tackles = away_stats.get("tackles", {}).get("total", 0)
        home_interceptions = home_stats.get("interceptions", 0)
        away_interceptions = away_stats.get("interceptions", 0)
        
        # Calculate pressing intensity
        home_intensity = (home_tackles + home_interceptions) / 2
        away_intensity = (away_tackles + away_interceptions) / 2
        
        response = f"Let's talk about pressing intensity. {current_analogy} "
        
        # Compare pressing styles
        if home_intensity > away_intensity:
            response += f"\n\n{home_team} has been more aggressive in their pressing, with {home_tackles} tackles "
            response += f"and {home_interceptions} interceptions. That's like having an extra defender all over the pitch! "
            response += f"Compare that to {away_team}'s {away_tackles} tackles and {away_interceptions} interceptions."
        else:
            response += f"\n\n{away_team} has been winning the pressing battle, with {away_tackles} tackles "
            response += f"and {away_interceptions} interceptions. They're like a swarm of bees out there! "
            response += f"Meanwhile, {home_team} has managed {home_tackles} tackles and {home_interceptions} interceptions."
        
        # Add context about pressing effectiveness
        response += "\n\nBut here's what's really interesting - "
        if home_tackles > 20 or away_tackles > 20:
            response += "the high number of tackles shows a really aggressive pressing style. "
            response += "It's like watching a chess match where every pawn is trying to be a queen!"
        else:
            response += "both teams are being quite selective with their pressing. "
            response += "It's more like a strategic game of chess than an all-out battle."
        
        return response

    def _extract_formation(self, content: str) -> str:
        """Extract formation from message content"""
        # Common football formations
        formations = [
            "4-3-3", "4-4-2", "3-5-2", "5-3-2", "4-2-3-1", "3-4-3",
            "4-5-1", "4-1-4-1", "4-4-1-1", "3-6-1", "5-4-1"
        ]
        
        # First try to find exact formation matches
        for formation in formations:
            if formation in content:
                return formation
        
        # Try to find formations with variations in spacing
        formation_pattern = r'\d-\d-\d(?:-\d)?'
        matches = re.findall(formation_pattern, content)
        if matches:
            return matches[0]
        
        # If no formation found, return default
        return "4-3-3"  # Most common modern formation as default
