"""
Memory system for agents to store and recall conversation history
"""
from typing import List, Dict
import json
from datetime import datetime

class ConversationMemory:
    def __init__(self, initial_state: str = "neutral", match_id: str = None):
        self.memories = []
        self.emotional_state = initial_state
        self.agreement_levels = {}  # Track agreement/disagreement with other agents
        self.match_id = match_id
        
    def add_memory(self, speaker: str, content: str, sentiment: str = "neutral"):
        """Add a new memory of something said in the conversation"""
        memory = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "content": content,
            "sentiment": sentiment,
            "emotional_impact": self._evaluate_emotional_impact(content),
            "match_id": self.match_id
        }
        self.memories.append(memory)
        self._update_emotional_state(memory)
        self._update_agreement_levels(speaker, content)
    
    def get_relevant_memories(self, topic: str, k: int = 5) -> List[Dict]:
        """Get memories relevant to a specific topic"""
        # Simple keyword matching for now, could be enhanced with embeddings
        relevant = []
        for memory in reversed(self.memories):  # Most recent first
            if topic.lower() in memory["content"].lower():
                relevant.append(memory)
                if len(relevant) >= k:
                    break
        return relevant
    
    def get_agent_stance(self, agent: str) -> List[Dict]:
        """Get an agent's previous statements and stances"""
        return [m for m in self.memories if m["speaker"] == agent]
    
    def should_interrupt(self, speaker: str, content: str) -> bool:
        """Determine if current content warrants an interruption"""
        # Check emotional state
        if self.emotional_state in ["angry", "frustrated"]:
            return True
            
        # Check agreement level with speaker
        if self.agreement_levels.get(speaker, 0) < -0.5:  # High disagreement
            return True
            
        # Check content triggers
        triggers = self._get_interruption_triggers()
        return any(trigger in content.lower() for trigger in triggers)
    
    def _evaluate_emotional_impact(self, content: str) -> float:
        """Evaluate the emotional impact of content"""
        # Simple sentiment analysis based on keywords
        positive_words = ["agree", "good", "excellent", "right", "perfect", "well"]
        negative_words = ["disagree", "wrong", "bad", "incorrect", "mistake"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        return (positive_count - negative_count) / max(1, positive_count + negative_count)
    
    def _update_emotional_state(self, memory: Dict):
        """Update emotional state based on new memory"""
        impact = memory["emotional_impact"]
        sentiment = memory["sentiment"]
        
        # Define state transitions based on impact and sentiment
        transitions = {
            "neutral": {
                "positive": "excited",
                "negative": "frustrated",
                "neutral": "neutral"
            },
            "excited": {
                "positive": "excited",
                "negative": "frustrated",
                "neutral": "positive"
            },
            "frustrated": {
                "positive": "neutral",
                "negative": "angry",
                "neutral": "frustrated"
            },
            "angry": {
                "positive": "frustrated",
                "negative": "angry",
                "neutral": "frustrated"
            },
            "positive": {
                "positive": "excited",
                "negative": "neutral",
                "neutral": "positive"
            }
        }
        
        # Determine sentiment direction
        if impact > 0.3:
            direction = "positive"
        elif impact < -0.3:
            direction = "negative"
        else:
            direction = "neutral"
            
        # Update state using transition table
        current_state = self.emotional_state
        if current_state in transitions and direction in transitions[current_state]:
            self.emotional_state = transitions[current_state][direction]
    
    def _update_agreement_levels(self, speaker: str, content: str):
        """Update agreement levels with other agents"""
        # Initialize if not exists
        if speaker not in self.agreement_levels:
            self.agreement_levels[speaker] = 0.0
            
        # Update based on content and emotional impact
        impact = self._evaluate_emotional_impact(content)
        current_level = self.agreement_levels[speaker]
        # Slowly move agreement level based on emotional impact
        self.agreement_levels[speaker] = max(min(current_level + (impact * 0.1), 1.0), -1.0)
    
    def _get_interruption_triggers(self) -> List[str]:
        """Get words that might trigger interruption based on emotional state"""
        base_triggers = ["disagree", "wrong", "incorrect", "mistake", "nonsense"]
        if self.emotional_state == "angry":
            return base_triggers + ["think", "maybe", "probably", "suggest"]
        elif self.emotional_state == "frustrated":
            return base_triggers + ["actually", "however", "but"]
        return base_triggers

class PanelMemory:
    def __init__(self, match_id: str = None):
        self.agents = {}
        self.discussion_flow = []
        self.interruption_count = 0
        self.host_interventions = 0
        self.current_topic = None
        self.topic_history = []
        self.match_id = match_id
        
    def add_agent(self, agent_name: str):
        """Add a new agent to the panel with initial emotional state"""
        if agent_name not in self.agents:
            # Set different initial states for different agents to encourage participation
            initial_states = {
                "Show Host": "neutral",
                "Stats Analyst": "excited",  # Eager to share statistics
                "Football Coach": "positive",  # Ready to discuss tactics
                "Home Fan": "excited",  # Enthusiastic about their team
                "Away Fan": "frustrated"  # Creates tension in discussion
            }
            self.agents[agent_name] = ConversationMemory(initial_states.get(agent_name, "neutral"), self.match_id)
    
    def add_statement(self, speaker: str, content: str, sentiment: str = "neutral"):
        """Add a statement to all agents' memories and update conversation state"""
        # Create statement record
        statement = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "content": content,
            "sentiment": sentiment,
            "topic": self._detect_topic(content),
            "match_id": self.match_id
        }
        
        # Update current topic if detected
        if statement["topic"]:
            self.current_topic = statement["topic"]
            self.topic_history.append(statement["topic"])
        
        # Add to discussion flow
        self.discussion_flow.append(statement)
        
        # Each agent processes and stores the statement
        for agent in self.agents.values():
            agent.add_memory(speaker, content, sentiment)
    
    def _detect_topic(self, content: str) -> str:
        """Detect the main topic of a statement"""
        content_lower = content.lower()
        
        # Define topic keywords
        topic_keywords = {
            "tactics": ["tactics", "formation", "strategy", "press", "counter"],
            "statistics": ["stats", "statistics", "numbers", "possession", "shots"],
            "player_performance": ["player", "performance", "played", "scored", "assist"],
            "refereeing": ["referee", "decision", "penalty", "foul", "card"],
            "atmosphere": ["fans", "crowd", "atmosphere", "support", "stadium"],
            "history": ["history", "previous", "last season", "record"],
            "transfer": ["transfer", "signing", "player", "market"]
        }
        
        # Check for topic matches
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return topic
        
        return None
    
    def get_discussion_state(self) -> Dict:
        """Get current state of the discussion"""
        return {
            "flow": self.discussion_flow,
            "interruptions": self.interruption_count,
            "host_interventions": self.host_interventions,
            "emotional_states": {
                name: memory.emotional_state
                for name, memory in self.agents.items()
            },
            "current_topic": self.current_topic,
            "topic_history": self.topic_history[-5:],  # Last 5 topics
            "recent_speakers": [
                exchange["speaker"] 
                for exchange in self.discussion_flow[-3:]
            ] if self.discussion_flow else []
        }
    
    def should_host_intervene(self) -> bool:
        """Determine if host should intervene based on discussion state"""
        # Count agents in negative emotional states
        angry_agents = sum(
            1 for agent in self.agents.values()
            if agent.emotional_state in ["angry", "frustrated"]
        )
        
        # Get recent speakers
        recent_speakers = [
            exchange["speaker"] 
            for exchange in self.discussion_flow[-3:]
        ] if self.discussion_flow else []
        
        # Intervention conditions
        if angry_agents >= 2:  # Multiple agents are upset
            return True
        if self.interruption_count >= 3:  # Too many rapid interruptions
            return True
        if len(recent_speakers) >= 3 and len(set(recent_speakers)) == 1:  # One person dominating
            return True
        if len(self.topic_history) >= 3 and len(set(self.topic_history[-3:])) == 1:  # Stuck on one topic
            return True
            
        return False
    
    def get_agent_context(self, agent_name: str) -> Dict:
        """Get relevant context for a specific agent"""
        agent_memory = self.agents.get(agent_name)
        if not agent_memory:
            return {}
            
        return {
            "emotional_state": agent_memory.emotional_state,
            "recent_memories": agent_memory.get_relevant_memories(self.current_topic or ""),
            "agreement_levels": agent_memory.agreement_levels,
            "discussion_state": self.get_discussion_state()
        }
    
    def save_to_file(self, filename: str):
        """Save discussion history to file"""
        with open(filename, 'w') as f:
            json.dump({
                "discussion_flow": self.discussion_flow,
                "statistics": {
                    "interruptions": self.interruption_count,
                    "host_interventions": self.host_interventions
                }
            }, f, indent=2)
    
    def load_from_file(self, filename: str):
        """Load discussion history from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            self.discussion_flow = data["discussion_flow"]
            self.interruption_count = data["statistics"]["interruptions"]
            self.host_interventions = data["statistics"]["host_interventions"] 