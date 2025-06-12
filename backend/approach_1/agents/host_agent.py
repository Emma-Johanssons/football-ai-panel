"""
Host agent for managing football panel discussions
"""
from typing import Dict, List, Set
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
from langchain_community.chat_models import ChatOpenAI
import random
import json
from datetime import datetime
import time

class HostAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        super().__init__(
            name="Show Host",
            role="Show Host",
            system_prompt="You are a professional football show host.",
            personality="engaging and knowledgeable",
            match_id=match_id
        )
        self.discussion_phases = [
            "match_overview",
            "key_moments",
            "tactical_analysis",
            "statistical_analysis",
            "player_performances",
            "conclusion"
        ]
        
        # Enhanced topic management
        self.topic_experts = {
            "tactics": "Tactical Analyst",
            "statistics": "Stats Expert",
            "key_moments": ["Tactical Analyst", "Stats Expert"],
            "player_performance": ["Tactical Analyst", "Stats Expert"]
        }
        
        # Track expert participation
        self.expert_tracking = {
            "Tactical Analyst": {"turns": 0, "last_spoke": 0, "topics": set()},
            "Stats Expert": {"turns": 0, "last_spoke": 0, "topics": set()}
        }
        
        # Enhanced prompts for drawing out different perspectives
        self.perspective_prompts = {
            "tactical": [
                "From a tactical standpoint, how did this influence the match?",
                "What tactical adjustments did you notice here?",
                "How did this affect the team's overall strategy?",
                "Was this a deliberate tactical choice?",
                "How did the opposition respond tactically?"
            ],
            "statistical": [
                "What do the numbers tell us about this?",
                "How does this compare to the season averages?",
                "Can you quantify the impact of this?",
                "Are there any interesting patterns in the data here?",
                "What statistical trends emerged from this?"
            ],
            "combined": [
                "How do the tactics and numbers align here?",
                "Does the data support what we saw tactically?",
                "Interesting point - can we look at this from both perspectives?",
                "Let's combine our tactical and statistical insights here.",
                "How do both of your expert views complement each other on this?"
            ]
        }
        
        self.conclusion_prompts = [
            "We've covered the tactics, the statistics, and the key moments. Looking at everything we've discussed - did the right team win today?",
            "Based on all we've analyzed - the numbers, the tactical battle, the key moments - was this a deserved result?",
            "After this fascinating discussion, let's address the big question: Did the better team win today?",
            "Taking everything into account - the stats, the tactics, the overall performance - was justice done with this result?",
            "Now for the verdict - having broken down every aspect of this match, was this the right result?"
        ]

        # Initialize services
        self.match_service = MatchService()
        
        # Initialize discussion tracking
        self.discussion_tracking = {
            "expert_contributions": {
                "Tactical Analyst": 0,
                "Stats Expert": 0
            },
            "topics_covered": set(),
            "last_speaker": None,
            "consecutive_same_speaker": 0
        }

    async def _load_match_data(self):
        """Load match data for the host"""
        try:
            if not self.match_id:
                return False
                
            # Load match data using match service
            match_data = await self.match_service.get_match_data(self.match_id)
            if match_data:
                self.match_data = match_data
                return True
            return False
            
        except Exception as e:
            print(f"Error loading match data: {e}")
            return False

    def should_speak(self, current_state: Dict) -> bool:
        """Determine if host should speak"""
        if not current_state:
            return False
            
        # Get recent discussion flow
        flow = current_state.get("flow", [])
        if not flow:
            return True  # Always speak first to introduce
            
        last_exchange = flow[-1]
        last_speaker = last_exchange.get("speaker")
        
        # Check if we need to intervene
        if self._needs_intervention(current_state):
            return True
            
        # Check if we need to transition topics
        if self._needs_topic_transition(current_state):
            return True
            
        # Check if we need to ensure balanced participation
        if self._needs_balance_correction(current_state):
            return True
            
        # Don't speak twice in a row unless necessary
        if last_speaker == self.role:
            return False
            
        # Random chance to speak to keep discussion flowing
        return random.random() < 0.2  # 20% chance to speak otherwise

    def _check_discussion_balance(self, state: Dict) -> bool:
        """Check if all experts have contributed roughly equally"""
        try:
            # Get contribution counts for each expert
            contributions = {}
            for entry in state.get("flow", []):
                speaker = entry.get("speaker")
                if speaker in ["Tactical Analyst", "Stats Expert"]:
                    contributions[speaker] = contributions.get(speaker, 0) + 1
                    
            if not contributions:
                return True  # No expert contributions yet
                
            # Check max difference in contributions
            max_contributions = max(contributions.values())
            min_contributions = min(contributions.values())
            
            # Allow difference of at most 2 contributions
            return (max_contributions - min_contributions) <= 2
            
        except Exception as e:
            print(f"Error checking discussion balance: {e}")
            return False

    async def _analyze_match_outcome(self, match_data: Dict, current_state: Dict) -> Dict:
        """Analyze match outcome from host perspective"""
        try:
            # Gather expert opinions
            expert_opinions = await self._gather_expert_opinions(current_state)
        
            # Check if discussion is complete
            discussion_complete = self._is_discussion_complete(current_state)
        
            # Check discussion balance
            balanced = self._check_discussion_balance(current_state)
        
            return {
                "discussion_complete": discussion_complete,
                "expert_opinions": expert_opinions,
                            "balanced": balanced
                        }
                
        except Exception as e:
            print(f"Error analyzing match outcome: {e}")
            return {
                "discussion_complete": True,
                "expert_opinions": [],
                "balanced": False
        }

    def _format_conclusion(self, conclusion: Dict, home_team: str, away_team: str, score: Dict) -> str:
        """Format conclusion from host perspective"""
        try:
            if not isinstance(conclusion, dict):
                
                return "Thank you all for these fascinating insights. We've had an excellent discussion analyzing this match from multiple perspectives."
        
            # Start with basic thank you
            response = "Thank you all for these fascinating insights. "
            
            # Safely get score values
            home_score = score.get('home', 0) if isinstance(score, dict) else 0
            away_score = score.get('away', 0) if isinstance(score, dict) else 0
            
            # Safely handle team names
            home_team = home_team if home_team else "the home team"
            away_team = away_team if away_team else "the away team"
            
            # Add key points if available
            key_points = conclusion.get("key_points_made", [])
            if key_points and isinstance(key_points, list):
                response += "\n\nThe key points we've discussed today were:"
                for point in key_points[:3]:
                    if point and isinstance(point, str):
                        response += f"\n- {point}"
        
                    # Add final wrap-up
                    response += f"\n\nIt's been a pleasure analyzing this {home_score}-{away_score} match between {home_team} and {away_team}. "
                    response += "Thank you for joining us for this discussion!"
        
                    return response
            
        except Exception as e:
            print(f"Error formatting conclusion: {e}")
            return "Thank you all for your valuable contributions to today's match analysis. This has been an insightful discussion."

    def _is_discussion_complete(self, state: Dict) -> bool:
        """Check if all important aspects have been discussed"""
        topics_covered = state.get("topics_covered", set())
        required_topics = {
            "tactics",
            "statistics",
            "key_moments",
            "player_performance"
        }
        
        return required_topics.issubset(topics_covered)

    async def _gather_expert_opinions(self, state: Dict) -> List[Dict]:
        """Gather opinions from different experts"""
        opinions = []
        flow = state.get("flow", [])
        
        for exchange in flow:
            if exchange["speaker"] in ["Tactical Analyst", "Stats Expert"]:
                opinions.append({
                    "expert": exchange["speaker"],
                    "opinion": exchange["content"],
                    "topic": self._detect_topic(exchange["content"])
                })
        
        return opinions

    async def _extract_key_points(self, state: Dict) -> List[str]:
        """Extract key points from the discussion"""
        key_points = []
        flow = state.get("flow", [])
        
        for exchange in flow:
            if not exchange or not exchange.get("content"):
                continue
            content = exchange["content"].lower()
            # Look for strong statements or conclusions
            if any(indicator in content for indicator in [
                "clearly showed", "proved decisive", "key factor",
                "significant impact", "crucial moment", "standout performer"
            ]):
                key_points.append(exchange["content"])
        
        return key_points

    def _get_transition_to_conclusion(self) -> str:
        """Get a smooth transition to conclusion phase"""
        transitions = [
            "We've covered a lot of ground in our analysis. Let's move towards our conclusion.",
            "As we approach the end of our discussion, let's address the big question.",
            "Now seems like the right time to get your final verdicts.",
            "Before we wrap up, let's address what everyone wants to know.",
            "We've analyzed this from every angle. Time for our final thoughts."
        ]
        return random.choice(transitions)

    def get_intervention_response(self, state: Dict) -> str:
        """Generate an intervention response based on the current state"""
        # Update expert tracking
        self._update_expert_tracking(state)
        
        # Check for participation imbalance
        if self._needs_balance_correction(state):
            return self._generate_balance_correction(state)
            
        # Check for topic coverage
        if self._needs_topic_transition(state):
            return self._generate_topic_transition(state)
            
        # Check for perspective diversity
        if self._needs_new_perspective(state):
            return self._generate_perspective_prompt(state)
            
        # Default to natural flow management
        return self._generate_flow_management(state)

    def _update_expert_tracking(self, state: Dict):
        """Update tracking of expert participation"""
        current_turn = state.get("turn_count", 0)
        last_speaker = state.get("last_speaker")
        current_topic = state.get("current_topic")
        
        if last_speaker in self.expert_tracking:
            self.expert_tracking[last_speaker]["turns"] += 1
            self.expert_tracking[last_speaker]["last_spoke"] = current_turn
            if current_topic:
                self.expert_tracking[last_speaker]["topics"].add(current_topic)

    def _needs_balance_correction(self, state: Dict) -> bool:
        """Check if participation needs rebalancing"""
        # Get participation counts
        counts = {expert: data["turns"] for expert, data in self.expert_tracking.items()}
        if not counts:
            return False
            
        # Calculate imbalance
        avg_turns = sum(counts.values()) / len(counts)
        max_imbalance = max(abs(count - avg_turns) for count in counts.values())
        
        return max_imbalance > 2  # Trigger if any expert has spoken 2 more times than average

    def _generate_balance_correction(self, state: Dict) -> str:
        """Generate response to correct participation imbalance"""
        # Find least active expert
        least_active = min(
            self.expert_tracking.items(),
            key=lambda x: (x[1]["turns"], -x[1]["last_spoke"])
        )[0]
        
        # Get unused topics for that expert
        expert_topics = self.expert_tracking[least_active]["topics"]
        all_relevant_topics = set(topic for topic, expert in self.topic_experts.items()
                                if least_active in (expert if isinstance(expert, list) else [expert]))
        unused_topics = all_relevant_topics - expert_topics
        
        if unused_topics:
            topic = random.choice(list(unused_topics))
            return f"Let's get {least_active}'s perspective on the {topic.replace('_', ' ')}. What stood out to you?"
        else:
            return f"{least_active}, we haven't heard from you in a while. What are your thoughts on this?"

    def _needs_topic_transition(self, state: Dict) -> bool:
        """Check if we need to transition to a new topic"""
        current_topic = state.get("current_topic")
        flow = state.get("flow", [])
        
        if not flow:
            return False
            
        # Check if we've spent enough time on current topic
        topic_exchanges = 0
        for exchange in reversed(flow):
            if exchange.get("topic") == current_topic:
                topic_exchanges += 1
            else:
                break
                
        return topic_exchanges >= 3

    def _generate_topic_transition(self, state: Dict) -> str:
        """Generate a transition to a new topic"""
        if not state:
            return "Let's move on to another aspect of the match."
            
        # Get current topic and mentioned aspects
        current_topic = state.get("current_topic", "").lower()
        mentioned_aspects = state.get("topics_covered", set())
        
        # Generate appropriate transition based on current topic
        if "tactical" in current_topic:
            if "statistics" not in mentioned_aspects:
                return "Those are excellent tactical insights. Let's look at what the statistics tell us about these patterns."
            elif "key_moments" not in mentioned_aspects:
                return "Interesting tactical analysis. How did these patterns play out in the key moments?"
            else:
                return "Let's explore another aspect of the match."
        elif "statistics" in current_topic:
            if "tactics" not in mentioned_aspects:
                return "The numbers are telling. How did this translate to the tactical battle?"
            elif "key_moments" not in mentioned_aspects:
                return "These statistics are fascinating. Let's look at some key moments that illustrate them."
            else:
                return "What other aspects of the match caught your attention?"
        elif "key_moments" in current_topic:
            if "tactics" not in mentioned_aspects:
                return "Those were crucial moments. How did they reflect the tactical approach?"
            elif "statistics" not in mentioned_aspects:
                return "Let's look at what the numbers tell us about these key moments."
            else:
                return "What other perspectives should we consider?"
        else:
            return "Let's explore another dimension of this match."

    def _needs_new_perspective(self, state: Dict) -> bool:
        """Check if we need a fresh perspective on the current topic"""
        recent_exchanges = state.get("flow", [])[-3:]  # Last 3 exchanges
        if not recent_exchanges:
            return False
            
        # Check if discussion is getting stale
        same_perspective = all(
            ex.get("speaker") == recent_exchanges[0].get("speaker")
            for ex in recent_exchanges
        )
        
        return same_perspective or len(recent_exchanges) >= 3

    def _generate_perspective_prompt(self, state: Dict) -> str:
        """Generate a prompt to get a fresh perspective"""
        current_topic = state.get("current_topic", "").lower()
        
        if "tactical" in current_topic:
            return random.choice(self.perspective_prompts["tactical"])
        elif "statistical" in current_topic:
            return random.choice(self.perspective_prompts["statistical"])
        else:
            return random.choice(self.perspective_prompts["combined"])

    def _generate_flow_management(self, state: Dict) -> str:
        """Generate a response to manage discussion flow"""
        # Get the last speaker and content
        last_speaker = state.get("last_speaker", "")
        current_topic = state.get("current_topic", "")
        
        # If last speaker was an expert, ask for elaboration
        if last_speaker in ["Tactical Analyst", "Stats Expert"]:
            return random.choice([
                "That's an interesting point. Could you elaborate on that?",
                "Tell us more about that aspect.",
                "How does that compare to what we typically see?",
                "What makes this particularly significant?"
            ])
            
        # If last speaker was a fan, bring in expert perspective
        if "Fan" in last_speaker:
            expert = "Tactical Analyst" if random.random() < 0.5 else "Stats Expert"
            return f"{expert}, what's your take on that point?"
            
        # Default to open-ended question about current topic
        current_topic_display = current_topic.replace('_', ' ') if current_topic else "aspects"
        return random.choice([
            f"Let's explore that further. What other aspects of {current_topic_display} stood out?",
            "How do others see this? Any different perspectives?",
            "That's fascinating. What else caught your attention?",
            "Let's dig deeper into that. What were the key factors?"
        ])

    def _is_interesting_point(self, content: str) -> bool:
        """Detect if a point merits follow-up"""
        if not content:
            return False
            
        interesting_topics = [
            "turning point", "key moment", "unusual", "surprising",
            "interesting", "fascinating", "remarkable", "crucial"
        ]
        return any(topic in content.lower() for topic in interesting_topics)

    def _extract_key_point(self, content: str) -> str:
        """Extract the main point from a statement"""
        # Simple extraction - could be enhanced with NLP
        sentences = content.split('.')
        return sentences[0].strip()

    def _find_related_point(self, point: str, match_data: Dict) -> str:
        """Find a related point from match data"""
        # Implementation would use match_data to find relevant related points
        # For now, return a generic related point
        return "the overall tactical approach"

    def _ensure_balanced_participation(self, state: Dict, match_data: Dict) -> str:
        """Ensure balanced participation from all experts"""
        speaking_counts = state.get("speaking_counts", {})
        least_spoken = min(speaking_counts, key=speaking_counts.get)
        
        if least_spoken == "Stats Expert":
            return "Let's look at this from a statistical perspective. What do the numbers tell us?"
        elif least_spoken == "Tactical Analyst":
            return "From a tactical standpoint, how do you see this?"
        else:
            return random.choice(self.opening_questions)

    async def _generate_response(self, current_state: Dict, recent_context: List[Dict], match_data: Dict, knowledge: Dict) -> str:
        """Generate a response based on the current state and match data"""
        try:
            # Get team names and basic info
            match_info = match_data.get('match_info', {})
            teams = match_info.get('teams', {})
            home_team = teams.get('home', {}).get('name', 'Home Team')
            away_team = teams.get('away', {}).get('name', 'Away Team')
            score = match_info.get('score', {}).get('fulltime', {'home': 0, 'away': 0})
            
            # Check if this is the opening statement
            if not recent_context:
                return self._generate_opening(home_team, away_team, score)
            
            # Check if it's time for conclusion
            if self._is_conclusion_question(recent_context[-1]["content"]):
                return self._generate_conclusion(home_team, away_team, score, current_state)
            
            # Get the last few speakers and their topics
            recent_speakers = [msg.get("speaker") for msg in recent_context[-3:]]
            recent_content = [msg.get("content", "") for msg in recent_context[-3:]]
            
            # Determine the current phase of discussion
            discussion_phase = self._determine_discussion_phase(current_state)
            
            # Generate appropriate response based on phase
            if discussion_phase == "initial_analysis":
                return self._moderate_initial_analysis(home_team, away_team, recent_speakers, recent_content)
            elif discussion_phase == "tactical_deep_dive":
                return self._moderate_tactical_discussion(home_team, away_team, recent_speakers, recent_content)
            elif discussion_phase == "statistical_analysis":
                return self._moderate_stats_discussion(home_team, away_team, recent_speakers, recent_content)
            elif discussion_phase == "key_moments":
                return self._moderate_key_moments(home_team, away_team, score, recent_speakers, recent_content)
            else:
                return self._generate_transition(home_team, away_team, recent_speakers, recent_content)
            
        except Exception as e:
            print(f"Error in host response generation: {e}")
            return self._get_fallback_response()
            
    def _generate_opening(self, home_team: str, away_team: str, score: Dict) -> str:
        """Generate opening statement"""
        return f"Welcome to our post-match analysis of an intriguing encounter between {home_team} and {away_team}. A {score['home']}-{score['away']} result that deserves thorough analysis. Let's start with the overall flow of the match. What were your initial observations?"
        
    def _generate_conclusion(self, home_team: str, away_team: str, score: Dict, current_state: Dict) -> str:
        """Generate conclusion statement"""
        topics_covered = current_state.get("topics_covered", set())
        
        response = f"Thank you all for these fascinating insights. We've covered this match from every angle - "
        
        if "tactics" in topics_covered:
            response += "the tactical battle, "
        if "statistics" in topics_covered:
            response += "the statistical story, "
        if "key_moments" in topics_covered:
            response += "and the key moments that shaped the game. "
            
        response += f"It's been a pleasure analyzing this {score['home']}-{score['away']} match between {home_team} and {away_team}. Thank you for joining us for this discussion!"
        
        return response
        
    def _determine_discussion_phase(self, current_state: Dict) -> str:
        """Determine the current phase of discussion"""
        topics_covered = current_state.get("topics_covered", set())
        flow = current_state.get("flow", [])
        
        if len(flow) < 5:
            return "initial_analysis"
        elif "tactics" not in topics_covered:
            return "tactical_deep_dive"
        elif "statistics" not in topics_covered:
            return "statistical_analysis"
        elif "key_moments" not in topics_covered:
            return "key_moments"
        else:
            return "transition"
            
    def _moderate_initial_analysis(self, home_team: str, away_team: str, recent_speakers: List[str], recent_content: List[str]) -> str:
        """Moderate the initial analysis phase"""
        if "Tactical Analyst" not in recent_speakers:
            return f"Let's hear from our tactical analyst. How did {home_team} and {away_team} set up tactically?"
        elif "Stats Expert" not in recent_speakers:
            return "Interesting tactical observation. Stats expert, what do the numbers tell us about this match?"
        else:
            return "Those are fascinating insights. Let's delve deeper into some specific aspects of the game."
            
    def _moderate_tactical_discussion(self, home_team: str, away_team: str, recent_speakers: List[str], recent_content: List[str]) -> str:
        """Moderate the tactical analysis phase"""
        tactical_keywords = ["formation", "press", "buildup", "defensive line"]
        mentioned_aspects = [kw for kw in tactical_keywords if any(kw in content.lower() for content in recent_content)]
        
        if not mentioned_aspects:
            return f"Let's focus on the tactical setup. How did {home_team}'s formation match up against {away_team}?"
        elif "press" not in mentioned_aspects:
            return "What about the pressing game? How did both teams approach this aspect?"
        elif "buildup" not in mentioned_aspects:
            return "And how did they differ in their buildup play?"
        else:
            return "Those are excellent tactical insights. Let's look at what the statistics tell us about these patterns."
            
    def _moderate_stats_discussion(self, home_team: str, away_team: str, recent_speakers: List[str], recent_content: List[str]) -> str:
        """Moderate statistical discussion"""
        if not recent_content:
            return f"Let's look at the numbers. What do the statistics tell us about {home_team} and {away_team}?"
            
        mentioned_aspects = set()
        for content in recent_content:
            if "possession" in content.lower():
                mentioned_aspects.add("possession")
            if "shots" in content.lower():
                mentioned_aspects.add("shots")
            if "pass" in content.lower():
                mentioned_aspects.add("passing")
                
        if "possession" not in mentioned_aspects:
            return "How did the possession stats influence the game?"
        elif "shots" not in mentioned_aspects:
            return "What about the shooting statistics?"
        elif "passing" not in mentioned_aspects:
            return "And how do the passing numbers compare?"
        else:
            return "Those are excellent statistical insights. Let's look at how these patterns played out tactically."
            
    def _moderate_key_moments(self, home_team: str, away_team: str, score: Dict, recent_speakers: List[str], recent_content: List[str]) -> str:
        """Moderate key moments discussion"""
        if not recent_content:
            return "What were the key moments that shaped this match?"
            
        mentioned_aspects = set()
        for content in recent_content:
            if "goal" in content.lower():
                mentioned_aspects.add("goals")
            if "save" in content.lower():
                mentioned_aspects.add("saves")
            if "chance" in content.lower():
                mentioned_aspects.add("chances")
                
        if "goals" not in mentioned_aspects:
            return "Talk us through the goals and how they changed the game."
        elif "saves" not in mentioned_aspects:
            return "Were there any crucial saves that proved decisive?"
        elif "chances" not in mentioned_aspects:
            return "What about other big chances that could have changed the outcome?"
        else:
            return "Excellent analysis of the key moments. Let's hear some final thoughts."
            
    def _generate_transition(self, home_team: str, away_team: str, recent_speakers: List[str], recent_content: List[str]) -> str:
        """Generate transitional questions"""
        transitions = [
            f"That's an interesting point about {home_team}. How does this compare to their usual approach?",
            f"Looking at {away_team}'s performance, what stands out as particularly noteworthy?",
            "How do you think this match might influence future tactical approaches?",
            "What lessons can be drawn from this performance?",
            "Let's explore that aspect in more detail. What are your thoughts?"
        ]
        
        return transitions[len(recent_content) % len(transitions)]

    def _get_fallback_response(self) -> str:
        """Get a safe fallback response when normal generation fails"""
        fallbacks = [
            "That's an interesting point. Let's hear from our tactical analyst on this.",
            "Those are some compelling insights. What does our stats expert make of this?",
            "Let's explore that further. What are your thoughts on how this affected the match?",
            "That's a fascinating perspective. How does this compare to what we typically see?",
            "Let's dig deeper into that observation. What were the key factors at play?"
        ]
        return random.choice(fallbacks)
        
    def _needs_intervention(self, state: Dict) -> bool:
        """Check if host needs to intervene in discussion"""
        return (
            self._needs_balance_correction(state) or
            self._needs_topic_transition(state) or
            self._needs_new_perspective(state)
        )

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

    async def analyze_match(self, match_data: dict) -> str:
        """Analyze match from a host's perspective"""
        try:
            # Get combined personality traits
            personality = self.get_combined_personality()
            
            # Base analysis focusing on overall game and key moments
            analysis = self._analyze_match_overview(match_data)
            
            # Adjust response based on personality
            analysis = self.adjust_response_style(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error in host analysis: {e}")
            return self.get_fallback_response()
            
    def _analyze_match_overview(self, match_data: dict) -> str:
        """Create a neutral, engaging overview of the match"""
        try:
            teams = match_data.get("match_info", {}).get("teams", {})
            score = match_data.get("match_info", {}).get("score", {}).get("fulltime", {})
            
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            home_score = score.get("home", 0)
            away_score = score.get("away", 0)
            
            overview = (
                f"Looking at this match between {home_team} and {away_team}, "
                f"which ended {home_score}-{away_score}, we saw some fascinating football. "
                f"Let's break down the key aspects of this game and understand how this result came about."
            )
            
            return overview
            
        except Exception as e:
            print(f"Error in match overview: {e}")
            return "Let's analyze this match in detail."
