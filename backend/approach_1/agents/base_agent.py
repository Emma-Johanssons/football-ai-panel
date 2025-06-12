"""
Base agent class for panel discussion participants using LangChain
"""
from langchain.agents import AgentExecutor
from langchain.agents.agent import LLMSingleActionAgent
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from typing import Dict, List, Optional
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
import json
from services.match_service import MatchService
from services.data_store import DataStore
import random
import re
from datetime import datetime

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str, personality: str, match_id: str = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.personality = personality
        self.match_id = match_id
        self.match_data = None
        self.data_store = DataStore()
        self.match_service = MatchService()
        
        # Initialize with default personality traits
        self.personality_traits = {
            "detail_focus": 0.5,     # How much they focus on details vs overview
            "emotion_level": 0.3,    # How emotional vs analytical they are
            "topic_expertise": 0.5   # Level of expertise in specific topics
        }
        
        # Map roles to learned personalities
        self.personality_mapping = {
            "Show Host": ["joe_devine", "patrick_van_straaten"],  # Tifo and Football Daily hosts
            "Tactical Analyst": ["alex_stewart", "coach_matt"],   # Tactical experts
            "Stats Expert": ["joe_thomlinson", "dylan"],         # Stats focused analysts
        }
        
        # Try to load a matching personality
        self._load_matching_personality()
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(temperature=0.7)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define agent tools
        self.tools = [
            Tool(
                name="get_next_speaker",
                func=self._determine_next_speaker,
                description="Determine who should speak next"
            )
        ]
        
        # Create agent prompt
        self.agent_prompt = PromptTemplate(
            input_variables=["chat_history", "match_data", "current_topic", "tools", "tool_names", "agent_scratchpad"],
            template=f"""You are {self.role}, a {self.personality} football expert.
            
Your task is to analyze and discuss football matches naturally, using the provided match data and discussion history.

Previous discussion:
{{chat_history}}

Match data:
{{match_data}}

Current topic: {{current_topic}}

Think carefully about what information you need before responding.
Keep responses natural and focused on your expertise.

Available tools: {{tool_names}}

This is your scratchpad for working through the problem:
{{agent_scratchpad}}"""
        )
        
        # Initialize output parser
        self.output_parser = ReActSingleInputOutputParser()
        
        # Create agent executor
        self.agent = LLMSingleActionAgent(
            llm_chain=LLMChain(
                llm=self.llm,
                prompt=self.agent_prompt
            ),
            allowed_tools=[tool.name for tool in self.tools],
            output_parser=self.output_parser,
            stop=["\nObservation:", "\nThought:", "\nAction:"],
            format_scratchpad=format_log_to_str
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
        
    def _determine_next_speaker(self, current_state: Dict) -> str:
        """Determine who should speak next based on discussion flow"""
        try:
            flow = current_state.get("flow", [])
            if not flow:
                return "Show Host"  # Always start with host
                
            last_speaker = flow[-1].get("speaker")
            current_topic = current_state.get("current_topic", "")
            
            # Don't repeat speakers unless necessary
            if last_speaker == "Show Host":
                return "Tactical Analyst" if random.random() > 0.5 else "Stats Expert"
            elif last_speaker == "Tactical Analyst":
                return "Stats Expert" if "tactics" in current_topic.lower() else "Show Host"
            elif last_speaker == "Stats Expert":
                return "Tactical Analyst" if "stats" in current_topic.lower() else "Show Host"
            
            return "Show Host"  # Default to host
            
        except Exception as e:
            print(f"Error determining next speaker: {e}")
            return "Show Host"
            
    async def get_response(self, current_state: Dict) -> str:
        """Generate a response using LangChain agent"""
        try:
            # Ensure match data is properly formatted
            if isinstance(current_state.get("match_data"), str):
                try:
                    match_data = json.loads(current_state["match_data"])
                    current_state["match_data"] = match_data
                except:
                    match_data = {}
                    
            # Add specific focus areas based on role
            if self.role == "Stats Expert":
                current_state["focus"] = ["match_statistics", "player_stats", "team_performance"]
            elif self.role == "Tactical Analyst":
                current_state["focus"] = ["formations", "tactical_analysis", "player_positions"]
            elif self.role == "Show Host":
                current_state["focus"] = ["overall_flow", "key_moments", "narrative"]
            
            # Convert sets to lists for JSON serialization
            serializable_state = self._make_json_serializable(current_state)
            
            # Run agent to get response
            response = await self.agent_executor.arun(
                input=json.dumps(serializable_state, indent=2)
            )
            
            # Validate response
            if not response or response.strip() == "" or "error" in response.lower():
                print("⚠️ Invalid response from agent, using fallback")
                return self._get_fallback_response()
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._get_fallback_response()
            
    def _make_json_serializable(self, obj):
        """Convert object to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _get_fallback_response(self) -> str:
        """Get a fallback response when normal generation fails"""
        return f"As a {self.role}, I need to analyze this further."

    def _load_matching_personality(self):
        """Load a matching personality based on role"""
        if self.role in self.personality_mapping:
            # Get potential personalities for this role
            potential_personalities = self.personality_mapping[self.role]
            
            # Try each personality until we find one that exists
            for personality_file in potential_personalities:
                try:
                    self.load_personality(personality_file)
                    print(f"✅ Loaded personality from {personality_file} for {self.role}")
                    return
                except FileNotFoundError:
                            continue
            
            print(f"⚠️ No matching personality found for {self.role}, using defaults")
        else:
            print(f"⚠️ No personality mapping for role: {self.role}")
            
    def load_personality(self, role_model: str):
        """Load personality traits based on a learned profile"""
        try:
            with open(f"learning_data/personalities/{role_model}.json", "r") as f:
                learned_data = json.load(f)
                
                # Update personality traits
                if "traits" in learned_data:
                    self.personality_traits.update(learned_data["traits"])
                    
                # Update system prompt with learned style
                style_prompt = self._generate_style_prompt(learned_data)
                self.system_prompt = f"{self.system_prompt}\n\n{style_prompt}"
                
                print(f"Loaded personality traits for {role_model}:")
                for trait, value in self.personality_traits.items():
                    print(f"- {trait}: {value:.2f}")
                    
        except FileNotFoundError:
            print(f"No learned data for {role_model}, using default personality")
            
    def _generate_style_prompt(self, learned_data: Dict) -> str:
        """Generate a style prompt based on learned personality"""
        traits = learned_data.get("traits", {})
        
        style_elements = []
        
        # Add detail focus
        if traits.get("detail_focus", 0) > 0.7:
            style_elements.append("You are very detail-oriented and thorough in your analysis")
        elif traits.get("detail_focus", 0) < 0.3:
            style_elements.append("You prefer to give broad, high-level insights")
            
        # Add emotional style
        if traits.get("emotion_level", 0) > 0.7:
            style_elements.append("You are passionate and emotional in your commentary")
        elif traits.get("emotion_level", 0) < 0.3:
            style_elements.append("You maintain a calm, analytical approach")
            
        # Add expertise focus
        if traits.get("topic_expertise", 0) > 0.7:
            style_elements.append("You frequently reference specific tactical concepts and technical details")
        
        return "\n".join([
            "Speaking style:",
            *[f"- {element}" for element in style_elements]
        ])
        
    def should_interrupt(self, speaker: str, content: str) -> bool:
        """Determine if agent should interrupt based on personality"""
        if random.random() < self.personality_traits["interruption_frequency"]:
            # Check for trigger words or phrases that would cause interruption
            trigger_words = ["completely wrong", "always", "never", "impossible"]
            return any(word in content.lower() for word in trigger_words)
            return False
        
    def add_personality(self, content: str) -> str:
        """Add personality elements to response based on learned traits"""
        if not content:
            return content
            
        # Add detail based on detail_focus trait
        if random.random() < self.personality_traits["detail_focus"]:
            details = [
                "To break this down further,",
                "Looking at the specific details,",
                "If we analyze this closely,"
            ]
            content = f"{random.choice(details)} {content}"
            
        # Add emotional elements based on emotion_level
        if random.random() < self.personality_traits["emotion_level"]:
            emotions = [
                "What's really exciting here is",
                "I'm particularly impressed by",
                "This is fascinating because"
            ]
            content = f"{random.choice(emotions)} {content}"
            
        # Add expertise elements based on topic_expertise
        if random.random() < self.personality_traits["topic_expertise"]:
            expertise = [
                "From a tactical perspective,",
                "The statistical analysis shows",
                "Looking at the technical aspects,"
            ]
            content = f"{random.choice(expertise)} {content}"
            
        return content
        
    def format_response(self, content: str) -> str:
        """Format response with personality and learned phrases"""
        # Add transitions
        if random.random() > 0.7:  # 30% chance
            transition = random.choice(self.learned_phrases["transitions"])
            content = f"{transition}, {content}"
            
        # Add agreement/disagreement based on personality
        if random.random() < self.personality_traits["disagreement_likelihood"]:
            phrase = random.choice(self.learned_phrases["disagreement"])
            content = f"{phrase}. {content}"
        else:
            phrase = random.choice(self.learned_phrases["agreement"])
            content = f"{phrase}. {content}"
            
        return self.add_personality(content)

    async def _load_match_data(self) -> bool:
        """Load match data from storage or fetch if needed"""
        if self.match_data:
            return True
            
        try:
            self.match_data = self.data_store.load_match_data(self.match_id)
            if not self.match_data:
                success = await self.match_service.get_match_data(self.match_id)
                if success:
                    self.match_data = self.data_store.load_match_data(self.match_id)
            return bool(self.match_data)
        except Exception as e:
            print(f"Error loading match data: {e}")
            return False
            
    def _load_youtube_personality(self):
        """Load YouTube personality traits based on role"""
        try:
            personality_file = None
            if self.role == "Show Host":
                # Alternate between Joe Devine and Patrick van Straaten
                import random
                personality_file = random.choice([
                    "joe_devine.json",
                    "patrick_van_straaten.json"
                ])
            elif self.role == "Tactical Analyst":
                # Alternate between Alex Stewart and Coach Matt
                import random
                personality_file = random.choice([
                    "alex_stewart.json",
                    "coach_matt.json"
                ])
            elif self.role == "Stats Expert":
                # Alternate between Joe Thomlinson and Dylan
                import random
                personality_file = random.choice([
                    "joe_thomlinson.json",
                    "dylan.json"
                ])
                
            if personality_file:
                import os
                import json
                file_path = os.path.join("backend/learning_data/personalities", personality_file)
                with open(file_path, 'r') as f:
                    personality = json.load(f)
                    self.personality_traits.update(personality.get("traits", {}))
                        
        except Exception as e:
            print(f"Failed to load YouTube personality: {e}")
            
    def get_combined_personality(self) -> dict:
        """Get combined personality traits from both role and YouTube learning"""
        base_traits = self.role_traits.get(self.role, {})
        
        # Combine role-based and YouTube-learned traits
        combined = {
            "discussion_style": {
                "neutrality": base_traits.get("neutrality", 0.5),
                "focus": base_traits.get("discussion_focus", "general"),
                "depth": (base_traits.get("analysis_depth", 0.5) + self.personality_traits.get("detail_focus", 0.5)) / 2
            },
            "emotional_style": {
                "base_emotion_level": self.personality_traits.get("emotion_level", 0.5),
                "excitement": base_traits.get("emotional_range", {}).get("excitement", 0.5),
                "criticism": base_traits.get("emotional_range", {}).get("criticism", 0.5)
            },
            "expertise": {
                "topic_knowledge": self.personality_traits.get("topic_expertise", 0.5),
                "role_specific": base_traits.get("analysis_depth", 0.5)
            }
        }
        
        # Add role-specific traits
        if self.role == "Tactical Analyst":
            combined["coaching_perspective"] = base_traits.get("coaching_perspective", {})
        elif self.role == "Stats Expert":
            combined["statistical_perspective"] = base_traits.get("statistical_perspective", {})
            
        return combined
        
    def _add_player_context(self, response: str, match_data: dict) -> str:
        """Add player names and context to responses"""
        try:
            # Get player data
            lineups = match_data.get("match_info", {}).get("lineups", {})
            events = match_data.get("match_info", {}).get("events", [])
            
            # Track mentioned players to avoid repetition
            mentioned_players = set()
            
            # Replace generic positions with player names
            position_patterns = {
                r"central midfielder": lambda: self._get_random_player(lineups, "MID", mentioned_players),
                r"striker": lambda: self._get_random_player(lineups, "FWD", mentioned_players),
                r"winger": lambda: self._get_random_player(lineups, "FWD", mentioned_players),
                r"defender": lambda: self._get_random_player(lineups, "DEF", mentioned_players),
                r"goalkeeper": lambda: self._get_random_player(lineups, "GK", mentioned_players)
            }
            
            for pattern, player_func in position_patterns.items():
                matches = re.finditer(pattern, response, re.IGNORECASE)
                offset = 0
                for match in matches:
                    player = player_func()
                    if player:
                        start = match.start() + offset
                        end = match.end() + offset
                        response = response[:start] + player + response[end:]
                        offset += len(player) - (end - start)
            
            return response
            
        except Exception as e:
            print(f"Error adding player context: {e}")
            return response
            
    def _get_random_player(self, lineups: dict, position: str, mentioned: set) -> str:
        """Get a random player from a specific position that hasn't been mentioned"""
        try:
            available_players = []
            for team_lineup in lineups.values():
                for player in team_lineup:
                    if (player.get("position") == position and 
                        player.get("name") not in mentioned):
                        available_players.append(player.get("name"))
            
            if available_players:
                player = random.choice(available_players)
                mentioned.add(player)
                return player
            return ""
                        
        except Exception as e:
            print(f"Error getting random player: {e}")
            return ""

    def _avoid_formation_repetition(self, response: str) -> str:
        """Avoid repeating formation numbers too often"""
        try:
            # Count formation mentions
            formation_patterns = [r'\d-\d-\d', r'\d-\d-\d-\d']
            formation_count = sum(len(re.findall(pattern, response)) for pattern in formation_patterns)
            
            # If formations are mentioned more than twice, replace subsequent mentions
            if formation_count > 2:
                response = re.sub(r'(\d-\d-\d(?:-\d)?)', 'their setup', response, count=formation_count-2)
                
            return response
            
        except Exception as e:
            print(f"Error avoiding formation repetition: {e}")
        return response
        
    def _vary_expert_intros(self) -> str:
        """Get varied introduction phrases for experts"""
        intros = {
            "Stats Expert": [
                "The numbers tell an interesting story here.",
                "Looking at the match statistics,",
                "The data shows some clear patterns.",
                "Breaking down the key metrics,",
                "Analyzing the match numbers,"
            ],
            "Tactical Analyst": [
                "From a coaching perspective,",
                "Looking at the tactical setup,",
                "Analyzing the game plan,",
                "Breaking down the strategy,",
                "Examining the tactical approach,"
            ],
            "Show Host": [
                "Let's analyze",
                "Interesting point about",
                "That brings us to",
                "Moving on to",
                "Looking at"
            ]
        }
        
        return random.choice(intros.get(self.role, [""])) if self.role in intros else ""

    def adjust_response_style(self, response: str, match_data: dict = None) -> str:
        """Adjust response based on combined personality traits"""
        try:
            # Get personality traits
            personality = self.get_combined_personality()
            
            # Add player names and context
            if match_data:
                response = self._add_player_context(response, match_data)
            
            # Avoid formation repetition
            response = self._avoid_formation_repetition(response)
            
            # Add varied expert intros
            if not any(phrase in response for phrase in ["Good evening", "Thank you", "Let's welcome"]):
                intro = self._vary_expert_intros()
                if intro and not response.startswith(intro):
                    response = f"{intro} {response}"
            
            # Apply role-specific adjustments
            if self.role == "Show Host":
                if personality["emotional_style"]["base_emotion_level"] > 0.7:
                    response = self._add_excitement(response)
                if personality["discussion_style"]["neutrality"] > 0.8:
                    response = self._make_more_neutral(response)
                    
            elif self.role == "Tactical Analyst":
                if personality["expertise"]["role_specific"] > 0.7:
                    response = self._add_coaching_perspective(response)
                if personality.get("coaching_perspective", {}).get("tactical_adaptation", 0) > 0.8:
                    response = self._add_tactical_insights(response)
                    
            elif self.role == "Stats Expert":
                if personality["expertise"]["role_specific"] > 0.7:
                    response = self._add_statistical_context(response)
                if personality.get("statistical_perspective", {}).get("rule_application", 0) > 0.8:
                    response = self._add_rule_references(response)
            
            return response
            
        except Exception as e:
            print(f"Error adjusting response style: {e}")
        return response

    def _add_excitement(self, text: str) -> str:
        """Add more emotional language for exciting moments"""
        # Implementation details...
        return text
        
    def _make_more_neutral(self, text: str) -> str:
        """Make the language more neutral and balanced"""
        # Implementation details...
        return text
        
    def _add_coaching_perspective(self, text: str) -> str:
        """Add coaching-specific insights"""
        # Implementation details...
        return text
        
    def _add_tactical_insights(self, text: str) -> str:
        """Add detailed tactical analysis"""
        # Implementation details...
        return text
        
    def _add_statistical_context(self, text: str) -> str:
        """Add statistical context and data-driven insights"""
        # Implementation details...
        return text
        
    def _add_rule_references(self, text: str) -> str:
        """Add references to football rules and regulations"""
        # Implementation details...
        return text
