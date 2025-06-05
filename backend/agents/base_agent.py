"""
Base agent class for panel discussion participants
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from openai import OpenAI
import json
from datetime import datetime
import os
from memory_system import ConversationMemory
from rag_system import FootballKnowledgeRAG
import time
import random
import openai
from services.rag_utils import rag_retrieve
from services.match_analysis_service import MatchAnalysisService
from services.match_data_store import MatchDataStore
from services.match_service import MatchService
from services.data_store import DataStore

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, system_prompt: str, personality: str, match_id: str = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.personality = personality
        self.match_id = match_id
        self.memory = ConversationMemory(match_id=match_id)
        self.rag_service = FootballKnowledgeRAG()
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_state = {
            "last_speaker": None,
            "turn_count": 0,
            "interruption_threshold": 0.5,  # Increased from 0.3 for more interruptions
            "match_id": match_id
        }
        self.conversation_history = []
        self.match_analysis = MatchAnalysisService()
        self.match_data = None
        self.role_specific_knowledge = None
        self.data_loaded = False
        
        # Initialize services
        self.match_service = MatchService()
        self.data_store = DataStore()
        
        # Load match data if match_id is provided
        if match_id:
            self._load_match_data()
        
    def _load_match_data(self) -> None:
        """Load match data from data store or fetch and save if not exists"""
        if not self.match_id:
            print("❌ No match ID provided")
            return
            
        # Try to load from data store first
        self.match_data = self.data_store.load_match_data(self.match_id)
        
        # If no data found, fetch from API and save
        if not self.match_data:
            print(f"Fetching match data for {self.match_id} from API...")
            self.match_data = self.match_service.get_match_info(self.match_id)
            if self.match_data:
                self.data_store.save_match_data(self.match_id, self.match_data)
        
        self.data_loaded = bool(self.match_data)
        if self.data_loaded:
            print(f"✅ Data loaded successfully for {self.name}")
        else:
            print(f"❌ Failed to load data for {self.name}")
    
    def get_response(self, current_state: Dict) -> str:
        """Generate a response based on current state"""
        if not self.data_loaded:
            self._load_match_data()
            
        if not self.match_data:
            return "No match data available."
            
        recent_context = current_state.get("flow", [])[-5:]  # Get last 5 exchanges
        knowledge = self._get_football_knowledge(current_state.get("current_topic", "general"))
        
        return self._generate_response(current_state, recent_context, self.match_data, knowledge)
    
    def _generate_response(self, current_state: Dict, recent_context: List[Dict], 
                          match_data: Dict, knowledge: Dict) -> str:
        """Generate response based on current state, context, and data"""
        raise NotImplementedError("Subclasses must implement _generate_response")
    
    def _get_football_knowledge(self, topic: str) -> Dict:
        """Get football knowledge from RAG system"""
        try:
            if not self.match_id:
                return {"stats": [], "rules": [], "tactics": [], "historical": []}
                
            response = rag_retrieve(self.match_id, f"football rules and statistics about {topic}")
            if isinstance(response, tuple) and len(response) >= 4:
                stats, rules, tactics, historical = response
            else:
                stats, rules, tactics, historical = [], [], [], []
            
            return {
                "stats": stats or [],
                "rules": rules or [],
                "tactics": tactics or [],
                "historical": historical or []
            }
        except Exception as e:
            print(f"❌ Error getting football knowledge: {e}")
            return {"stats": [], "rules": [], "tactics": [], "historical": []}
    
    def add_to_memory(self, prompt: str, response: str):
        """Add interaction to memory"""
        self.memory.add_memory(
            speaker=self.role,
            content=response,
            sentiment="neutral"  # Default sentiment
        )
        
        # Add to conversation history for tracking
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response
        })
        
        # Keep only last 20 interactions in history
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_relevant_context(self, query: str, collection: str = "matches") -> List[Dict]:
        """Get relevant context from RAG service"""
        return self.rag_service.get_relevant_context(query, collection)
    
    def add_to_discussion(self, match_id: str, content: str):
        """Add a discussion point to the RAG service"""
        self.rag_service.add_discussion(match_id, self.role, content)
    
    def should_speak(self, current_context: Dict) -> bool:
        """Determine if the agent should speak based on context and conversation state"""
        # Always speak if directly addressed
        if current_context.get("addressed_to") == self.role:
            return True
            
        # Calculate speaking probability based on:
        # 1. Time since last spoke
        # 2. Relevance to current topic
        # 3. Natural interruption opportunity
        relevance_score = self.calculate_relevance(current_context)
        time_since_last_spoke = self.get_time_since_last_spoke()
        
        # Higher probability if:
        # - Topic is highly relevant to agent's expertise
        # - It's been a while since agent spoke
        # - Current speaker is pausing or finished a point
        speaking_probability = (
            relevance_score * 0.5 +
            min(time_since_last_spoke / 60, 1.0) * 0.3 +
            (1 if current_context.get("speaker_paused", False) else 0) * 0.2
        )
        
        return speaking_probability > self.conversation_state["interruption_threshold"]
    
    def calculate_relevance(self, context: Dict) -> float:
        """Calculate how relevant the current topic is to this agent's expertise"""
        # Get relevant context from RAG
        relevant_context = self.get_relevant_context(context.get("current_topic", ""))
        
        # Calculate relevance score based on context matches
        if not relevant_context:
            return 0.0
            
        # Higher score for more recent and more relevant matches
        relevance_scores = [
            c.get("relevance_score", 0.0) * (1.0 - (i * 0.1))  # Decay factor
            for i, c in enumerate(relevant_context[:3])  # Consider top 3 matches
        ]
        
        # Also consider agent's recent memories about the topic
        agent_memories = self.memory.get_relevant_memories(context.get("current_topic", ""), k=3)
        if agent_memories:
            memory_scores = [0.5 * (1.0 - (i * 0.1)) for i in range(len(agent_memories))]
            relevance_scores.extend(memory_scores)
        
        return max(relevance_scores) if relevance_scores else 0.0
    
    def get_time_since_last_spoke(self) -> float:
        """Get time in seconds since agent last spoke"""
        # Get agent's previous statements
        agent_memories = self.memory.get_agent_stance(self.role)
        
        if not agent_memories:
            return float('inf')
            
        last_spoke = agent_memories[-1]["timestamp"]
        current_time = datetime.now().isoformat()
        
        # Convert to datetime objects and calculate difference
        last_spoke_dt = datetime.fromisoformat(last_spoke)
        current_dt = datetime.fromisoformat(current_time)
        
        return (current_dt - last_spoke_dt).total_seconds()
    
    def learn_from_interaction(self, interaction: Dict):
        """Learn from a specific interaction"""
        self.rag_service.add_to_knowledge(
            text=f"Prompt: {interaction['prompt']}\nResponse: {interaction['response']}",
            metadata={
                "speaker_role": self.role,
                "context": str(interaction.get("context", ""))
            }
        )
    
    def learn_from_match(self, match_data: Dict):
        """Learn from match data"""
        self.rag_service.learn_from_match(match_data)
    
    def should_interrupt(self, other_agent_type: str, content: str) -> bool:
        """Determine if this agent should interrupt based on content"""
        # Use memory system's built-in interruption logic
        if self.memory.should_interrupt(other_agent_type, content):
            return True
            
        # Additional custom interruption logic
        if any(trigger in content.lower() for trigger in self._get_interruption_triggers()):
            return random.random() < 0.8  # 80% chance if trigger word found
            
        # Random chance of interruption for natural flow
        return random.random() < 0.4  # Increased from 0.2 to 0.4 for more dynamic discussion
    
    def get_interruption(self, content: str) -> str:
        """Generate an interruption response"""
        match_context = json.dumps(self.match_data, indent=2) if self.match_data else "No match data available"
        
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\nMatch Data:\n{match_context}"},
            {"role": "user", "content": f"Generate an interruption to the following statement:\n{content}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.8,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating interruption: {e}")
            return "Excuse me, but I have to disagree with that point."
    
    def analyze(self, match_data: Dict) -> str:
        """Analyze match data - to be implemented by specific agents"""
        raise NotImplementedError("Specific agents must implement their own analysis method")
    
    def _format_match_info(self, info: Dict) -> str:
        """Format match information"""
        if not info:
            return "No match information available"
        return str(info)  # Override in specific agents for better formatting
    
    def _format_statistics(self, stats: Dict) -> str:
        """Format statistics"""
        if not stats:
            return "No statistics available"
        return str(stats)  # Override in specific agents for better formatting
    
    def _get_recent_context(self, state: Dict) -> List[Dict]:
        """Get recent discussion context"""
        if not state.get("flow"):
            return []
            
        # Get the last 5 exchanges
        recent_exchanges = state["flow"][-5:]
        
        # Format each exchange as a dictionary
        context = []
        for exchange in recent_exchanges:
            context.append({
                "speaker": exchange["speaker"],
                "message": exchange["content"]
            })
        
        return context
    
    def _get_interruption_triggers(self) -> List[str]:
        """Get triggers that might cause this agent to interrupt"""
        return [
            "completely wrong",
            "i disagree",
            "that's not true",
            "actually",
            "incorrect",
            "false",
            "misleading",
            "statistics show",
            "in my experience",
            "i must point out"
        ]

    def get_controversial_take(self, match_data: Dict) -> str:
        """Generate a controversial statement about the match"""
        match_context = json.dumps(self.match_data, indent=2) if self.match_data else "No match data available"
        
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\nMatch Data:\n{match_context}\n\nAdditional instruction: Generate a controversial but well-reasoned take about the match that will spark debate."},
            {"role": "user", "content": f"As {self.role}, give a controversial opinion about this match that will get other panel members talking. Use specific data or observations to back up your point."}
        ]
        
        response = self._get_completion(messages)
        return response

    def get_reaction(self, statement: str) -> str:
        """React to another panelist's statement"""
        match_context = json.dumps(self.match_data, indent=2) if self.match_data else "No match data available"
        
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\nMatch Data:\n{match_context}\n\nAdditional instruction: Generate a strong reaction to another panelist's statement."},
            {"role": "user", "content": f"As {self.role}, react strongly to this statement: '{statement}'. You can agree passionately or disagree strongly, but back up your position with expertise and facts from the match data."}
        ]
        
        response = self._get_completion(messages)
        return response

    def get_defensive_response(self, interruption: str) -> str:
        """Generate a quick defensive response to an interruption"""
        match_context = json.dumps(self.match_data, indent=2) if self.match_data else "No match data available"
        
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\nMatch Data:\n{match_context}\n\nAdditional instruction: Generate a quick, defensive response to someone who interrupted you."},
            {"role": "user", "content": f"As {self.role}, respond quickly and defensively to this interruption: '{interruption}'. Keep it short but impactful, using match facts to support your position."}
        ]
        
        response = self._get_completion(messages)
        return response

    def _get_completion(self, messages: List[Dict]) -> str:
        """Helper method to get completion from OpenAI API with error handling"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.8,
                max_tokens=200  # Shorter for quick responses
            )
            return str(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in _get_completion: {e}")
            # Return a fallback response
            return "I need a moment to collect my thoughts on that."

    def consider_response(self, last_utterance, history):
        # Use RAG to get context
        stats, news = rag_retrieve(self.match_id, last_utterance)
        match_context = json.dumps(self.match_data, indent=2) if self.match_data else "No match data available"
        context = f"Match Data:\n{match_context}\nStats: {stats}\nNews: {news}\nHistory: {history}\n"
        
        prompt = (
            f"You are {self.name}, a {self.personality} football panelist. "
            f"Given the context and the last utterance: '{last_utterance}', "
            "what would you say next? Use specific match data to support your points. "
            "Respond naturally, as if in a live discussion."
        )
        full_prompt = context + prompt
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": full_prompt}]
        )
        text = response.choices[0].message.content.strip()
        
        # Simple desire function: respond if mentioned or if you have a strong opinion
        desire = 1.0 if self.name.lower() in last_utterance.lower() else 0.5
        
        # Add to memory
        self.memory.add_memory(
            speaker=self.role,
            content=text,
            sentiment="neutral"  # Default sentiment
        )
        return text, desire

    def _format_conversation_history(self, state: Dict) -> str:
        """Format the full conversation history for context"""
        if not state.get("flow"):
            return "No previous conversation."
            
        history = []
        for exchange in state["flow"]:
            speaker = exchange["speaker"]
            content = exchange["content"]
            history.append(f"{speaker}: {content}")
            
        return "\n".join(history)

    def _update_conversation_history(self, message: str, speaker: str):
        """Update conversation history with new message"""
        self.conversation_history.append({
            "speaker": speaker,
            "message": message
        })

class RateLimitTracker:
    def __init__(self):
        self.request_times = []
        self.token_counts = []
        self.minute_window = 60  # 1 minute window
        self.day_window = 86400  # 24 hour window
        self.last_retry_delay = 0
        
    def can_make_request(self):
        now = time.time()
        # Remove old entries
        minute_old_entries = [t for t in zip(self.request_times, self.token_counts) 
                            if now - t[0] < self.minute_window]
        day_old_entries = [t for t in zip(self.request_times, self.token_counts) 
                          if now - t[0] < self.day_window]
        
        self.request_times = [t[0] for t in minute_old_entries]
        self.token_counts = [t[1] for t in minute_old_entries]
        
        # Check RPM (5000 per minute)
        if len(minute_old_entries) >= 4990:  # Leave some buffer
            return False
            
        # Check TPM (450,000 per minute)
        if sum(t[1] for t in minute_old_entries) >= 440000:  # Leave some buffer
            return False
            
        # Check RPD (Daily request limit)
        if len(day_old_entries) >= 200000:  # Example daily limit
            return False
            
        # Check TPD (Daily token limit)
        if sum(t[1] for t in day_old_entries) >= 10000000:  # Example daily token limit
            return False
            
        return True
    
    def add_request(self, token_count):
        now = time.time()
        self.request_times.append(now)
        self.token_counts.append(token_count)
    
    def get_retry_delay(self, attempt):
        """Calculate retry delay with exponential backoff and jitter"""
        if attempt == 0:
            self.last_retry_delay = 0.2  # Base delay 200ms
            return self.last_retry_delay
            
        # Exponential backoff with jitter
        self.last_retry_delay = min(60, self.last_retry_delay * 2)  # Cap at 60 seconds
        jitter = random.uniform(0, 0.1 * self.last_retry_delay)  # 10% jitter
        return self.last_retry_delay + jitter
