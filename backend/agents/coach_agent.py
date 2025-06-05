from typing import Dict, List
import os
import requests
from dotenv import load_dotenv
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
import random

# Load environment variables
load_dotenv()

class CoachAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Tactical Analyst"
        role = "Tactical Analyst"
        system_prompt = """You are an experienced football tactical analyst with a professional playing career.
        Your role is to provide tactical insights while making them engaging and relatable.
        You should:
        1. Draw from your playing experience
        2. Use analogies and examples from famous matches
        3. Challenge statistical views with practical insights
        4. Share insider knowledge about tactics and training
        5. Make tactical concepts easy to understand
        6. Add personality and humor when appropriate
        
        Blend your tactical expertise with natural conversation and real football experience."""
        personality = "experienced professional with practical insights"
        
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        self.match_service = MatchService()
        
        # D-ID API configuration
        self.did_api_key = os.getenv('DID_API_KEY')
        self.did_base_url = "https://api.d-id.com"
        self.coach_image_url = os.getenv('COACH_AVATAR_URL')  # Get avatar URL from environment
        
        # Set avatar configuration
        self.avatar_config = get_avatar_config("Football Coach")  # Use the correct role name from avatar_mapping.py
        
        # Initialize avatar creator
        self.avatar_creator = AvatarCreator()
        
        # Initialize tactical knowledge base
        self.tactical_insights = {
            "formations": {
                "4-3-3": {
                    "strengths": [
                        "Excellent for possession-based play",
                        "Strong pressing capabilities",
                        "Width in attack through wingers"
                    ],
                    "weaknesses": [
                        "Can be vulnerable to counter-attacks",
                        "Requires technically skilled midfielders",
                        "Wide areas can be exposed"
                    ],
                    "famous_examples": [
                        "Guardiola's Barcelona",
                        "Klopp's Liverpool",
                        "Modern PSG setup"
                    ]
                },
                "3-5-2": {
                    "strengths": [
                        "Strong defensive coverage",
                        "Effective counter-attacking",
                        "Numerical advantage in midfield"
                    ],
                    "weaknesses": [
                        "Can struggle against wide attacks",
                        "Requires specific player profiles",
                        "Transition phases can be challenging"
                    ],
                    "famous_examples": [
                        "Conte's Chelsea",
                        "Allegri's Juventus",
                        "Inter's recent success"
                    ]
                }
            },
            "playing_styles": {
                "high_press": {
                    "characteristics": [
                        "Aggressive forward pressure",
                        "High defensive line",
                        "Quick transitions"
                    ],
                    "requirements": [
                        "Physically fit squad",
                        "Technical defenders",
                        "Coordinated movement"
                    ],
                    "examples": [
                        "Klopp's gegenpressing",
                        "Bayern's dominance",
                        "Ajax's total football"
                    ]
                },
                "possession": {
                    "characteristics": [
                        "Patient buildup",
                        "Positional play",
                        "Control through ball retention"
                    ],
                    "requirements": [
                        "Technical midfielders",
                        "Intelligent movement",
                        "Tactical discipline"
                    ],
                    "examples": [
                        "Guardiola's teams",
                        "Spain's tiki-taka",
                        "Arsenal's beautiful game"
                    ]
                }
            }
        }
        
        # Add coaching wisdom
        self.coaching_wisdom = [
            "Sometimes the best tactic is simply letting your players express themselves.",
            "Football is played on grass, not on paper with statistics.",
            "The best formation is the one that suits your players, not the other way around.",
            "In big games, it's not about the system, it's about the moments."
        ]
        
        # Add match analogies
        self.match_analogies = [
            "This reminds me of the 2005 Champions League final - tactics went out the window!",
            "It's like watching the old Arsenal Invincibles - they make it look so simple.",
            "This is classic Italian catenaccio meets modern pressing.",
            "Reminds me of how we used to set up against the big teams - respect but no fear."
        ]
    
    def create_video_response(self, text: str) -> str:
        """Create a video response using D-ID API"""
        if not self.did_api_key:
            return None
            
        headers = {
            'Authorization': f'Basic {self.did_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "source_url": self.coach_image_url,
            "script": {
                "type": "text",
                "provider": {
                    "type": "microsoft",
                    "voice_id": "sv-SE-MattiasNeural"
                },
                "input": text
            }
        }
        
        try:
            print("Creating coach video response...")
            response = requests.post(f"{self.did_base_url}/talks", headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                talk_id = result.get('id')
                
                if talk_id:
                    # Wait for video to be ready
                    video_url = self.wait_for_video(talk_id)
                    if video_url:
                        return video_url
            
            print(f"❌ Failed to create video: {response.text}")
            return None
            
        except Exception as e:
            print(f"❌ Error creating video: {e}")
            return None
    
    def wait_for_video(self, talk_id: str, max_attempts: int = 30) -> str:
        """Wait for the video to be ready"""
        headers = {
            'Authorization': f'Basic {self.did_api_key}',
            'Content-Type': 'application/json'
        }
        
        import time
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.did_base_url}/talks/{talk_id}", headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'done':
                        return result.get('result_url')
                    elif status in ['created', 'started']:
                        print(f"⏳ Video processing... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(5)
                    else:
                        print(f"❌ Unexpected status: {status}")
                        return None
                        
            except Exception as e:
                print(f"❌ Error checking video status: {e}")
                return None
        
        return None

    def _generate_response(self, current_state: Dict, recent_context: List[Dict], 
                          match_data: Dict, knowledge: Dict) -> str:
        """Generate an engaging tactical response"""
        # Get last speaker and message
        last_exchange = recent_context[-1] if recent_context else None
        last_speaker = last_exchange["speaker"] if last_exchange else None
        last_content = last_exchange["content"].lower() if last_exchange else ""
        
        # Check if this is a final/conclusion question
        if self._is_conclusion_question(last_content):
            return self._give_final_verdict(match_data)
        
        # If responding to stats, blend tactical insight with data
        if last_speaker == "Stats Expert":
            # Extract key stats mentioned
            if "possession" in last_content:
                return "Those possession numbers are interesting, but what really caught my eye was how they used the ball. " + self._analyze_possession_tactically(match_data)
            elif "shots" in last_content:
                return "The shot count tells part of the story, but let's look at the quality of chances created. " + self._analyze_shooting_tactically(match_data)
            elif any(name.lower() in last_content.lower() for name in self._get_player_names(match_data)):
                return self._analyze_player_tactical_role(match_data, last_content)
            else:
                return "The numbers are fascinating, but let me add some tactical context. " + self._analyze_match_tactics_engaging(match_data)
            
        # If a specific formation was mentioned
        for formation in self.tactical_insights["formations"]:
            if formation in last_content:
                return self._analyze_formation_engaging(formation, match_data)
                
        # If discussing playing style
        if any(style in last_content for style in self.tactical_insights["playing_styles"]):
            return self._analyze_playing_style_engaging(match_data)
            
        # Default to general tactical analysis
        return self._analyze_match_tactics_engaging(match_data)
        
    def _blend_tactics_with_stats(self, match_data: Dict, last_content: str) -> str:
        """Blend tactical insights with statistical points"""
        response = "You know, the numbers are interesting, but let me tell you what I see on the pitch. "
        response += f"{random.choice(self.coaching_wisdom)} "
        
        # Add tactical context to statistical points
        if "possession" in last_content:
            response += self._analyze_possession_tactically(match_data)
        elif "shots" in last_content:
            response += self._analyze_shooting_tactically(match_data)
        else:
            response += self._analyze_general_tactics(match_data)
            
        return response
        
    def _analyze_formation_engaging(self, formation: str, match_data: Dict) -> str:
        """Analyze formation in an engaging way"""
        formation_info = self.tactical_insights["formations"][formation]
        
        response = f"Speaking of the {formation}, it reminds me of {random.choice(formation_info['famous_examples'])}. "
        response += "But what's really interesting is how they've adapted it. "
        
        # Add specific match context
        match_formation = self._get_team_formation(match_data)
        if match_formation:
            response += f"\n\nIn today's game, they've used it to {self._analyze_formation_effectiveness(match_data)}. "
            response += f"One thing that caught my eye was {self._analyze_key_tactical_moment(match_data)}."
            
        return response
        
    def _analyze_playing_style_engaging(self, match_data: Dict) -> str:
        """Analyze playing style with engaging insights"""
        style = self._determine_dominant_style(match_data)
        if style in self.tactical_insights["playing_styles"]:
            style_info = self.tactical_insights["playing_styles"][style]
            
            response = f"What we're seeing here is reminiscent of {random.choice(style_info['examples'])}. "
            response += f"\n\nThe key elements are {', '.join(style_info['characteristics'][:2])}. "
            response += f"\n\nBut what makes it special is {self._analyze_style_adaptation(match_data)}."
            
            return response
            
        return self._analyze_match_tactics_engaging(match_data)
        
    def _analyze_match_tactics_engaging(self, match_data: Dict) -> str:
        """Provide engaging tactical match analysis"""
        response = f"{random.choice(self.match_analogies)} "
        
        # Add specific tactical insights
        key_tactics = self._analyze_key_tactics(match_data)
        if key_tactics:
            response += f"\n\nWhat's fascinating is {key_tactics}. "
            response += f"It reminds me of {self._get_tactical_comparison(match_data)}."
            
        # Add practical insight
        response += f"\n\n{random.choice(self.coaching_wisdom)}"
        
        return response
        
    def _analyze_key_tactics(self, match_data: Dict) -> str:
        """Analyze key tactical aspects of the match"""
        # Implementation of tactical analysis
        return "how they've adapted their pressing game to counter the opposition's build-up play"
        
    def _get_tactical_comparison(self, match_data: Dict) -> str:
        """Get relevant tactical comparison"""
        # Implementation of tactical comparison
        return "how we used to set up against strong attacking teams - sometimes the best offense is a solid defensive structure"
        
    def _determine_dominant_style(self, match_data: Dict) -> str:
        """Determine the dominant playing style"""
        # Implementation of style analysis
        return "high_press"
        
    def _analyze_style_adaptation(self, match_data: Dict) -> str:
        """Analyze how the style has been adapted"""
        # Implementation of style adaptation analysis
        return "how they've modified the traditional approach to suit their players' strengths"
        
    def _get_team_formation(self, match_data: Dict) -> str:
        """Get team's formation"""
        # Implementation of formation extraction
        return "4-3-3"
        
    def _analyze_formation_effectiveness(self, match_data: Dict) -> str:
        """Analyze how effectively the formation was used"""
        # Implementation of formation effectiveness analysis
        return "create overloads in wide areas while maintaining defensive stability"
        
    def _analyze_key_tactical_moment(self, match_data: Dict) -> str:
        """Analyze a key tactical moment"""
        # Implementation of tactical moment analysis
        return "how they adjusted their pressing triggers after the first goal"
        
    def _analyze_possession_tactically(self, match_data: Dict) -> str:
        """Analyze possession from a tactical perspective"""
        stats = match_data.get("statistics", {})
        formations = match_data.get("formations", {})
        
        # Get possession stats
        home_possession = stats.get("home", {}).get("possession", 50)
        away_possession = stats.get("away", {}).get("possession", 50)
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Analyze possession style
        if home_possession > 60:
            return f"{home_team} dominated possession, using the ball effectively to control the tempo and create opportunities through patient build-up play."
        elif away_possession > 60:
            return f"{away_team} controlled the game through possession, dictating the pace and forcing their opponents to chase the ball."
        else:
            return "Both teams showed good spells of possession, making it a tactically balanced contest with neither side able to dominate the ball for extended periods."

    def _analyze_shooting_tactically(self, match_data: Dict) -> str:
        """Analyze shooting from a tactical perspective"""
        stats = match_data.get("statistics", {})
        events = match_data.get("events", [])
        
        # Get team names
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        
        # Get goal events
        goal_events = [e for e in events if e.get("type") == "Goal"]
        
        if goal_events:
            return "The quality of chances created was evident in the finishing. The teams showed good tactical awareness in their shot selection, choosing the right moments to pull the trigger."
        else:
            return "Despite the lack of goals, both teams showed tactical maturity in their approach to creating chances. It was more about quality over quantity in the final third."

    def _analyze_stats_impact_on_tactics(self, match_data: Dict, last_message: str) -> str:
        """Analyze how statistics mentioned affect tactical aspects"""
        stats = match_data.get("statistics", {})
        formations = match_data.get("formations", {})
        
        response = "Looking at these numbers from a tactical perspective, "
        
        if "possession" in last_message:
            response += self._analyze_possession_tactics(stats, formations)
        elif "shots" in last_message:
            response += self._analyze_shooting_tactics(stats, formations)
        elif "accuracy" in last_message:
            response += self._analyze_passing_tactics(stats, formations)
        
        return response

    def _analyze_player_tactical_role(self, match_data: Dict, last_content: str) -> str:
        """Analyze a player's tactical role and contribution"""
        # Extract player name from message
        player_name = None
        for name in self._get_player_names(match_data):
            if name.lower() in last_content.lower():
                player_name = name
                break
        
        if not player_name:
            return "Let me focus on the overall tactical setup of the team..."
        
        # Get player data from match
        player_data = None
        lineups = match_data.get("lineups", [])
        for team_lineup in lineups:
            # Check starting XI
            for player in team_lineup.get("startXI", []):
                if player.get("player", {}).get("name") == player_name:
                    player_data = player
                    break
            # Check substitutes
            if not player_data:
                for player in team_lineup.get("substitutes", []):
                    if player.get("player", {}).get("name") == player_name:
                        player_data = player
                        break
        
        if not player_data:
            return f"While {player_name} was involved in the match, let me focus on their tactical contribution to the team's overall strategy..."
        
        # Build tactical analysis
        position = player_data.get("player", {}).get("position", "")
        response = f"Looking at {player_name}'s role from a tactical perspective, "
        
        if position:
            response += f"their positioning as a {position} was key to how the team set up. "
        
        # Add tactical context based on position
        if "forward" in position.lower() or "striker" in position.lower():
            response += "They were crucial in our pressing from the front and creating spaces for midfield runners."
        elif "midfield" in position.lower():
            response += "Their movement between the lines helped us control the tempo and transition between defense and attack."
        elif "defender" in position.lower() or "back" in position.lower():
            response += "They were instrumental in building from the back and maintaining our defensive shape."
        
        return response

    def _give_match_verdict(self, match_data: Dict) -> str:
        """Provide tactical verdict on whether the right team won"""
        stats = match_data.get("statistics", {})
        events = match_data.get("events", [])
        formations = match_data.get("formations", {})
        
        # Analyze tactical superiority
        home_tactical_score = self._calculate_tactical_effectiveness("home", stats, events, formations)
        away_tactical_score = self._calculate_tactical_effectiveness("away", stats, events, formations)
        
        verdict = self._form_tactical_verdict(home_tactical_score, away_tactical_score, match_data)
        return f"From a tactical perspective, {verdict}"

    def _build_on_previous_point(self, last_message: str, match_data: Dict) -> str:
        """Build on the previous point with tactical insight"""
        # Extract key topics from last message
        topics = self._extract_topics(last_message)
        
        response = "That's an interesting point. "
        
        if "defense" in topics:
            response += self._analyze_defensive_tactics(match_data)
        elif "attack" in topics:
            response += self._analyze_attacking_tactics(match_data)
        elif "midfield" in topics:
            response += self._analyze_midfield_tactics(match_data)
        else:
            response += self._analyze_general_tactics(match_data)
        
        return response

    def _calculate_tactical_effectiveness(self, team: str, stats: Dict, events: List, formations: Dict) -> float:
        """Calculate a team's tactical effectiveness score"""
        score = 0.0
        
        # Analyze formation adaptability
        formation_changes = self._count_formation_changes(team, events)
        score += formation_changes * 0.5  # Reward tactical flexibility
        
        # Analyze pressing effectiveness
        pressing_stats = self._calculate_pressing_stats(team, stats)
        score += pressing_stats * 0.3
        
        # Analyze positional play
        positional_score = self._analyze_positional_play(team, stats, formations)
        score += positional_score * 0.2
        
        return score

    def _form_tactical_verdict(self, home_score: float, away_score: float, match_data: Dict) -> str:
        """Form a verdict about which team deserved to win based on tactics"""
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        score = match_info.get("score", {"home": 0, "away": 0})
        
        # Compare tactical scores
        if abs(home_score - away_score) < 0.1:
            return f"both teams were tactically well-matched. The {score['home']}-{score['away']} scoreline reflects the even nature of the tactical battle."
        
        # Determine which team was tactically superior
        superior_team = home_team if home_score > away_score else away_team
        inferior_team = away_team if home_score > away_score else home_team
        
        actual_winner = home_team if score["home"] > score["away"] else away_team
        
        if superior_team == actual_winner:
            return f"{superior_team} were tactically superior and deserved their victory. Their approach consistently created problems for {inferior_team}."
        else:
            return f"while {actual_winner} got the result, {superior_team} showed tactical superiority in many aspects. Sometimes football isn't just about tactics."

    def _analyze_tactical_overview(self) -> str:
        """Provide comprehensive tactical overview of the match"""
        if not self.match_data:
            return "No match data available for tactical analysis."
            
        match_info = self.match_data.get("match_info", {})
        team_stats = self.match_data.get("team_statistics", {})
        coach_data = self.match_data.get("coach_data", {})
        
        analysis = f"Let me analyze the tactical approach of {match_info.get('home_team', 'Home Team')} vs {match_info.get('away_team', 'Away Team')}:\n\n"
        
        # Analyze team formations and approach
        for team_type in ["home", "away"]:
            team_name = match_info.get(f"{team_type}_team", f"{team_type.title()} Team")
            team_stats_data = team_stats.get(team_type, {})
            formation = coach_data.get("formations", {}).get(team_type, "Unknown")
            
            analysis += f"{team_name}'s Tactical Approach:\n"
            analysis += f"- Formation: {formation}\n"
            analysis += f"- Form: {team_stats_data.get('form', 'N/A')}\n"
            analysis += f"- Goals Scored: {team_stats_data.get('goals', {}).get('for', {}).get('total', {}).get('total', 'N/A')}\n"
            analysis += f"- Clean Sheets: {team_stats_data.get('clean_sheet', {}).get('total', 'N/A')}\n\n"
        
        return analysis
    
    def _analyze_player_performance(self, message: str) -> str:
        """Analyze individual player performance from a tactical perspective"""
        if not self.match_data:
            return "No match data available for player analysis."
            
        # Extract player name from message
        player_name = message.split("player")[-1].strip()
        
        # Get player statistics
        player_stats = self.match_data.get("statistics", {}).get("players", {}).get(player_name, {})
        if not player_stats:
            return f"No detailed performance data available for {player_name}."
        
        analysis = f"Tactical Analysis of {player_name}'s Performance:\n\n"
        
        # Analyze player's role and impact
        analysis += f"Role and Position:\n"
        analysis += f"- Position: {player_stats.get('position', 'N/A')}\n"
        analysis += f"- Minutes Played: {player_stats.get('minutes', 'N/A')}\n"
        analysis += f"- Distance Covered: {player_stats.get('distance', 'N/A')} km\n\n"
        
        # Analyze tactical contributions
        analysis += "Tactical Contributions:\n"
        analysis += f"- Passes: {player_stats.get('passes', {}).get('total', 'N/A')} (Accuracy: {player_stats.get('passes', {}).get('accuracy', 'N/A')}%)\n"
        analysis += f"- Key Passes: {player_stats.get('key_passes', 'N/A')}\n"
        analysis += f"- Duels Won: {player_stats.get('duels', {}).get('won', 'N/A')}/{player_stats.get('duels', {}).get('total', 'N/A')}\n"
        analysis += f"- Interceptions: {player_stats.get('interceptions', 'N/A')}\n"
        
        return analysis
    
    def _analyze_tactical_changes(self, match_data: Dict) -> str:
        """Analyze tactical changes during the match"""
        if not match_data:
            return "No match data available for tactical analysis."
            
        match_info = match_data.get("match_info", {})
        coach_data = match_data.get("coach_data", {})
        events = coach_data.get("events", [])
        
        analysis = "Tactical Changes Analysis:\n\n"
        
        # Analyze substitutions and their impact
        for team_type in ["home", "away"]:
            team_name = match_info.get(f"{team_type}_team", f"{team_type.title()} Team")
            team_events = [e for e in events if e.get("team", {}).get("name") == team_name]
            subs = [e for e in team_events if e.get("type") == "subst"]
            
            analysis += f"{team_name}'s Tactical Adaptations:\n"
            analysis += f"- Formation: {coach_data.get('formations', {}).get(team_type, 'Unknown')}\n"
            analysis += f"- Substitutions Made: {len(subs)}\n"
            
            # Add key substitution moments
            if subs:
                analysis += "Key Changes:\n"
                for sub in subs:
                    time = sub.get("time", {}).get("elapsed", "?")
                    player_out = sub.get("player", {}).get("name", "Unknown")
                    player_in = sub.get("assist", {}).get("name", "Unknown")
                    analysis += f"  • {time}': {player_out} ⟶ {player_in}\n"
            
            analysis += "\n"
        
        return analysis
    
    def _give_tactical_verdict(self) -> str:
        """Provide tactical verdict on the match"""
        if not self.match_data:
            return "No match data available for tactical analysis."
            
        match_info = self.match_data.get("match_info", {})
        team_stats = self.match_data.get("team_statistics", {})
        score = match_info.get("score", {})
        
        analysis = "Tactical Verdict:\n\n"
        
        # Compare team performances
        for team_type in ["home", "away"]:
            team_name = match_info.get(f"{team_type}_team", f"{team_type.title()} Team")
            team_stats_data = team_stats.get(team_type, {})
            goals_data = team_stats_data.get("goals", {})
            
            analysis += f"{team_name}'s Performance:\n"
            analysis += f"- Score: {score.get(team_type, 0)}\n"
            analysis += f"- Shots (avg per game): {goals_data.get('for', {}).get('average', {}).get('total', 'N/A')}\n"
            analysis += f"- Clean Sheets: {team_stats_data.get('clean_sheet', {}).get('total', 'N/A')}\n"
            analysis += f"- Form: {team_stats_data.get('form', 'N/A')}\n\n"
        
        return analysis
    
    def _give_general_tactical_analysis(self) -> str:
        """Provide general tactical analysis"""
        if not self.match_data:
            return "No match data available for tactical analysis."
            
        match_info = self.match_data.get("match_info", {})
        team_stats = self.match_data.get("team_statistics", {})
        coach_data = self.match_data.get("coach_data", {})
        
        analysis = "General Tactical Analysis:\n\n"
        
        # Analyze overall tactical patterns
        for team_type in ["home", "away"]:
            team_name = match_info.get(f"{team_type}_team", f"{team_type.title()} Team")
            team_stats_data = team_stats.get(team_type, {})
            formation = coach_data.get("formations", {}).get(team_type, "Unknown")
            fixtures = team_stats_data.get("fixtures", {})
            
            analysis += f"{team_name}'s Approach:\n"
            analysis += f"- Formation: {formation}\n"
            analysis += f"- Season Stats:\n"
            analysis += f"  • Wins: {fixtures.get('wins', {}).get('total', 'N/A')}\n"
            analysis += f"  • Draws: {fixtures.get('draws', {}).get('total', 'N/A')}\n"
            analysis += f"  • Losses: {fixtures.get('loses', {}).get('total', 'N/A')}\n\n"
        
        return analysis
    
    def _analyze_possession_style(self, stats: Dict) -> str:
        """Analyze team's possession style"""
        possession = stats.get("possession", 0)
        passes = stats.get("passes", {}).get("total", 0)
        pass_accuracy = stats.get("passes", {}).get("accuracy", 0)
        
        if possession > 60 and pass_accuracy > 85:
            return "Dominant possession-based play with high technical quality"
        elif possession > 50 and passes > 400:
            return "Controlled possession with emphasis on ball retention"
        else:
            return "Direct approach with focus on quick transitions"
    
    def _analyze_attacking_style(self, stats: Dict) -> str:
        """Analyze team's attacking style"""
        shots = stats.get("shots", {}).get("total", 0)
        xg = stats.get("xg", 0)
        crosses = stats.get("crosses", {}).get("total", 0)
        
        if shots > 15 and xg > 2:
            return "Aggressive attacking approach with high chance creation"
        elif crosses > 20:
            return "Wing-focused attacking strategy"
        else:
            return "Balanced attacking approach"
    
    def _analyze_defensive_style(self, stats: Dict) -> str:
        """Analyze team's defensive style"""
        tackles = stats.get("tackles", {}).get("total", 0)
        interceptions = stats.get("interceptions", 0)
        fouls = stats.get("fouls", 0)
        
        if tackles > 15 and interceptions > 10:
            return "Aggressive pressing and high defensive line"
        elif fouls < 5:
            return "Disciplined defensive approach with good positioning"
        else:
            return "Balanced defensive strategy"
    
    def _analyze_formation_changes(self, stats: Dict) -> str:
        """Analyze formation changes during the match"""
        # This would typically come from match events data
        return "No significant formation changes observed"
    
    def _analyze_substitutions(self, stats: Dict) -> str:
        """Analyze impact of substitutions"""
        # This would typically come from match events data
        return "Substitutions maintained tactical balance"
    
    def _analyze_tactical_shifts(self, stats: Dict) -> str:
        """Analyze tactical shifts during the match"""
        # This would typically come from match events data
        return "Team maintained consistent tactical approach"
    
    def _evaluate_tactical_approach(self, stats: Dict) -> str:
        """Evaluate overall tactical approach"""
        possession = stats.get("possession", 0)
        shots = stats.get("shots", {}).get("total", 0)
        xg = stats.get("xg", 0)
        
        if possession > 55 and shots > 12:
            return "Effective possession-based attacking approach"
        elif shots > 15 and xg > 2:
            return "Successful direct attacking strategy"
        else:
            return "Balanced tactical approach"
    
    def _identify_key_strengths(self, stats: Dict) -> str:
        """Identify team's key tactical strengths"""
        strengths = []
        
        if stats.get("possession", 0) > 55:
            strengths.append("Ball retention")
        if stats.get("shots", {}).get("total", 0) > 12:
            strengths.append("Chance creation")
        if stats.get("passes", {}).get("accuracy", 0) > 85:
            strengths.append("Passing accuracy")
            
        return ", ".join(strengths) if strengths else "No clear strengths identified"
    
    def _identify_improvement_areas(self, stats: Dict) -> str:
        """Identify areas for tactical improvement"""
        improvements = []
        
        if stats.get("possession", 0) < 45:
            improvements.append("Ball retention")
        if stats.get("shots", {}).get("total", 0) < 8:
            improvements.append("Chance creation")
        if stats.get("passes", {}).get("accuracy", 0) < 80:
            improvements.append("Passing accuracy")
            
        return ", ".join(improvements) if improvements else "No major areas for improvement identified"
    
    def _analyze_build_up(self, stats: Dict) -> str:
        """Analyze team's build-up play"""
        try:
            # Convert possession to int, removing % if present
            possession = int(str(stats.get("possession", "0")).replace("%", ""))
            
            # Get passes data safely
            passes_data = stats.get("passes", {})
            total_passes = int(passes_data.get("total", 0))
            
            # Convert pass accuracy to int, removing % if present
            pass_accuracy_str = str(passes_data.get("accuracy", "0")).replace("%", "")
            pass_accuracy = int(pass_accuracy_str) if pass_accuracy_str.isdigit() else 0
            
            if possession > 55 and pass_accuracy > 85:
                return "Patient build-up with emphasis on possession"
            elif total_passes > 400:
                return "Methodical build-up with good ball circulation"
            else:
                return "Direct build-up with quick transitions"
        except (ValueError, TypeError) as e:
            print(f"Error analyzing build-up play: {e}")
            return "Build-up play analysis unavailable"
    
    def _analyze_pressing(self, stats: Dict) -> str:
        """Analyze team's pressing strategy"""
        tackles = stats.get("tackles", {}).get("total", 0)
        interceptions = stats.get("interceptions", 0)
        fouls = stats.get("fouls", 0)
        
        if tackles > 15 and interceptions > 10:
            return "Aggressive pressing high up the pitch"
        elif fouls < 5:
            return "Disciplined pressing with good positioning"
        else:
            return "Balanced pressing approach"
    
    def _analyze_transitions(self, stats: Dict) -> str:
        """Analyze team's transition play"""
        counter_attacks = stats.get("counter_attacks", {}).get("total", 0)
        shots = stats.get("shots", {}).get("total", 0)
        
        if counter_attacks > 5:
            return "Effective counter-attacking transitions"
        elif shots > 12:
            return "Quick attacking transitions"
        else:
            return "Controlled transition play"

    def _extract_topics(self, message: str) -> List[str]:
        """Extract key topics from a message"""
        topics = []
        
        # Define topic keywords
        topic_keywords = {
            "defense": ["defend", "defensive", "back line", "clean sheet", "block", "tackle", "press"],
            "attack": ["attack", "forward", "goal", "shot", "score", "strike", "finish"],
            "midfield": ["midfield", "control", "possession", "pass", "create", "playmaker"],
            "tactics": ["formation", "tactic", "system", "setup", "approach", "strategy"],
            "transition": ["counter", "transition", "break", "turnover", "recover"],
            "pressing": ["press", "pressure", "intensity", "high line", "compact"],
            "buildup": ["build up", "buildup", "play out", "progression", "distribute"]
        }
        
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Check for each topic's keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ["general"]

    def _analyze_defensive_tactics(self, match_data: Dict) -> str:
        """Analyze team's defensive tactics"""
        stats = match_data.get("statistics", {})
        events = match_data.get("events", [])
        
        # Get defensive stats
        tackles = stats.get("tackles", {}).get("total", 0)
        interceptions = stats.get("interceptions", 0)
        clearances = stats.get("clearances", 0)
        blocks = stats.get("blocks", 0)
        
        analysis = ""
        if tackles > 20 and interceptions > 10:
            analysis = "the team employed an aggressive pressing system with high defensive engagement. "
        elif clearances > 15 and blocks > 10:
            analysis = "the team focused on a deep defensive block with emphasis on protecting their goal. "
        else:
            analysis = "the team maintained a balanced defensive approach, mixing pressing with positional defense. "
        
        # Add formation context
        formations = match_data.get("formations", {})
        if formations:
            analysis += f"Their defensive setup in a {formations.get('home', 'standard')} formation allowed them to "
            analysis += "control key areas and limit opposition chances."
        
        return analysis

    def _analyze_attacking_tactics(self, match_data: Dict) -> str:
        """Analyze team's attacking tactics"""
        stats = match_data.get("statistics", {})
        
        # Get attacking stats
        shots = stats.get("shots", {}).get("total", 0)
        shots_on = stats.get("shots", {}).get("on", 0)
        possession = stats.get("possession", "0").strip("%")
        passes = stats.get("passes", {}).get("total", 0)
        
        analysis = ""
        if int(possession) > 60 and passes > 500:
            analysis = "the team dominated through possession-based attacking play, patiently building up their chances. "
        elif shots > 15 and shots_on > 8:
            analysis = "the team showed direct attacking intent, creating numerous shooting opportunities. "
        else:
            analysis = "the team balanced their attacking approach, mixing possession with direct play. "
        
        # Add tactical context
        analysis += "Their attacking movements were well-coordinated, with players making intelligent runs and "
        analysis += "finding spaces between the lines."
        
        return analysis

    def _analyze_midfield_tactics(self, match_data: Dict) -> str:
        """Analyze team's midfield tactics"""
        stats = match_data.get("statistics", {})
        
        # Get midfield stats
        possession = int(stats.get("possession", "0").strip("%"))
        passes = stats.get("passes", {}).get("total", 0)
        pass_accuracy = float(stats.get("passes", {}).get("accuracy", "0").strip("%"))
        
        analysis = ""
        if possession > 55 and pass_accuracy > 85:
            analysis = "the midfield controlled the game through excellent ball retention and distribution. "
        elif passes > 400:
            analysis = "the midfield focused on quick ball circulation and creating passing lanes. "
        else:
            analysis = "the midfield maintained a balanced approach between possession and direct play. "
        
        # Add tactical context
        analysis += "Their positioning and movement created numerical advantages in key areas, "
        analysis += "allowing them to progress the ball effectively."
        
        return analysis

    def _analyze_general_tactics(self, match_data: Dict) -> str:
        """Analyze general tactical approach"""
        stats = match_data.get("statistics", {})
        formations = match_data.get("formations", {})
        
        # Get general stats
        possession = int(stats.get("possession", "0").strip("%"))
        shots = stats.get("shots", {}).get("total", 0)
        pass_accuracy = float(stats.get("passes", {}).get("accuracy", "0").strip("%"))
        
        analysis = ""
        if possession > 60 and pass_accuracy > 85:
            analysis = "the team's tactical approach was centered on controlling the game through possession. "
        elif shots > 15:
            analysis = "the team adopted a direct tactical approach, focusing on creating shooting opportunities. "
        else:
            analysis = "the team showed tactical flexibility, adapting their approach based on the game state. "
        
        # Add formation context
        if formations:
            analysis += f"Their {formations.get('home', 'standard')} formation provided a solid foundation for both "
            analysis += "attacking transitions and defensive stability."
        
        return analysis

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

    def _give_final_verdict(self, match_data: Dict) -> str:
        """Provide a comprehensive final verdict on the match"""
        match_info = match_data.get("match_info", {})
        team_stats = match_data.get("team_statistics", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        score = match_info.get("score", {"home": 0, "away": 0})
        
        # Calculate tactical effectiveness scores
        home_score = self._calculate_tactical_effectiveness("home", team_stats, 
                                                          match_data.get("events", []),
                                                          match_data.get("formations", {}))
        away_score = self._calculate_tactical_effectiveness("away", team_stats,
                                                          match_data.get("events", []),
                                                          match_data.get("formations", {}))
        
        # Build comprehensive verdict
        verdict = f"Let me give you my final tactical verdict on this {score['home']}-{score['away']} match. "
        
        # Add tactical analysis
        verdict += self._form_tactical_verdict(home_score, away_score, match_data)
        
        # Add key tactical moments
        verdict += "\n\nThe key tactical turning points were: "
        verdict += self._analyze_key_tactical_moment(match_data)
        
        # Add coaching wisdom for conclusion
        verdict += f"\n\n{random.choice(self.coaching_wisdom)}"
        
        return verdict

    def _get_player_names(self, match_data: Dict) -> List[str]:
        """Extract player names from match data"""
        player_names = []
        
        # Get lineups from match data
        lineups = match_data.get("lineups", [])
        for team_lineup in lineups:
            # Add starting XI
            for player in team_lineup.get("startXI", []):
                player_names.append(player.get("player", {}).get("name", ""))
            # Add substitutes
            for player in team_lineup.get("substitutes", []):
                player_names.append(player.get("player", {}).get("name", ""))
        
        return [name for name in player_names if name]  # Filter out empty names
