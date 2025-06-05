from typing import List, Dict, Optional, Set
from services.match_service import MatchService
from agents.host_agent import HostAgent
from agents.stats_agent import StatsAgent
from agents.coach_agent import CoachAgent

class Panel:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.match_service = MatchService()
        self.match_data = self.match_service.get_match_data(match_id)
        
        if not self.match_data:
            raise ValueError(f"Could not get match data for ID: {match_id}")
            
        # Initialize panel members
        self.host = HostAgent(match_id=match_id)
        self.stats_expert = StatsAgent(match_id=match_id)
        self.tactical_analyst = CoachAgent(match_id=match_id)
        
        # Initialize discussion state
        self.discussion_state = {
            "current_topic": None,
            "last_speaker": None,
            "topics_covered": set(),
            "key_moments_discussed": set(),
            "conclusions_reached": {
                "tactical": None,
                "statistical": None,
                "overall": None
            },
            "interaction_count": {
                "Show Host": 0,
                "Stats Expert": 0,
                "Tactical Analyst": 0
            }
        }
        
        # Define discussion flow
        self.discussion_flow = {
            "introduction": {
                "next": ["match_overview", "key_moments", "tactical_analysis"],
                "required": True
            },
            "match_overview": {
                "next": ["tactical_analysis", "statistical_analysis", "key_moments"],
                "required": True
            },
            "tactical_analysis": {
                "next": ["statistical_analysis", "key_moments", "player_performance"],
                "required": True
            },
            "statistical_analysis": {
                "next": ["tactical_analysis", "key_moments", "player_performance"],
                "required": True
            },
            "key_moments": {
                "next": ["player_performance", "team_comparison", "conclusion"],
                "required": True
            },
            "player_performance": {
                "next": ["team_comparison", "conclusion"],
                "required": False
            },
            "team_comparison": {
                "next": ["conclusion"],
                "required": False
            },
            "conclusion": {
                "next": [],
                "required": True
            }
        }
        
        # Add personality traits and interaction styles
        self.interaction_styles = {
            "Show Host": {
                "style": "moderator",
                "traits": [
                    "guides discussion naturally",
                    "picks up on interesting points",
                    "encourages debate when opinions differ",
                    "keeps focus on key aspects",
                    "brings out personality of experts"
                ]
            },
            "Stats Expert": {
                "style": "analytical but engaging",
                "traits": [
                    "uses stats to tell stories",
                    "makes numbers relatable",
                    "adds historical context",
                    "shares interesting facts",
                    "responds to tactical points with data"
                ]
            },
            "Tactical Analyst": {
                "style": "experienced professional",
                "traits": [
                    "draws from playing experience",
                    "challenges statistical views",
                    "provides practical insights",
                    "uses analogies from famous matches",
                    "shares insider knowledge"
                ]
            }
        }
        
    def generate_discussion(self) -> str:
        """Generate a dynamic panel discussion about the match"""
        discussion = []
        current_topic = "introduction"
        
        while current_topic:
            # Get next speaker based on context
            next_speaker = self._select_next_speaker(current_topic, discussion)
            
            # Generate response based on context
            response = self._generate_contextual_response(next_speaker, current_topic, discussion)
            
            # Add response to discussion
            discussion.append({
                "speaker": next_speaker,
                "content": response,
                "topic": current_topic
            })
            
            # Update discussion state
            self._update_discussion_state(next_speaker, response, current_topic)
            
            # Determine next topic
            current_topic = self._determine_next_topic(current_topic, discussion)
            
            # Check if we should conclude
            if self._should_conclude(discussion):
                current_topic = "conclusion"
                
        return self._format_discussion(discussion)
        
    def _select_next_speaker(self, current_topic: str, discussion: List[Dict]) -> str:
        """Select next speaker based on context and natural flow"""
        if not discussion:
            return "Show Host"  # Host always starts
            
        last_speaker = discussion[-1]["speaker"]
        last_content = discussion[-1]["content"].lower()
        
        # Balance participation
        participation = self.discussion_state["interaction_count"]
        least_active = min(participation.items(), key=lambda x: x[1])[0]
        
        # If tactical point was made, let stats expert respond
        if last_speaker == "Tactical Analyst" and any(word in last_content for word in ["formation", "pressing", "tactics"]):
            return "Stats Expert"
            
        # If statistical point was made, let tactical analyst provide perspective
        if last_speaker == "Stats Expert" and any(word in last_content for word in ["numbers", "statistics", "data"]):
            return "Tactical Analyst"
            
        # If discussion is getting one-sided, have host redirect
        if len(discussion) >= 2 and discussion[-1]["speaker"] == discussion[-2]["speaker"]:
            return "Show Host"
            
        # If host just spoke, determine based on content and participation
        if last_speaker == "Show Host":
            if least_active != "Show Host" and participation[least_active] < participation["Show Host"] - 2:
                return least_active
            if "tactical" in last_content or "formation" in last_content:
                return "Tactical Analyst"
            if "statistics" in last_content or "numbers" in last_content:
                return "Stats Expert"
            return "Tactical Analyst" if participation["Stats Expert"] > participation["Tactical Analyst"] else "Stats Expert"
            
        # If an expert just spoke, maybe let other expert respond
        if last_speaker == "Stats Expert" and participation["Tactical Analyst"] < participation["Stats Expert"]:
            return "Tactical Analyst"
        if last_speaker == "Tactical Analyst" and participation["Stats Expert"] < participation["Tactical Analyst"]:
            return "Stats Expert"
            
        # Default to host to maintain flow
        return "Show Host"
        
    def _generate_contextual_response(self, speaker: str, topic: str, discussion: List[Dict]) -> str:
        """Generate a response appropriate for the context"""
        # Get recent context
        recent_context = discussion[-3:] if len(discussion) > 3 else discussion
        
        # Check if responding to a host question
        is_answering_question = False
        question_content = None
        if recent_context and recent_context[-1]["speaker"] == "Show Host" and "?" in recent_context[-1]["content"]:
            is_answering_question = True
            question_content = recent_context[-1]["content"]
        
        # Get current state
        current_state = {
            "topic": topic,
            "conclusions": self.discussion_state["conclusions_reached"],
            "topics_covered": self.discussion_state["topics_covered"],
            "key_moments": self.discussion_state["key_moments_discussed"],
            "is_answering_question": is_answering_question,
            "question_content": question_content
        }
        
        # Get relevant knowledge
        knowledge = {
            "interaction_style": self.interaction_styles[speaker],
            "match_data": self.match_data,
            "discussion_flow": self.discussion_flow
        }
        
        # Generate response based on speaker
        if speaker == "Show Host":
            return self.host.generate_response(current_state, recent_context, self.match_data, knowledge)
        elif speaker == "Stats Expert":
            return self.stats_expert.generate_response(current_state, recent_context, self.match_data, knowledge)
        else:
            return self.tactical_analyst.generate_response(current_state, recent_context, self.match_data, knowledge)
            
    def _update_discussion_state(self, speaker: str, response: str, topic: str):
        """Update discussion state based on latest response"""
        # Update speaker count
        self.discussion_state["interaction_count"][speaker] += 1
        
        # Update topics covered
        self.discussion_state["topics_covered"].add(topic)
        
        # Update last speaker
        self.discussion_state["last_speaker"] = speaker
        
        # Extract and update key moments discussed
        moments = self._extract_key_moments(response)
        self.discussion_state["key_moments_discussed"].update(moments)
        
        # Update conclusions if any reached
        if topic == "conclusion" or "conclude" in response.lower():
            self._update_conclusions(speaker, response)
            
    def _determine_next_topic(self, current_topic: str, discussion: List[Dict]) -> Optional[str]:
        """Determine next topic based on discussion flow and context"""
        if not current_topic or current_topic not in self.discussion_flow:
            return None
            
        # Get possible next topics
        next_topics = self.discussion_flow[current_topic]["next"]
        
        # If no next topics, we're done
        if not next_topics:
            return None
            
        # Filter out covered topics unless required
        available_topics = [
            topic for topic in next_topics
            if topic not in self.discussion_state["topics_covered"] or
            (topic in self.discussion_flow and self.discussion_flow[topic]["required"])
        ]
        
        # If no available topics, move to conclusion
        if not available_topics:
            return "conclusion" if "conclusion" not in self.discussion_state["topics_covered"] else None
            
        # Select most relevant topic based on context
        last_response = discussion[-1]["content"].lower() if discussion else ""
        
        # Prioritize topics mentioned in last response
        for topic in available_topics:
            if topic.replace("_", " ") in last_response:
                return topic
                
        return available_topics[0]
        
    def _should_conclude(self, discussion: List[Dict]) -> bool:
        """Determine if discussion should move to conclusion"""
        # Check if we've covered required topics
        required_topics = {
            topic for topic, config in self.discussion_flow.items()
            if config["required"]
        }
        covered_required = all(
            topic in self.discussion_state["topics_covered"]
            for topic in required_topics
            if topic != "conclusion"
        )
        
        # Check if we have enough interaction
        min_exchanges = 6  # Minimum number of exchanges before conclusion
        
        # Check if we have both tactical and statistical perspectives
        has_tactical = any(d["speaker"] == "Tactical Analyst" for d in discussion)
        has_statistical = any(d["speaker"] == "Stats Expert" for d in discussion)
        
        # Check if there are any unanswered questions from the host
        if discussion:
            last_exchange = discussion[-1]
            if (last_exchange["speaker"] == "Show Host" and 
                "?" in last_exchange["content"] and 
                len(discussion) < 2):
                return False  # Don't conclude if host just asked a question
                
        # Check if the last question was answered by both experts
        if len(discussion) >= 2 and "?" in discussion[-2]["content"]:
            responses_after_question = [
                d for d in discussion[-2:]
                if d["speaker"] in ["Tactical Analyst", "Stats Expert"]
            ]
            if len(responses_after_question) < 2:
                return False  # Need both experts to respond to the last question
        
        return (covered_required and 
                len(discussion) >= min_exchanges and 
                has_tactical and 
                has_statistical)
                
    def _format_discussion(self, discussion: List[Dict]) -> str:
        """Format the discussion in a readable way"""
        formatted = f"Match: {self._get_match_title()}\n"
        formatted += "=" * 50 + "\n\n"
        
        for entry in discussion:
            formatted += f"{entry['speaker']}:\n{entry['content']}\n\n"
            formatted += "-" * 30 + "\n\n"
            
        return formatted
        
    def _get_match_title(self) -> str:
        """Get formatted match title"""
        match_info = self.match_data.get("match_info", {})
        home_team = match_info.get("home_team", "Home Team")
        away_team = match_info.get("away_team", "Away Team")
        return f"{home_team} vs {away_team}"
        
    def _extract_key_moments(self, response: str) -> Set[str]:
        """Extract key moments mentioned in response"""
        # Implementation of key moment extraction
        return set()
        
    def _update_conclusions(self, speaker: str, response: str):
        """Update conclusions based on speaker and response"""
        if speaker == "Tactical Analyst":
            self.discussion_state["conclusions_reached"]["tactical"] = response
        elif speaker == "Stats Expert":
            self.discussion_state["conclusions_reached"]["statistical"] = response
        elif speaker == "Show Host" and all(self.discussion_state["conclusions_reached"].values()):
            self.discussion_state["conclusions_reached"]["overall"] = response
            
    def _can_contribute(self, speaker: str, topic: str) -> bool:
        """Determine if a speaker can contribute meaningfully to a topic"""
        if speaker == "Show Host":
            return True  # Host can always contribute
            
        topic_expertise = {
            "Stats Expert": ["statistical_analysis", "match_overview", "player_performance"],
            "Tactical Analyst": ["tactical_analysis", "key_moments", "team_comparison"]
        }
        
        return topic in topic_expertise.get(speaker, []) 