from typing import Dict, List
import json
import os
from datetime import datetime
from .base_agent import BaseAgent

class LearningAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.learning_data_dir = os.getenv("LEARNING_DATA_DIR", "/app/learning_data")
        self.personality_traits = self._load_personality_traits()
        self.conversation_patterns = self._load_conversation_patterns()
        
    def _load_personality_traits(self) -> Dict:
        """Load personality traits from real panelists"""
        traits_file = os.path.join(self.learning_data_dir, f"{self.agent_type}_traits.json")
        if os.path.exists(traits_file):
            with open(traits_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_conversation_patterns(self) -> Dict:
        """Load conversation patterns from real panelists"""
        patterns_file = os.path.join(self.learning_data_dir, f"{self.agent_type}_patterns.json")
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                return json.load(f)
        return {}
    
    def learn_from_interaction(self, interaction_data: Dict):
        """Learn from a new interaction with real panelists"""
        # Update personality traits
        if "personality_traits" in interaction_data:
            self.personality_traits.update(interaction_data["personality_traits"])
            self._save_personality_traits()
        
        # Update conversation patterns
        if "conversation_patterns" in interaction_data:
            self.conversation_patterns.update(interaction_data["conversation_patterns"])
            self._save_conversation_patterns()
    
    def _save_personality_traits(self):
        """Save updated personality traits"""
        os.makedirs(self.learning_data_dir, exist_ok=True)
        traits_file = os.path.join(self.learning_data_dir, f"{self.agent_type}_traits.json")
        with open(traits_file, 'w') as f:
            json.dump(self.personality_traits, f, indent=2)
    
    def _save_conversation_patterns(self):
        """Save updated conversation patterns"""
        os.makedirs(self.learning_data_dir, exist_ok=True)
        patterns_file = os.path.join(self.learning_data_dir, f"{self.agent_type}_patterns.json")
        with open(patterns_file, 'w') as f:
            json.dump(self.conversation_patterns, f, indent=2)
    
    def get_personality_traits(self) -> Dict:
        """Get current personality traits"""
        return self.personality_traits
    
    def get_conversation_patterns(self) -> Dict:
        """Get current conversation patterns"""
        return self.conversation_patterns 