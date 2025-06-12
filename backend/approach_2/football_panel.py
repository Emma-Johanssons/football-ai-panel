"""
Enhanced football panel discussion system with personas and topic tracking
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, List, Optional, Tuple
import json
import os
from dotenv import load_dotenv
from prompts.system_prompts import (
    HOST_PROMPT,
    TACTICAL_PROMPT,
    STATS_PROMPT,
    MEMORY_PROMPT
)
from services.match_service import MatchService
from services.tts_service import TTSService
from services.data_store import DataStore
from services.stats_service import StatsService
from datetime import datetime

load_dotenv()

# Personality mapping for agents
PERSONALITY_MAPPING = {
    "Show Host": "alex_stewart",  # Host personality
    "Tactical Analyst": "coach_matt",  # Coach personality
    "Stats Expert": "joe_devine"  # Stats personality
}

# Timing guidelines (in seconds) for a 10-minute (600 second) discussion
TIMING_GUIDELINES = {
    "introduction": 60,      # 1 minute for intro
    "first_half": 120,       # 2 minutes for first half analysis
    "second_half": 120,      # 2 minutes for second half analysis
    "key_moments": 90,       # 1.5 minutes for key moments
    "player_performances": 120,  # 2 minutes for player analysis
    "historical_context": 60,    # 1 minute for historical context
    "conclusion": 30,        # 30 seconds for conclusion
}

# Approximate words per minute for natural speech
WORDS_PER_MINUTE = 150

class FootballPanel:
    def __init__(self, match_id: str):
        """Initialize the football panel with agents and personalities"""
        try:
            # Store match ID
            self.match_id = match_id
            
            # Initialize agents
            self.host = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=500
            )
            
            self.coach = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=500
            )
            
            self.stats = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=500
            )
            
            # Load personalities
            self.personalities = self._load_personalities()
        
            # Assign personalities to agents
            self.coach_personality = self.personalities.get("coach_matt", {})
            self.stats_personality = self.personalities.get("alex_stewart", {})
            
            # Initialize discussion history
            self.discussion_history = []
            self.topics_discussed = set()
            self.stats_mentioned = set()
            self.tactics_mentioned = set()
            self.players_discussed = set()
            self.events_discussed = set()
                                
                            # Initialize match data cache
            self.current_match_data = None
            
            # Initialize services
            self.match_service = MatchService()
            self.stats_service = StatsService()
            self.tts_service = TTSService()
            self.data_store = DataStore()
                    
            print("✅ Football panel initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing football panel: {e}")
            raise
        
    def _load_personalities(self) -> Dict:
        """Load personality data from JSON files"""
        try:
            personalities = {}
            personality_dir = os.path.join(os.path.dirname(__file__), "learning_data", "personalities")
        
            for filename in os.listdir(personality_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(personality_dir, filename), "r") as f:
                        personality_data = json.load(f)
                        name = personality_data.get("name", "").lower().replace(" ", "_")
                        personalities[name] = personality_data
            
            print(f"✅ Loaded {len(personalities)} personalities")
            return personalities

        except Exception as e:
            print(f"❌ Error loading personalities: {e}")
            raise

    async def generate_response(self, agent_type: str, context: Dict) -> str:
        """Generate a response from an agent based on the context"""
        try:
            # Validate agent type
            valid_agents = ["Show Host", "Tactical Analyst", "Stats Expert"]
            if agent_type not in valid_agents:
                print(f"❌ Invalid agent type: {agent_type}")
                return None

            # Get the appropriate agent and base prompt
            if agent_type == "Show Host":
                agent = self.host
                base_prompt = HOST_PROMPT
                personality = {}  # Host doesn't need a personality
            elif agent_type == "Tactical Analyst":
                agent = self.coach
                base_prompt = TACTICAL_PROMPT
                personality = self.coach_personality
            elif agent_type == "Stats Expert":
                agent = self.stats
                base_prompt = STATS_PROMPT
                personality = self.stats_personality

            # Get match data from cache
            match_data = self._get_match_data()
            if not match_data:
                print("❌ No match data available for response generation")
                return None

            # Handle introduction and conclusion specially for Show Host
            current_topic = context.get("current_topic", "")
            if agent_type == "Show Host" and current_topic in ["introduction", "closing"]:
                return context.get("content", "")

            # Get relevant discussion history
            relevant_history = self._get_relevant_history(agent_type)
            formatted_history = [f"{speaker}: {content}" for speaker, content in relevant_history]
            
            # Get fresh talking points
            fresh_points = self._get_fresh_talking_points(agent_type)
            
            # Get personality traits
            traits = personality.get("traits", {}) if personality else {}
            
            # Get actual players from match data
            actual_players = set()
            lineups = match_data.get("lineups", {})
            if isinstance(lineups, dict):
                for team in ["home", "away"]:
                    team_lineup = lineups.get(team, [])
                    for player in team_lineup:
                        if isinstance(player, dict) and "name" in player:
                            actual_players.add(player["name"].lower())
            
            # Prepare focused context with memory and fresh points
            focused_context = {
                "current_topic": context.get("current_topic", ""),
                "content": context.get("content", ""),
                "match_info": {
                    "teams": match_data.get("teams", {}),
                    "score": match_data.get("score", {}),
                    "goals": match_data.get("goals", []),
                    "fixture": match_data.get("fixture", {}),
                    "actual_players": list(actual_players)
                },
                "discussion_history": "\n".join(formatted_history),
                "fresh_points": fresh_points,
                "topics_discussed": list(self.topics_discussed),
                "personality": {
                    "name": personality.get("name", ""),
                    "channel": personality.get("channel", ""),
                    "role": personality.get("role", ""),
                    "traits": traits,
                    "emotion_level": traits.get("emotion_level", 0.5),
                    "detail_focus": traits.get("detail_focus", 0.5),
                    "topic_expertise": traits.get("topic_expertise", 0.5)
                }
            }

            # Generate response using the agent with focused context
            messages = [
                SystemMessage(content=base_prompt),
                SystemMessage(content=MEMORY_PROMPT.format(discussion_history="\n".join(formatted_history))),
                HumanMessage(content=json.dumps(focused_context))
            ]
            
            response = await agent.ainvoke(messages)
            if response and hasattr(response, 'content'):
                content = response.content
                
                # Clean up the response
                content = content.replace(f"{agent_type}:", "").strip()
                
                # Remove any JSON-like content
                content = content.split('{')[0].strip() if '{' in content else content
                
                # Remove common repetitive phrases
                content = content.replace("Absolutely, let's", "").replace("Let's", "").strip()
                
                # Remove other common phrases to avoid
                for phrase in ["Now, ", "Well, ", "I think ", "I can see "]:
                    content = content.replace(phrase, "")
                
                # Remove questions from expert responses
                if agent_type in ["Tactical Analyst", "Stats Expert"]:
                    content = content.split("?")[0] + "." if "?" in content else content
                
                # Remove references to non-existent players
                for player in ["mbappe", "neymar", "di maria", "draxler", "herrera", "gueye", "bernat"]:
                    if player not in actual_players:
                        content = content.replace(player, "[player]")
                
                # Ensure proper speaker labeling
                if agent_type == "Show Host" and "Tactical Analyst:" in content:
                    content = content.replace("Tactical Analyst:", "").strip()
                if agent_type == "Show Host" and "Stats Expert:" in content:
                    content = content.replace("Stats Expert:", "").strip()
                
                # Add personality-based reactions
                if agent_type in ["Tactical Analyst", "Stats Expert"]:
                    emotion_level = traits.get("emotion_level", 0.5)
                    detail_focus = traits.get("detail_focus", 0.5)
                    
                    # Adjust emotional level
                    if emotion_level > 0.7:
                        content = content.replace(".", "!").replace("?", "!")
                    elif emotion_level < 0.3:
                        content = content.replace("!", ".").replace("?", ".")
                    
                    # Adjust detail level
                    if detail_focus < 0.3:
                        # Make response more concise
                        sentences = content.split(". ")
                        content = ". ".join(sentences[:2]) + "."
                    elif detail_focus > 0.7:
                        # Add more tactical/statistical detail
                        if agent_type == "Tactical Analyst":
                            content += " The tactical setup really allowed them to exploit these spaces effectively."
                        else:
                            content += " The numbers really back this up with some impressive statistics."
                
                self.discussion_history.append((agent_type, content))
                return content
            
            return None

        except Exception as e:
            print(f"❌ Error generating response for {agent_type}: {e}")
            return None

    def _get_match_data(self) -> Optional[Dict]:
        """Get match data from cache or load if necessary"""
        if not self.current_match_data:
            print("❌ No match data available")
            return None
        return self.current_match_data

    async def initialize(self) -> bool:
        """Initialize the panel discussion with fresh match data"""
        try:
            if self.current_match_data:
                print("✅ Using cached match data")
                return True
                
            # First try to load from data store
            match_data = self.data_store.load_match_data(self.match_id)
            
            if not match_data:
                # If data doesn't exist, fetch it using match service
                match_data = await self.match_service.get_match_data(self.match_id)
                if match_data:
                    self.data_store.save_match_data(self.match_id, match_data)
                    print("✅ Successfully fetched and saved match data")
                    
            if not match_data:
                print("❌ Failed to load match data")
                return False
                
            # Get additional match details if not present
            if not match_data.get("match_info"):
                match_details = await self.match_service.get_match_info(self.match_id)
                if match_details:
                    match_data.update(match_details)
                    print("✅ Successfully added match details")
                
            # Get detailed statistics if not present
            if not match_data.get("detailed_statistics"):
                stats_data = await self.stats_service.get_match_stats(self.match_id)
                if stats_data:
                    match_data["detailed_statistics"] = stats_data
                    print("✅ Successfully added detailed statistics")
                
            # Reset discussion tracking
            self.discussion_history.clear()
            
            # Store match data for later use
            self.current_match_data = match_data
            
            print("✅ Successfully initialized with match data")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing panel discussion: {e}")
            return False
            
    def _generate_discussion_points(self, match_data: Dict) -> List[Dict]:
        """Generate discussion points based on match data"""
        try:
            # Extract key match information
            teams = match_data.get("match_info", {}).get("teams", {})
            score = match_data.get("match_info", {}).get("score", {})
            goals = match_data.get("match_info", {}).get("goals", {})
            fixture = match_data.get("match_info", {}).get("fixture", {})
            league = match_data.get("match_info", {}).get("league", {})
            
            # Extract actual players from lineups
            actual_players = set()
            lineups = match_data.get("lineups", [])
            for team in lineups:
                for player in team.get("startXI", []):
                    if "player" in player and "name" in player["player"]:
                        actual_players.add(player["player"]["name"].lower())
            
            # Generate discussion points with expert responses
            discussion_points = [
                {
                    "topic": "introduction",
                    "content": f"Good evening and welcome to our post-match analysis of this {league.get('name', 'match')} between {teams.get('home', {}).get('name', 'Home Team')} and {teams.get('away', {}).get('name', 'Away Team')}. What a performance we witnessed tonight – {teams.get('home', {}).get('name', 'Home Team')} absolutely dominant in a {goals.get('home', 0)}–{goals.get('away', 0)} win that will be talked about for a long time. I'm joined by our tactical analyst George and statistics expert Callum to break it all down. Callum, what do the early numbers tell us about how this match unfolded?",
                    "responses": {
                        "Stats Expert": "The first 15 minutes were absolutely crucial. [Statistical analysis of opening period]",
                        "Tactical Analyst": "The tactical setup was fascinating. [Tactical analysis of first half]"
                    }
                },
                {
                    "topic": "first_half",
                    "content": "George, can you break down the tactical setup that allowed them to take a commanding lead? And Callum, from a statistical standpoint, what stood out to you about their performance in the first 45 minutes?",
                    "responses": {
                        "Tactical Analyst": "Looking at the tactical approach, [Detailed tactical analysis]",
                        "Stats Expert": "The statistics show [Detailed statistical analysis]"
                    }
                },
                {
                    "topic": "second_half",
                    "content": "Moving to the second half, George, how did they extend their lead? And Callum, what do the numbers tell us about their continued dominance after the break?",
                    "responses": {
                        "Tactical Analyst": "The second half adjustments were key. [Tactical analysis of second half]",
                        "Stats Expert": "The second half stats reveal [Statistical analysis of second half]"
                    }
                },
                {
                    "topic": "key_moments",
                    "content": "Was there a particular moment that changed the game? George, from a tactical perspective, what was the turning point? And Callum, do the numbers support that?",
                    "responses": {
                        "Tactical Analyst": "The key moment was [Tactical analysis of turning point]",
                        "Stats Expert": "Looking at the data, [Statistical analysis of turning point]"
                    }
                },
                {
                    "topic": "player_performances",
                    "content": "Let's talk about individual performances. George, who stood out tactically? And Callum, what do the numbers tell us about these players?",
                    "responses": {
                        "Tactical Analyst": "Several players really impressed. [Player tactical analysis]",
                        "Stats Expert": "The player statistics show [Player statistical analysis]"
                    }
                },
                {
                    "topic": "historical_context",
                    "content": "Looking at the bigger picture, George, what does this performance tell us about their current status? And Callum, how does this compare to their previous matches?",
                    "responses": {
                        "Tactical Analyst": "This performance demonstrates [Historical tactical analysis]",
                        "Stats Expert": "Comparing to previous matches, [Historical statistical analysis]"
                    }
                },
                {
                    "topic": "conclusion",
                    "content": "As we wrap up, George, what are the key takeaways from this match? And Callum, what do the overall statistics tell us about their strength?",
                    "responses": {
                        "Tactical Analyst": "The key takeaways are [Final tactical analysis]",
                        "Stats Expert": "The overall statistics suggest [Final statistical analysis]"
                    }
                },
                {
                    "topic": "closing",
                    "content": f"That wraps up our analysis of this remarkable {league.get('name', 'match')}: {teams.get('home', {}).get('name', 'Home Team')} {goals.get('home', 0)}, {teams.get('away', {}).get('name', 'Away Team')} {goals.get('away', 0)}. From the early dominance to those late goals, it was a complete performance from start to finish. Thank you to our experts for their insights, and thank you all for joining us. Until next time – good evening."
                }
            ]
            
            return discussion_points
            
        except Exception as e:
            print(f"❌ Error generating discussion points: {e}")
            return None
            
    async def generate_script(self) -> List[Dict]:
        """Generate the complete discussion script"""
        try:
            # Get discussion points
            discussion_points = self._generate_discussion_points(self.current_match_data)
            if not discussion_points:
                print("❌ No discussion points generated")
                return None

            # Generate script with expert responses
            script = []
            for point in discussion_points:
                # Add host's introduction
                script.append({
                    "speaker": "Show Host",
                    "content": point["content"],
                    "segment": point["topic"],
                    "timing": f"{TIMING_GUIDELINES.get(point['topic'], 60)/60:.1f} minutes"
                })

                # Add expert responses if they exist
                if "responses" in point:
                    for expert, response in point["responses"].items():
                        # Generate response using the appropriate agent
                        expert_response = await self.generate_response(
                            expert,
                            {
                                "current_topic": point["topic"],
                                "content": response
                            }
                        )
                        if expert_response:
                            script.append({
                                "speaker": expert,
                                "content": expert_response,
                                "segment": point["topic"],
                                "timing": f"{TIMING_GUIDELINES.get(point['topic'], 60)/60:.1f} minutes"
                            })
                    
            return script
            
        except Exception as e:
            print(f"❌ Error generating script: {e}")
            return None
            
    async def generate_audio(self, script: List[Dict]):
        """Generate audio for the discussion using TTS service"""
        try:
            audio_files = []
            for entry in script:
                speaker = entry["speaker"]
                content = entry["content"]
                
                # Use TTS service to generate audio
                audio_file = await self.tts_service.generate_speech(
                    text=content,
                    speaker=speaker
                )
                
                if audio_file:
                    audio_files.append(audio_file)
                    
            # Combine audio files if needed
            if audio_files:
                combined_audio = await self.tts_service.combine_audio_files(audio_files)
                if combined_audio:
                    print(f"✅ Audio generated successfully: {combined_audio}")
                    return combined_audio
                    
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None

    def _get_relevant_history(self, agent_type: str) -> List[Tuple[str, str]]:
        """Get relevant discussion history based on agent type and current topic"""
        if not self.discussion_history:
            return []

        # Get the last 5 exchanges for better context
        recent_history = self.discussion_history[-5:]
        
        # Filter based on agent type and topic relevance
        relevant_history = []
        current_topic = self.discussion_history[-1][1] if self.discussion_history else ""
        
        for speaker, content in recent_history:
            # Always include the last exchange
            if len(relevant_history) == 0:
                relevant_history.append((speaker, content))
                continue
                
            # Include exchanges from other agents
            if speaker != agent_type:
                relevant_history.append((speaker, content))
                continue
                
            # For same agent, only include if it's a different topic
            if not self._is_same_topic(content, current_topic):
                relevant_history.append((speaker, content))
                
        return relevant_history

    def _is_same_topic(self, content1: str, content2: str) -> bool:
        """Check if two pieces of content are about the same topic"""
        # Extract key words from content
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        # Check for common key words
        common_words = words1.intersection(words2)
        
        # If there are enough common words, consider it the same topic
        return len(common_words) > 3

    def _get_fresh_talking_points(self, agent_type: str) -> Dict:
        """Get topics that haven't been discussed yet"""
        if not self.current_match_data:
            return {}
            
        # Extract players from lineups and events
        all_players = set()
        
        # Handle lineups which might be a list or dict
        lineups = self.current_match_data.get("lineups", [])
        if isinstance(lineups, dict):
            # If it's a dict with home/away keys
            for team in ["home", "away"]:
                team_lineup = lineups.get(team, [])
                for player in team_lineup:
                    if isinstance(player, dict) and "name" in player:
                        all_players.add(player["name"].lower())
        elif isinstance(lineups, list):
            # If it's a list of players
            for player in lineups:
                if isinstance(player, dict) and "name" in player:
                    all_players.add(player["name"].lower())
                    
        # Handle events
        events = self.current_match_data.get("events", [])
        fresh_events = []
        for event in events:
            if isinstance(event, dict):
                # Add player from event to all_players
                player_name = (event.get("player", {}) or {}).get("name")
                if player_name:
                    all_players.add(player_name.lower())
                    
                # Track fresh events
                event_type = event.get("type", "").lower()
                event_key = f"{event_type}_{player_name}".lower() if player_name else event_type
                if event_key not in self.events_discussed:
                    fresh_events.append(event)
                    
        if agent_type == "Stats Expert":
            return {
                "stats": [stat for stat, mentioned in self.stats_mentioned.items() 
                         if not mentioned],
                "players": sorted(list(all_players - self.players_discussed))
            }
        elif agent_type == "Tactical Analyst":
            return {
                "tactics": [tactic for tactic, mentioned in self.tactics_mentioned.items()
                          if not mentioned],
                "players": sorted(list(all_players - self.players_discussed)),
                "events": fresh_events
            }
        return {}

async def main():
    """Main entry point for the panel discussion generator"""
    import sys
    import os
    
    # Get match ID from command line argument
    if len(sys.argv) < 2:
        print("❌ Please provide a match ID")
        print("Usage: python enhanced_panel.py <match_id>")
        print("Example: python enhanced_panel.py 1374812")
        return
        
    match_id = sys.argv[1]
    print(f"\n🎙️ Generating panel discussion for match {match_id}")
    
    try:
        # Create panel discussion instance
        panel = FootballPanel(match_id)
        
        # Initialize and load match data
        print("\n📊 Loading match data...")
        if not await panel.initialize():
            print("❌ Failed to initialize panel discussion")
            return
            
        # Generate discussion script
        print("\n📝 Generating discussion script...")
        script = await panel.generate_script()
        
        if not script:
            print("❌ Failed to generate discussion script")
            return
            
        # Format and save script
        formatted_script = format_script(script)
        
        # Ensure directory exists
        script_dir = os.path.join(os.path.dirname(__file__), "generated_scripts")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"match_{match_id}_discussion.txt")
        
        # Save script (explicitly overwrite)
        try:
            # Remove existing file if it exists
            if os.path.exists(script_path):
                os.remove(script_path)
                
            # Write new script
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(formatted_script)
            print(f"\n✅ Script saved to: {script_path}")
            
            # Show preview
            print("\nScript preview:")
            print("=" * 50)
            preview_length = min(500, len(formatted_script))
            print(formatted_script[:preview_length] + "...\n")
            
        except Exception as e:
            print(f"❌ Error saving script: {e}")
            return
        
        # Ask about audio generation
        while True:
            print("\nWould you like to generate audio for this discussion? (y/n)")
            choice = input().lower().strip()
            
            if choice in ['y', 'n']:
                break
            print("Please enter 'y' for yes or 'n' for no.")
        
        if choice == 'y':
            print("\n🔊 Generating audio...")
            audio_file = await panel.generate_audio(script)
            if audio_file:
                print(f"✅ Audio saved to: {audio_file}")
            else:
                print("❌ Failed to generate audio")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print("\nDetailed error information:")
        print(traceback.format_exc())

def format_script(script: List[Dict]) -> str:
    """Format the script for display with timing information"""
    if not script:
        return "No script generated."
        
    formatted = []
    current_segment = None
    
    for entry in script:
        # Add segment header if it's a new segment
        if entry["segment"] != current_segment:
            current_segment = entry["segment"]
            formatted.extend([
                f"\n=== {current_segment.replace('_', ' ').title()} ===",
                f"(Approximate timing: {entry['timing']})\n"
            ])
        
        # Add the exchange
        formatted.extend([
            f"\n{entry['speaker']}:",
            f"  {entry['content']}\n"
        ])
        
    return "\n".join(formatted)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 