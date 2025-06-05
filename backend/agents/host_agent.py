"""
Host agent for moderating the panel discussion
"""
from typing import Dict, List, Set
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
import random

class HostAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Show Host"
        role = "Show Host"
        system_prompt = """You are a charismatic football show host who moderates discussions between experts.
        Your role is to:
        1. Guide the conversation naturally
        2. Pick up on interesting points to explore
        3. Encourage debate when experts disagree
        4. Keep the discussion balanced and engaging
        5. Draw out personality from the experts
        6. Move towards clear conclusions
        
        Make the discussion feel like a natural conversation between football experts."""
        personality = "charismatic and knowledgeable moderator"
        
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        # Initialize host prompts
        self.transition_phrases = [
            "That's a fascinating point about {topic}. {expert}, what's your take on this?",
            "Interesting perspective. {expert}, how does that align with what you've seen?",
            "Let's get another angle on this. {expert}, based on your experience...",
            "That brings up an interesting question. {expert}, what do you make of that?",
            "I have to jump in here because that's fascinating. {expert}, does this match what you've observed?"
        ]
        
        self.topic_transitions = [
            "Let's talk about another aspect of the match...",
            "Moving on to something that caught my eye...",
            "That leads us nicely to another key point...",
            "Speaking of which, there's another interesting aspect...",
            "While we're on that subject..."
        ]
        
        self.debate_encouragement = [
            "I notice you have a different view on this...",
            "That's quite different from what we heard earlier...",
            "This seems to contradict our earlier discussion...",
            "Interesting how you see it differently...",
            "That's a contrasting perspective..."
        ]
        
        self.conclusion_prompts = [
            "As we wrap up, let's get your final thoughts...",
            "Looking at the whole picture, what's your verdict?",
            "Taking everything into account, did the better team win?",
            "What's the key takeaway from this match?",
            "Final thoughts on today's performance?"
        ]
        
    def generate_response(self, current_state: Dict, recent_context: List[Dict], 
                         match_data: Dict, knowledge: Dict) -> str:
        """Generate an engaging host response"""
        # Get discussion state
        topic = current_state.get("topic", "")
        topics_covered = current_state.get("topics_covered", set())
        last_speaker = current_state.get("last_speaker", "")
        
        # If starting discussion
        if not recent_context:
            return self._generate_introduction(match_data)
            
        # Get recent context
        last_exchange = recent_context[-1]
        last_content = last_exchange["content"].lower()
        
        # If experts disagree, encourage debate
        if self._detect_disagreement(recent_context):
            return self._encourage_debate(recent_context)
            
        # If topic needs transition
        if self._should_transition_topic(current_state):
            return self._transition_to_new_topic(current_state)
            
        # If moving towards conclusion
        if self._should_conclude(current_state):
            return self._initiate_conclusion()
            
        # Default to following up on last point
        return self._follow_up_on_point(last_exchange, match_data)
        
    def _generate_introduction(self, match_data: Dict) -> str:
        """Generate engaging introduction"""
        match_info = match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        score = match_info.get("score", {"home": 0, "away": 0})
        
        intro = f"Welcome to our post-match analysis of {home_team} versus {away_team}. "
        intro += "I'm joined by our tactical analyst, a former professional player who understands the game from both sides of the touchline, "
        intro += "and our stats expert who brings us the numbers that matter. "
        intro += f"\n\nWhat a match we've just witnessed, ending {score['home']}-{score['away']}. "
        intro += "Let's break down what we've seen today."
        
        return intro
        
    def _detect_disagreement(self, recent_context: List[Dict]) -> bool:
        """Detect if experts are disagreeing"""
        if len(recent_context) < 2:
            return False
            
        last_two = recent_context[-2:]
        last_content = last_two[1]["content"].lower()
        prev_content = last_two[0]["content"].lower()
        
        disagreement_indicators = [
            ("but", "however", "although", "though"),
            ("disagree", "different", "contrary"),
            ("actually", "fact", "reality"),
            ("not quite", "not exactly", "not necessarily")
        ]
        
        for indicators in disagreement_indicators:
            if any(word in last_content for word in indicators) and \
               any(word in prev_content for word in indicators):
                return True
                
        return False
        
    def _encourage_debate(self, recent_context: List[Dict]) -> str:
        """Encourage debate between experts"""
        prompt = random.choice(self.debate_encouragement)
        last_point = self._extract_key_point(recent_context[-1]["content"])
        
        response = f"{prompt} "
        response += f"Let's explore this further. "
        response += f"How do these different perspectives affect our understanding of {last_point}?"
        
        return response
        
    def _should_transition_topic(self, current_state: Dict) -> bool:
        """Determine if we should transition to a new topic"""
        topic = current_state.get("topic", "")
        topics_covered = current_state.get("topics_covered", set())
        required_topics = {"match_overview", "tactical_analysis", "statistical_analysis"}
        
        return topic in topics_covered and len(topics_covered) < len(required_topics)
        
    def _transition_to_new_topic(self, current_state: Dict) -> str:
        """Generate smooth topic transition"""
        transition = random.choice(self.topic_transitions)
        next_topic = self._determine_next_topic(current_state)
        
        response = f"{transition} "
        response += self._generate_topic_question(next_topic)
        
        return response
        
    def _should_conclude(self, current_state: Dict) -> bool:
        """Determine if discussion should move to conclusion"""
        topics_covered = current_state.get("topics_covered", set())
        required_topics = {"match_overview", "tactical_analysis", "statistical_analysis"}
        
        # Check if all required topics have been covered
        topics_complete = all(topic in topics_covered for topic in required_topics)
        
        # Check if we've had enough exchanges
        exchanges = len(current_state.get("flow", []))
        sufficient_discussion = exchanges >= 6  # Minimum exchanges before conclusion
        
        # Check if we're in a natural conclusion point
        last_exchange = current_state.get("flow", [])[-1] if current_state.get("flow") else {}
        last_content = last_exchange.get("content", "").lower()
        natural_conclusion_point = any(phrase in last_content for phrase in [
            "that's interesting",
            "fascinating point",
            "good observation",
            "excellent analysis"
        ])
        
        return topics_complete and sufficient_discussion and natural_conclusion_point
        
    def _initiate_conclusion(self) -> str:
        """Initiate conclusion of discussion"""
        # Choose a more specific conclusion prompt
        conclusion_prompts = [
            "We've covered a lot of ground here. Taking everything into account - the tactics, the statistics, the key moments - did the right team win today?",
            "This has been a fascinating analysis. Looking at both the tactical setup and the statistical evidence, what's your final verdict on this match?",
            "Before we wrap up, I'd like to get your final thoughts. Based on everything we've discussed, was this a fair reflection of both teams' performance?",
            "We've analyzed this from every angle. In conclusion, what do you think was the decisive factor in today's result?",
            "To bring our discussion to a close, I'm curious about your final verdict. Did the scoreline tell the full story of this match?"
        ]
        return random.choice(conclusion_prompts)
        
    def _follow_up_on_point(self, last_exchange: Dict, match_data: Dict) -> str:
        """Follow up on an interesting point"""
        speaker = last_exchange.get("speaker", "")
        content = last_exchange.get("content", "")
        
        # Determine who to address next based on context
        if speaker == "Stats Expert":
            next_expert = "Tactical Analyst"
            return f"Those numbers are fascinating. {next_expert}, how does this align with what you've seen on the pitch?"
        elif speaker == "Tactical Analyst":
            next_expert = "Stats Expert"
            return f"Interesting tactical observation. {next_expert}, do the numbers support this analysis?"
        else:
            # If neither expert has spoken, start with stats
            next_expert = "Stats Expert"
            return f"Let's look at the numbers first. {next_expert}, what do the statistics tell us about this match?"
        
    def _extract_key_point(self, content: str) -> str:
        """Extract key point from content for follow-up"""
        # Look for key phrases or topics
        key_topics = {
            "possession": ["possession", "control", "ball"],
            "pressing": ["press", "pressure", "intensity"],
            "formation": ["formation", "setup", "system"],
            "statistics": ["stats", "numbers", "data"],
            "performance": ["performance", "played", "showing"],
            "tactics": ["tactical", "approach", "strategy"]
        }
        
        content_lower = content.lower()
        
        # Find the first matching topic
        for topic, keywords in key_topics.items():
            if any(keyword in content_lower for keyword in keywords):
                # Find the sentence containing this keyword
                sentences = content.split('.')
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in keywords):
                        return sentence.strip()
        
        # Default to first sentence if no key topic found
        first_sentence = content.split(".")[0]
        if len(first_sentence) > 50:
            return first_sentence[:50] + "..."
        return first_sentence
        
    def _determine_next_topic(self, current_state: Dict) -> str:
        """Determine next topic to discuss"""
        topics_covered = current_state.get("topics_covered", set())
        all_topics = ["match_overview", "tactical_analysis", "statistical_analysis", 
                     "key_moments", "player_performance"]
                     
        for topic in all_topics:
            if topic not in topics_covered:
                return topic
                
        return "conclusion"
        
    def _generate_topic_question(self, topic: str) -> str:
        """Generate question for new topic"""
        questions = {
            "match_overview": "Let's get a general overview of what we've seen today.",
            "tactical_analysis": "What were the key tactical elements that shaped this match?",
            "statistical_analysis": "What do the numbers tell us about this performance?",
            "key_moments": "Which moments really changed the course of this match?",
            "player_performance": "Who were the standout performers today?",
            "conclusion": "Taking everything into account, what's your verdict on this match?"
        }
        
        return questions.get(topic, "What are your thoughts on this?")

    def get_intervention_response(self, state: Dict) -> str:
        """Generate an intervention response based on the current state"""
        # Get discussion state
        topic = state.get("topic", "")
        topics_covered = state.get("topics_covered", set())
        last_speaker = state.get("last_speaker", "")
        flow = state.get("flow", [])
        
        # If no recent context, start discussion
        if not flow:
            return self._generate_introduction(self.match_data)
            
        # Get recent context
        last_exchange = flow[-1]
        last_content = last_exchange["content"].lower()
        
        # If experts disagree, encourage debate
        if self._detect_disagreement(flow[-2:] if len(flow) > 1 else []):
            return self._encourage_debate(flow[-2:])
            
        # If topic needs transition
        if self._should_transition_topic(state):
            return self._transition_to_new_topic(state)
            
        # If moving towards conclusion
        if self._should_conclude(state):
            return self._initiate_conclusion()
            
        # Default to following up on last point
        return self._follow_up_on_point(last_exchange, self.match_data)
