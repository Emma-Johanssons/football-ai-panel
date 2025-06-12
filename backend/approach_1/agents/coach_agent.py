from typing import Dict, List, Any
import os
import requests
from dotenv import load_dotenv
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
from langchain_community.chat_models import ChatOpenAI
import random
import json
import time

# Load environment variables
load_dotenv()

class CoachAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Tactical Analyst"
        role = "Tactical Analyst"
        system_prompt = """You are a tactical football analyst. Your job is to:
1. Explain how teams are set up tactically
2. Point out key tactical changes during the match
3. Respond to others' points from a tactical perspective
4. Keep responses short and focused on tactics

Always relate your tactical insights to what others are discussing."""
        
        personality = "tactically astute"
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        # Track which tactical aspects we've covered
        self.discussed_tactics = {
            "formation": False,
            "pressing": False,
            "buildup": False,
            "transitions": False
        }
        
        self.match_service = MatchService()
        
        # Initialize content tracking
        self.content_tracking = {
            "used_tactics": set(),  # Track discussed tactical aspects
            "mentioned_players": set(),  # Track discussed players
            "discussed_events": set(),  # Track discussed match events
            "used_analogies": set()  # Track used tactical analogies
        }
        
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
        
        # Initialize tactical focus areas
        self.tactical_areas = {
            "formation": ["setup", "shape", "structure"],
            "pressing": ["press", "pressure", "intensity"],
            "buildup": ["build-up", "progression", "transition"],
            "attacking": ["attack", "offensive", "forward"],
            "defending": ["defense", "defensive", "block"]
        }
    
    def should_speak(self, current_state: Dict) -> bool:
        """Determine if tactical analyst should speak"""
        if not current_state:
            return False
            
        last_exchange = current_state.get("flow", [])[-1] if current_state.get("flow") else {}
        last_content = last_exchange.get("content", "").lower()
        
        # Speak if someone mentions anything tactical
        tactical_triggers = ["formation", "tactic", "setup", "press", "defend", "attack", "position"]
        if any(trigger in last_content for trigger in tactical_triggers):
            return True
            
        # Don't speak twice in a row
        if last_exchange.get("speaker") == self.role:
            return False
            
        return random.random() < 0.3  # 30% chance otherwise
    
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

    async def _generate_response(self, current_state: Dict, recent_context: List[Dict], match_data: Dict, knowledge: Dict) -> str:
        """Generate a response based on the current state and match data"""
        try:
            # Check if it's time for conclusion
            if recent_context and self._is_conclusion_question(recent_context[-1]["content"]):
                conclusion = await self._analyze_match_outcome(match_data, current_state)
                formatted = self._format_conclusion(conclusion)
                if not formatted:
                    return "From a tactical perspective, both teams showed interesting approaches to the game."
                return formatted
            
            # Get team names and basic info
            match_info = match_data.get('match_info', {})
            teams = match_info.get('teams', {})
            home_team = teams.get('home', {}).get('name', 'Home Team')
            away_team = teams.get('away', {}).get('name', 'Away Team')
            
            # Get tactical information
            details = match_data.get('details', {})
            formations = details.get('formations', {})
            home_formation = formations.get('home', 'Unknown')
            away_formation = formations.get('away', 'Unknown')
            
            # Get tactical analysis
            tactical = match_data.get('tactical_analysis', {})
            home_tactics = tactical.get('home', {})
            away_tactics = tactical.get('away', {})
            
            # Analyze current topic
            current_topic = current_state.get('current_topic', '').lower()
            
            # Generate focused tactical analysis
            if "formation" in current_topic:
                response = self._analyze_formations(home_team, away_team, home_formation, away_formation, home_tactics, away_tactics)
            elif "press" in current_topic:
                response = self._analyze_pressing(home_team, away_team, home_tactics, away_tactics)
            elif "build" in current_topic or "attack" in current_topic:
                response = self._analyze_buildup(home_team, away_team, home_tactics, away_tactics)
            else:
                # General tactical overview
                response = self._format_tactical_analysis(home_team, away_team, home_tactics, away_tactics, home_formation, away_formation)
            
            # Add context from RAG if available
            if knowledge:
                response += f"\n\n{knowledge}"
            
            return response
            
        except Exception as e:
            print(f"Error in tactical analysis generation: {e}")
            return self._get_fallback_response(current_state)
            
    def _analyze_formations(self, home_team: str, away_team: str, home_formation: str, away_formation: str, home_tactics: Dict, away_tactics: Dict) -> str:
        """Analyze team formations and their implications"""
        response = f"Looking at the tactical setup, {home_team} opted for a {home_formation} formation while {away_team} went with {away_formation}. "
        
        # Analyze formation matchup
        if home_formation == "4-3-3" and away_formation == "3-5-2":
            response += f"This created an interesting dynamic where {home_team}'s wide attackers could exploit the spaces behind {away_team}'s wing-backs. "
        elif home_formation == "3-5-2" and away_formation == "4-3-3":
            response += f"This meant {home_team} had extra defensive coverage against {away_team}'s front three, but risked being exposed in wide areas. "
        
        # Add tactical context
        response += f"{home_team}'s {home_tactics.get('buildup_style', 'Unknown')} buildup style complemented their formation, "
        response += f"while {away_team} focused on a {away_tactics.get('attacking_style', 'Unknown')} approach. "
        
        return response
        
    def _analyze_pressing(self, home_team: str, away_team: str, home_tactics: Dict, away_tactics: Dict) -> str:
        """Analyze pressing tactics"""
        home_press = home_tactics.get('pressing_intensity', 'Unknown')
        away_press = away_tactics.get('pressing_intensity', 'Unknown')
        
        response = f"In terms of pressing, {home_team} implemented a {home_press} pressing intensity, while {away_team} opted for {away_press} pressing. "
        
        # Analyze pressing matchup
        if home_press == "high" and away_press == "medium":
            response += f"This allowed {home_team} to disrupt {away_team}'s buildup play effectively. "
        elif home_press == "medium" and away_press == "high":
            response += f"This meant {away_team} could put significant pressure on {home_team}'s defense. "
        
        # Add defensive context
        response += f"{home_team} maintained a {home_tactics.get('defensive_line', 'Unknown')} defensive line, "
        response += f"while {away_team} set up with a {away_tactics.get('defensive_line', 'Unknown')} block. "
        
        return response
        
    def _analyze_buildup(self, home_team: str, away_team: str, home_tactics: Dict, away_tactics: Dict) -> str:
        """Analyze buildup and attacking tactics"""
        home_style = home_tactics.get('buildup_style', 'Unknown')
        away_style = away_tactics.get('buildup_style', 'Unknown')
        home_attack = home_tactics.get('attacking_style', 'Unknown')
        away_attack = away_tactics.get('attacking_style', 'Unknown')
        
        response = f"Analyzing the attacking approaches, {home_team} focused on {home_style} buildup leading to {home_attack}, "
        response += f"while {away_team} preferred {away_style} buildup with {away_attack}. "
        
        # Add tactical interpretation
        if home_style == "possession" and away_style == "direct":
            response += f"This created a clear contrast in styles, with {home_team} looking to control the game through possession "
            response += f"while {away_team} aimed to be more direct and vertical in their approach. "
        elif home_style == "direct" and away_style == "possession":
            response += f"The tactical battle saw {away_team} trying to dominate possession, "
            response += f"while {home_team} looked to exploit spaces with direct play. "
        
        return response
        
    def _format_tactical_analysis(self, home_team: str, away_team: str, home_tactics: Dict, away_tactics: Dict, home_formation: str, away_formation: str) -> str:
        """Format comprehensive tactical analysis"""
        response = f"The tactical battle between {home_team} and {away_team} was fascinating. "
        
        # Formation analysis
        response += f"{home_team} lined up in a {home_formation} against {away_team}'s {away_formation}. "
        
        # Pressing and defensive setup
        response += f"They implemented a {home_tactics.get('pressing_intensity', 'Unknown')} pressing approach with a {home_tactics.get('defensive_line', 'Unknown')} defensive line, "
        response += f"while {away_team} countered with {away_tactics.get('pressing_intensity', 'Unknown')} pressing and a {away_tactics.get('defensive_line', 'Unknown')} block. "
        
        # Attacking approaches
        response += f"\n\nIn terms of attacking strategy, {home_team} focused on {home_tactics.get('buildup_style', 'Unknown')} buildup leading to {home_tactics.get('attacking_style', 'Unknown')}, "
        response += f"while {away_team} preferred {away_tactics.get('buildup_style', 'Unknown')} progression with {away_tactics.get('attacking_style', 'Unknown')}. "
        
        # Add tactical interpretation
        response += "\n\nThis tactical setup meant "
        if home_tactics.get('pressing_intensity') == "high" and home_tactics.get('buildup_style') == "possession":
            response += f"{home_team} could control the game through both possession and territorial dominance. "
        elif away_tactics.get('attacking_style') == "counter-attack" and home_tactics.get('defensive_line') == "high":
            response += f"{away_team} could exploit the spaces behind {home_team}'s high defensive line. "
        
        return response

    def _get_fallback_response(self, current_state: Dict = None) -> str:
        """Get a safe fallback response when normal generation fails"""
        try:
            if not current_state or not current_state.get("match_data"):
                return "From a tactical perspective, both teams showed interesting approaches."
            
            match_data = current_state.get("match_data", {})
            
            # Get team names and formations
            teams = match_data.get("match_info", {}).get("teams", {})
            formations = match_data.get("details", {}).get("formations", {})
            
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            home_formation = formations.get("home", "their formation")
            away_formation = formations.get("away", "their setup")
            
            # Generate response based on formations
            if home_formation != "their formation" or away_formation != "their setup":
                return f"Looking at the tactical setup, {home_team} went with {home_formation} while {away_team} opted for {away_formation}."
            
            # Get possession stats for tactical context
            stats = match_data.get("statistics", {})
            if stats:
                home_possession = stats.get("home", {}).get("Ball Possession", "")
                away_possession = stats.get("away", {}).get("Ball Possession", "")
                if home_possession and away_possession:
                    return f"The tactical battle is reflected in the possession stats: {home_team} with {home_possession} and {away_team} with {away_possession}."
            
            # Default response if no specific data available
            return f"The tactical approaches from both {home_team} and {away_team} created an interesting dynamic."
            
        except Exception as e:
            print(f"Error in tactical fallback: {e}")
            return "The tactical setup from both teams created some interesting matchups."

    async def _share_new_insight(self, match_data: Dict) -> str:
        """Share a new tactical insight about the match"""
        try:
            # Get formations
            home_formation = match_data.get("details", {}).get("formations", {}).get("home", "Unknown")
            away_formation = match_data.get("details", {}).get("formations", {}).get("away", "Unknown")
            
            # Get team names
            home_team = match_data.get("match_info", {}).get("teams", {}).get("home", {}).get("name", "Home Team")
            away_team = match_data.get("match_info", {}).get("teams", {}).get("away", {}).get("name", "Away Team")
            
            # Generate tactical insight
            insight = f"Looking at the formations, {home_team} set up in a {home_formation} while {away_team} opted for a {away_formation}. "
            
            # Add insight about possession if available
            home_possession = match_data.get("statistics", {}).get("home", {}).get("possession")
            if home_possession:
                insight += f"The possession stats ({home_possession}% vs {100-home_possession}%) suggest "
                if home_possession > 60:
                    insight += f"{home_team} dominated the ball, controlling the tempo of the game. "
                elif home_possession < 40:
                    insight += f"{away_team} controlled more of the ball, dictating the play. "
                else:
                    insight += "it was an evenly contested match in terms of ball control. "
            
            return insight
            
        except Exception as e:
            print(f"Error generating tactical insight: {e}")
            return "Let me analyze the tactical setup of both teams."

    def _is_conclusion_question(self, content: str) -> bool:
        """Check if content is asking for conclusion"""
        if not content:
            return False
            
        conclusion_indicators = [
            "final thoughts",
            "to conclude",
            "in conclusion",
            "summing up",
            "overall thoughts",
            "wrap up"
        ]
        return any(indicator in content.lower() for indicator in conclusion_indicators)

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

    async def _analyze_match_outcome(self, match_data: Dict, current_state: Dict) -> Dict:
        """Analyze match outcome from tactical perspective"""
        tactics = match_data.get("tactical_analysis", {})
        match_info = match_data.get("match_info", {})
        
        # Analyze tactical effectiveness
        home_tactics = await self._analyze_tactical_effectiveness("home", tactics)
        away_tactics = await self._analyze_tactical_effectiveness("away", tactics)
        
        # Get actual result
        score = match_info.get("score", {"home": 0, "away": 0})
        actual_winner = "home" if score["home"] > score["away"] else "away"
        
        # Analyze key tactical moments
        key_moments = await self._analyze_key_tactical_moments(tactics)
        formation_analysis = await self._analyze_formations(match_data)
        
        return {
            "tactical_winner": "home" if home_tactics > away_tactics else "away",
            "tactical_margin": abs(home_tactics - away_tactics),
            "actual_winner": actual_winner,
            "deserved_result": (home_tactics > away_tactics) == (actual_winner == "home"),
            "key_moments": key_moments,
            "formation_analysis": formation_analysis,
            "tactical_insights": await self._generate_tactical_insights(tactics)
        }

    def _format_conclusion(self, conclusion: Dict, home_team: str, away_team: str, score: Dict) -> str:
        """Format tactical conclusion"""
        winner = home_team if conclusion["actual_winner"] == "home" else away_team
        deserved = conclusion["deserved_result"]
        
        response = f"From a tactical perspective, "
        
        if deserved:
            response += f"{winner}'s victory was well deserved. "
            if conclusion["tactical_margin"] > 0.5:
                response += "They were clearly superior in their tactical execution. "
            else:
                response += "While it was close, they edged it through better tactical decisions. "
        else:
            response += f"while {winner} got the result, the tactical battle tells a different story. "
            response += "Sometimes football isn't just about tactical superiority. "
        
        # Add specific tactical insights
        response += f"\n\nThe key tactical aspects were: "
        for moment in conclusion["key_moments"][:2]:  # Top 2 key moments
            response += f"\n- {moment}"
        
        # Add coaching wisdom
        response += f"\n\n{random.choice(self.coaching_wisdom)}"
        
        return response

    def _get_key_tactical_stats(self, stats: Dict) -> Dict:
        """Extract key tactical statistics"""
        return {
            "possession": stats.get("possession", {}),
            "shots_on_target": stats.get("shots", {}).get("on", 0),
            "passes": stats.get("passes", {}).get("total", 0),
            "pressing_success": stats.get("pressing", {}).get("success_rate", 0)
        }

    def _analyze_key_tactical_moments(self, match_data: Dict) -> List[str]:
        """Analyze key tactical moments that influenced the match"""
        events = match_data.get("events", [])
        formations = match_data.get("formations", {})
        
        key_moments = []
        
        # Formation changes
        if formations.get("changes"):
            key_moments.append(f"The tactical switch in formation proved decisive")
            
        # Goals and their tactical context
        goals = [e for e in events if e.get("type") == "Goal"]
        if goals:
            key_moments.append(f"The opening goal came from well-executed tactical pressing")
            
        # Substitutions impact
        subs = [e for e in events if e.get("type") == "subst"]
        if subs:
            key_moments.append(f"The substitutions changed the tactical dynamic of the match")
            
        return key_moments

    def _identify_tactical_aspect(self, content: str) -> str:
        """Identify the tactical aspect being discussed in the content"""
        # List of tactical aspects and their related keywords
        aspect_keywords = {
            "formation": ["formation", "setup", "system", "shape"],
            "pressing": ["press", "pressure", "pressing", "intensity"],
            "possession": ["possession", "build-up", "ball control"],
            "defensive": ["defensive", "defense", "defending", "back line"],
            "attacking": ["attack", "offensive", "forward", "scoring"],
            "transition": ["transition", "counter", "break"],
            "positioning": ["position", "movement", "spacing"],
            "set-pieces": ["set piece", "corner", "free kick"],
            "substitutions": ["substitute", "change", "bench"],
            "tempo": ["tempo", "pace", "rhythm"]
        }
        
        # Find the most relevant aspect based on keyword matches
        aspect_matches = {}
        content_lower = content.lower()
        
        for aspect, keywords in aspect_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > 0:
                aspect_matches[aspect] = matches
                
        # Return the aspect with most keyword matches, or None if no matches
        if aspect_matches:
            return max(aspect_matches.items(), key=lambda x: x[1])[0]
        
        return "general"  # Default to general tactical aspect
        
    def _get_related_tactical_point(self, aspect: str, match_data: Dict) -> str:
        """Get a related tactical point based on the identified aspect"""
        # Get all tactical aspects
        all_aspects = self._get_all_tactical_aspects(match_data)
        used_aspects = self.content_tracking.get("used_tactics", set())
        
        # Define related aspects for each tactical aspect
        related_aspects = {
            "formation": ["team shape", "tactical flexibility", "player positioning"],
            "pressing": ["defensive organization", "pressing triggers", "pressing intensity"],
            "possession": ["build-up play", "ball progression", "possession style"],
            "defensive": ["defensive transitions", "marking system", "defensive organization"],
            "attacking": ["chance creation", "final third entries", "attacking patterns"],
            "transition": ["counter-attacking", "defensive transitions", "pressing triggers"],
            "positioning": ["team shape", "tactical discipline", "formation setup"],
            "set-pieces": ["set-piece organization", "attacking patterns", "defensive organization"],
            "substitutions": ["tactical flexibility", "game management", "formation changes"],
            "tempo": ["pressing intensity", "ball progression", "game management"],
            "general": ["tactical discipline", "game management", "team shape"]
        }
        
        # Get related aspects for the current aspect
        potential_aspects = related_aspects.get(aspect, related_aspects["general"])
        
        # Filter out used aspects
        available_aspects = [a for a in potential_aspects if a in all_aspects and a not in used_aspects]
        
        if not available_aspects:
            # If no unused related aspects, get any unused aspect
            available_aspects = [a for a in all_aspects if a not in used_aspects]
            if not available_aspects:
                return self._get_overall_tactical_summary(match_data)
        
        # Choose the most interesting aspect from available ones
        chosen_aspect = self._choose_most_interesting_aspect(available_aspects, match_data)
        if not chosen_aspect:
            return self._get_overall_tactical_summary(match_data)
            
        # Mark the chosen aspect as used
        self.content_tracking["used_tactics"].add(chosen_aspect)
        
        # Generate insight for the chosen aspect
        return self._generate_tactical_insight(chosen_aspect, match_data)

    def _analyze_tactical_content(self, content: str) -> Dict[str, Any]:
        """Analyze tactical content and provide insights"""
        if not content:
            return {}
            
        content_lower = content.lower()
        insights = {}
        
        # Formation analysis
        if "formation" in content_lower:
            insights["formation"] = self._analyze_formation()
            
        # Pressing analysis
        if "press" in content_lower:
            insights["pressing"] = self._analyze_pressing()
            
        # Attacking patterns
        if "attack" in content_lower:
            insights["attack"] = self._analyze_attack_patterns()
            
        # Defensive organization
        if "defen" in content_lower:
            insights["defense"] = self._analyze_defense()
            
        return insights

    def should_interrupt(self, speaker: str, content: str) -> bool:
        """Determine if tactical analyst should interrupt"""
        if not content:
            return False
            
        # Don't interrupt the host
        if speaker == "Show Host":
            return False
            
        # Check if there's a tactical point that needs elaboration
        content_lower = content.lower()
        tactical_keywords = ["formation", "tactic", "press", "defense", "attack", "position"]
        
        # Only interrupt if there's a tactical point and we haven't spoken recently
        if any(keyword in content_lower for keyword in tactical_keywords):
            return random.random() < 0.3  # 30% chance to interrupt tactical discussions
            
        return False
        
    def get_interruption(self, content: str) -> str:
        """Get an interruption response"""
        try:
            # Extract any tactical terms mentioned
            tactical_terms = [term for term in self.tactical_areas.keys() if term in content.lower()]
            
            if tactical_terms:
                return "If I could add to that tactical point..."
            else:
                return "From a tactical perspective, I'd like to add..."
                
        except Exception as e:
            print(f"Error generating interruption: {e}")
            return None
