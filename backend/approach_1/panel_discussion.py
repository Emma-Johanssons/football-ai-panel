"""
Football Panel Discussion Generator

This module implements a dynamic panel discussion system for football match analysis.
It uses AI-powered agents (host, coach, stats expert, and fans) to generate
natural, engaging discussions about football matches.

The discussion evolves naturally based on:
- Match data and statistics
- Agent expertise and roles
- Topic coverage and flow
- Natural turn-taking and interruptions
"""
import asyncio
import os
import json
from agents.host_agent import HostAgent
from agents.coach_agent import CoachAgent
from agents.stats_agent import StatsAgent
from agents.fan_agent import FanAgent
from services.tts_service import TTSService
from services.match_service import MatchService
from services.data_store import DataStore
from pydub import AudioSegment
from ffmpeg_config import FFMPEG_EXECUTABLE
from memory_system import PanelMemory
from typing import List, Dict, Optional, Any, Tuple, Set
from dotenv import load_dotenv
import random
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure FFmpeg paths from environment variables
FFMPEG_PATH = os.getenv('FFMPEG_PATH', '')
FFPROBE_PATH = os.getenv('FFPROBE_PATH', '')

if not FFMPEG_PATH or not FFPROBE_PATH:
    raise ValueError("FFMPEG_PATH and FFPROBE_PATH must be set in .env file")

AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffmpeg = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

def clean_metadata(data: Any) -> Any:
    """Clean metadata by removing complex objects that can't be serialized"""
    if isinstance(data, dict):
        return {k: clean_metadata(v) for k, v in data.items() 
                if not k.startswith('_') and v is not None}
    elif isinstance(data, list):
        return [clean_metadata(item) for item in data]
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif data is None:
        return None
    else:
        return str(data)  # Convert complex objects to string representation

class PanelDiscussion:
    """Class to manage a football match panel discussion"""
    def __init__(self, match_id: str):
        self.match_id = match_id
        
        # Initialize agents with match_id
        self.host = HostAgent(match_id=self.match_id)
        self.coach = CoachAgent(match_id=self.match_id)
        self.stats = StatsAgent(match_id=self.match_id)
        
        # Initialize discussion state
        self.discussion_state = {
            "match_id": match_id,
            "flow": [],
            "topics_covered": set(),
            "current_topic": None,
            "last_speaker": None,
            "conclusion_readiness": 0.0,
            "match_data": None,  # Will be loaded in initialize
            "is_conclusion": False
        }
        
    async def initialize(self):
        """Initialize the panel discussion by loading necessary data"""
        try:
            # Load match data
            data_store = DataStore()
            match_data = data_store.load_match_data(self.match_id)
            
            if not match_data:
                # If data doesn't exist, fetch it
                match_service = MatchService()
                success = await match_service.get_match_data(self.match_id)
                if success:
                    match_data = data_store.load_match_data(self.match_id)
                    
            if not match_data:
                raise ValueError(f"Failed to load match data for match {self.match_id}")
                
            # Update discussion state with match data
            self.discussion_state["match_data"] = match_data
            
            # Initialize agents with match data
            print("🔄 Initializing agents with match data...")
            await self.host._load_match_data()
            await self.coach._load_match_data()
            await self.stats._load_match_data()
            
            # Verify agents loaded data
            if not self.host.match_data or not self.coach.match_data or not self.stats.match_data:
                print("⚠️ Warning: One or more agents failed to load match data")
                return False
                
            print("✅ All agents initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing panel discussion: {e}")
            return False
            
    async def generate_discussion(self) -> List[Dict]:
        """Generate a dynamic panel discussion"""
        try:
            script = []
            
            # Ensure initialization
            if not self.discussion_state.get("match_data"):
                success = await self.initialize()
                if not success:
                    print("❌ Failed to initialize discussion")
                    return None
            
            # Get match info once and use consistently
            match_info = self.discussion_state.get("match_data", {}).get("match_info", {})
            teams = match_info.get("teams", {})
            score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            
            # Store consistent match info in discussion state
            self.discussion_state["consistent_match_info"] = {
                "home_team": home_team,
                "away_team": away_team,
                "score": score,
                "teams": teams
            }
            
            # Start with host introduction
            print("🎙️ Starting discussion with host introduction...")
            try:
                intro_context = {
                    "match_data": {
                        "teams": {
                            "home": home_team,
                            "away": away_team
                        },
                        "score": score
                    },
                    "flow": [],
                    "current_topic": "match_overview"
                }
                
                host_response = await self.host.get_response(intro_context)
                if not host_response:
                    print("❌ Failed to get host introduction")
                    host_response = f"Welcome to our post-match analysis of {home_team} versus {away_team}. A {score['home']}-{score['away']} result that deserves thorough analysis. Let's start with the overall flow of the match. What were your initial observations?"
                    
            except Exception as e:
                print(f"❌ Error generating host introduction: {e}")
                host_response = "Welcome to our post-match analysis. Let's begin with your observations."
                
            script.append({"speaker": "Show Host", "content": host_response})
            self._update_discussion_state("Show Host", host_response)
            
            # Continue discussion until natural conclusion
            print("🔄 Starting main discussion loop...")
            retries = 0
            max_retries = 3
            
            while not await self._is_conclusion_reached():
                try:
                    # Get potential responses from each agent
                    print("📝 Gathering potential responses...")
                    responses = await self._gather_potential_responses()
                    
                    # Handle no responses case
                    if not responses:
                        print("⚠️ No responses gathered, using host fallback...")
                        fallback = self.host._get_fallback_response(self.discussion_state) if hasattr(self.host, '_get_fallback_response') else "Let's continue our analysis."
                        script.append({"speaker": "Show Host", "content": fallback})
                        self._update_discussion_state("Show Host", fallback)
                        retries += 1
                        if retries >= max_retries:
                            print("❌ Failed to get responses after max retries")
                            break  # Exit loop but return what we have
                        continue
                        
                    print(f"Got responses from: {list(responses.keys())}")
                    
                    # Select most relevant/natural response
                    next_speaker, response = self._select_best_response(responses)
                    print(f"Selected speaker: {next_speaker}")
                    
                    # Handle invalid response case
                    if not response or not isinstance(response, str):
                        print("⚠️ Invalid response selected, using fallback...")
                        fallback = self.host._get_fallback_response(self.discussion_state) if hasattr(self.host, '_get_fallback_response') else "Let's explore that further."
                        script.append({"speaker": "Show Host", "content": fallback})
                        self._update_discussion_state("Show Host", fallback)
                        retries += 1
                        if retries >= max_retries:
                            print("❌ Failed to get valid response after max retries")
                            break  # Exit loop but return what we have
                        continue
                        
                    print(f"✅ Adding response from {next_speaker}")
                    script.append({"speaker": next_speaker, "content": response})
                    self._update_discussion_state(next_speaker, response)
                    retries = 0  # Reset retries on successful response
                    
                    # Check for interruptions
                    if response:  # Only check for interruptions on valid responses
                        interruption = await self._check_for_interruption(next_speaker, response)
                        if interruption and interruption.get("content"):
                            print(f"🗣️ Interruption from {interruption['speaker']}")
                            script.append(interruption)
                            self._update_discussion_state(interruption["speaker"], interruption["content"])
                        
                except Exception as e:
                    print(f"⚠️ Error in discussion loop: {e}")
                    retries += 1
                    if retries >= max_retries:
                        print("❌ Failed to continue discussion after max retries")
                        break  # Exit loop but return what we have
                    continue
                    
            print("🎬 Discussion complete, generating conclusion...")
            # Add conclusion
            try:
                # Set conclusion flag in discussion state
                self.discussion_state["is_conclusion"] = True
                self.discussion_state["current_topic"] = "conclusion"
                
                # Get consistent match info
                match_info = self.discussion_state["consistent_match_info"]
                
                # Generate conclusion with consistent match info
                conclusion = f"Thank you all for these fascinating insights. We've covered this match from every angle - the tactical battle, the statistical story, and the key moments that shaped the game. It's been a pleasure analyzing this {match_info['score']['home']}-{match_info['score']['away']} match between {match_info['home_team']} and {match_info['away_team']}. Thank you for joining us for this discussion!"
                
                script.append({"speaker": "Show Host", "content": conclusion})
                
            except Exception as e:
                print(f"⚠️ Error generating conclusion: {e}")
                script.append({
                    "speaker": "Show Host", 
                    "content": "Thank you all for your contributions to this analysis."
                })
            
            return script if script else None
            
        except Exception as e:
            print(f"❌ Error generating discussion: {e}")
            return None
            
    async def _gather_potential_responses(self) -> Dict[str, str]:
        """Gather potential responses from each agent based on context"""
        responses = {}
        
        # Get responses from each agent if they should speak
        for agent, role in [
            (self.host, "Show Host"),
            (self.coach, "Tactical Analyst"),
            (self.stats, "Stats Expert")
        ]:
            try:
                if agent and hasattr(agent, 'should_speak'):
                    should_speak = agent.should_speak(self.discussion_state)
                    print(f"🤔 {role} should speak: {should_speak}")
                    
                    if should_speak:
                        response = await agent.get_response(self.discussion_state)
                        # Only add valid responses
                        if response and isinstance(response, str):
                            print(f"✅ Got response from {role}")
                            responses[role] = response.strip()  # Ensure clean string
                        else:
                            print(f"⚠️ Invalid response from {role}: {response}")
                else:
                    print(f"⚠️ Agent {role} missing should_speak method")
            except Exception as e:
                print(f"⚠️ Error getting response from {role}: {e}")
                continue
                    
        return responses
        
    def _select_best_response(self, responses: Dict[str, str]) -> Tuple[str, str]:
        """Select the most natural/relevant response"""
        if not responses:
            return "Show Host", self.host._get_fallback_response(self.discussion_state) if hasattr(self.host, '_get_fallback_response') else None
            
        # Get context
        last_speaker = self.discussion_state.get("last_speaker")
        current_topic = self.discussion_state.get("current_topic", "").lower() if self.discussion_state.get("current_topic") else ""
        flow = self.discussion_state.get("flow", [])
        
        # Count recent responses for each role
        recent_responses = {}
        for entry in flow[-5:]:  # Look at last 5 exchanges
            speaker = entry.get("speaker", "")
            recent_responses[speaker] = recent_responses.get(speaker, 0) + 1
        
        # Strongly prioritize experts who haven't spoken much
        expert_responses = {k: v for k, v in responses.items() if k in ["Tactical Analyst", "Stats Expert"]}
        if expert_responses:
            # Find expert who has spoken least
            expert_counts = {role: recent_responses.get(role, 0) for role in expert_responses.keys()}
            least_active_expert = min(expert_counts.items(), key=lambda x: x[1])[0]
            if least_active_expert in responses:
                return least_active_expert, responses[least_active_expert]
        
        # If host has spoken recently (in last 3 exchanges), avoid selecting them
        if recent_responses.get("Show Host", 0) >= 1 and len(responses) > 1:
            non_host_responses = {k: v for k, v in responses.items() if k != "Show Host"}
            if non_host_responses:
                speaker = random.choice(list(non_host_responses.keys()))
                return speaker, non_host_responses[speaker]
        
        # If only one response available, use it
        if len(responses) == 1:
            speaker, response = list(responses.items())[0]
            return speaker, response
        
        # Default to random selection, but with lower weight for host
        speakers = list(responses.keys())
        weights = [0.2 if s == "Show Host" else 1.0 for s in speakers]
        speaker = random.choices(speakers, weights=weights, k=1)[0]
        return speaker, responses[speaker]
        
    async def _check_for_interruption(self, speaker: str, content: str) -> Optional[Dict]:
        """Check if any agent should interrupt"""
        if not content:  # Add null check
            return None
            
        # Don't interrupt the host
        if speaker == "Show Host":
            return None
            
        # Check if other experts should interrupt
        for agent, role in [
            (self.coach, "Tactical Analyst"),
            (self.stats, "Stats Expert")
        ]:
            if role != speaker and agent.should_interrupt(speaker, content):
                interruption = agent.get_interruption(content)
                if interruption:
                    return {"speaker": role, "content": interruption}
                    
        return None
        
    async def _is_conclusion_reached(self) -> bool:
        """Check if discussion has reached a natural conclusion"""
        try:
            # Get current discussion state
            flow = self.discussion_state.get("flow", [])
            current_length = len(flow)
            
            # Too early to conclude if less than minimum exchanges
            min_exchanges = 6
            if current_length < min_exchanges:
                print(f"📝 Discussion too short ({current_length}/{min_exchanges} exchanges)")
                return False
                
            # Check expert participation
            expert_counts = {
                "Tactical Analyst": 0,
                "Stats Expert": 0
            }
            for entry in flow:
                if entry.get("speaker") in expert_counts:
                    expert_counts[entry["speaker"]] += 1
            
            # Ensure each expert has spoken at least twice
            min_expert_contributions = 2
            for expert, count in expert_counts.items():
                if count < min_expert_contributions:
                    print(f"📝 Expert {expert} has only spoken {count}/{min_expert_contributions} times")
                    return False
            
            # Check topic coverage
            topics_covered = self.discussion_state.get("topics_covered", set())
            required_topics = {"tactics", "statistics", "key_moments", "player_performance"}
            missing_topics = required_topics - topics_covered
            
            if missing_topics:
                print(f"📝 Missing topics: {missing_topics}")
                return False
            
            # Check if explicitly moving to conclusion
            recent_entries = flow[-3:]
            for entry in recent_entries:
                if entry and entry.get("content"):
                    content = entry["content"]
                    if self._is_conclusion_question(content):
                        print("📝 Conclusion question detected")
                        return True
            
            # Check if maximum length reached
            max_exchanges = 20
            if current_length >= max_exchanges:
                print(f"📝 Maximum discussion length reached ({max_exchanges} exchanges)")
                return True
            
            # Check conclusion readiness
            if self.discussion_state.get("conclusion_readiness", 0) >= 0.8:
                # Double check expert participation before concluding
                if all(count >= min_expert_contributions for count in expert_counts.values()):
                    print("📝 Discussion naturally ready for conclusion")
                    return True
                else:
                    print("📝 Need more expert participation before concluding")
                    return False
            
            print("📝 Discussion continuing - more topics to cover")
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking conclusion status: {e}")
            return False
        
    def _is_conclusion_question(self, content: str) -> bool:
        """Check if content is asking for conclusion"""
        if not content or not isinstance(content, str):
            return False
            
        content_lower = content.lower()
        
        conclusion_indicators = [
            "final thoughts",
            "to conclude",
            "in conclusion",
            "summing up",
            "overall",
            "who deserved to win",
            "fair result",
            "right team won"
        ]
        return any(indicator in content_lower for indicator in conclusion_indicators)
        
    def _update_discussion_state(self, speaker: str, content: str):
        """Update discussion state with new content"""
        if not speaker or not content or not isinstance(content, str):
            print(f"⚠️ Warning: Invalid speaker or content received: speaker={speaker}, content={type(content)}")
            return
            
        # Update last speaker and flow
        self.discussion_state["last_speaker"] = speaker
        self.discussion_state["flow"].append({
            "speaker": speaker, 
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract and update topics
        new_topics = self._extract_topics(content)
        if new_topics:  # Only update if we found topics
            print(f"📌 Adding new topics: {new_topics}")
            self.discussion_state["topics_covered"].update(new_topics)
            
            # Update current topic based on most recent content
            # This helps drive the conversation forward
            if "tactics" in new_topics:
                self.discussion_state["current_topic"] = "tactical_analysis"
            elif "statistics" in new_topics:
                self.discussion_state["current_topic"] = "statistical_analysis"
            elif "player_performance" in new_topics:
                self.discussion_state["current_topic"] = "player_performance"
            elif "key_moments" in new_topics:
                self.discussion_state["current_topic"] = "key_moments"
                
        # Track speaking turns for each role
        if speaker not in self.discussion_state.get("speaker_turns", {}):
            self.discussion_state["speaker_turns"] = self.discussion_state.get("speaker_turns", {})
            self.discussion_state["speaker_turns"][speaker] = 0
        self.discussion_state["speaker_turns"][speaker] += 1
        
        # Update discussion progress
        self._update_conclusion_readiness()
        
        # Print debug info
        print(f"\n🔄 Discussion State Update:")
        print(f"Speaker: {speaker}")
        print(f"Topics Covered: {self.discussion_state.get('topics_covered', set())}")
        print(f"Current Topic: {self.discussion_state.get('current_topic')}")
        print(f"Speaker Turns: {self.discussion_state.get('speaker_turns', {})}")
        print(f"Conclusion Readiness: {self.discussion_state.get('conclusion_readiness', 0):.2f}\n")
        
    def _extract_topics(self, content: str) -> Set[str]:
        """Extract topics from content"""
        if not content:
            return set()
            
        content_lower = content.lower()
        topics = set()
        
        # Define topic categories and their keywords
        topic_keywords = {
            "tactics": [
                "formation", "tactic", "strategy", "press", "possession",
                "counter", "attack", "defend", "position", "system",
                "play", "style", "approach", "setup", "structure",
                "shape", "organization", "transition", "press"
            ],
            "statistics": [
                "stat", "number", "data", "performance", "record",
                "average", "percentage", "comparison", "metric", "figure",
                "accuracy", "success", "rate", "total", "count",
                "possession", "shots", "passes", "tackles"
            ],
            "key_moments": [
                "goal", "chance", "save", "turning point", "opportunity",
                "incident", "moment", "highlight", "key play", "crucial",
                "decisive", "important", "critical", "vital", "significant",
                "game-changing", "momentum"
            ],
            "player_performance": [
                "player", "individual", "performance", "contribution",
                "impact", "influence", "role", "effort", "work rate",
                "involvement", "quality", "skill", "technique", "ability",
                "talent", "display", "showing"
            ]
        }
        
        # Extract topics based on keyword matches
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.add(topic)
                print(f"📌 Detected topic: {topic}")
                
        return topics
        
    def _update_conclusion_readiness(self):
        """Update progress towards conclusion"""
        topics_covered = self.discussion_state.get("topics_covered", set())
        if not topics_covered:  # Add null check
            self.discussion_state["conclusion_readiness"] = 0.0
            return
            
        required_topics = {"tactics", "statistics", "key_moments", "player_performance"}
        
        # Calculate readiness based on topic coverage
        coverage = len(topics_covered & required_topics) / len(required_topics)
        
        # Consider discussion length
        flow = self.discussion_state.get("flow", [])
        length_factor = min(1.0, len(flow) / 15) if flow else 0.0
        
        # Consider expert participation
        expert_counts = {}
        for entry in flow:
            if entry and entry.get("speaker") in ["Tactical Analyst", "Stats Expert"]:
                expert_counts[entry["speaker"]] = expert_counts.get(entry["speaker"], 0) + 1
                
        participation = 1.0 if len(expert_counts) == 2 and min(expert_counts.values()) >= 2 else 0.5
        
        # Update readiness
        self.discussion_state["conclusion_readiness"] = (coverage + length_factor + participation) / 3

    def format_script(self, script: List[Dict]) -> str:
        """Format the discussion script for display"""
        if not script:
            return "No script generated."
            
        formatted_lines = []
        for entry in script:
            speaker = entry["speaker"]
            content = entry["content"]
            
            # Format speaker name with padding
            speaker_line = f"\n{speaker}:"
            formatted_lines.append(speaker_line)
            
            # Format content with wrapping
            content_lines = self._wrap_text(content, width=80)
            formatted_lines.extend(["  " + line for line in content_lines])
            
        return "\n".join(formatted_lines)
        
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= width:
                current_line.append(word)
                current_length += word_length + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
                
        if current_line:
            lines.append(" ".join(current_line))
            
        return lines

async def main():
    match_id = "1374812"
    print("\n📝 Generating panel discussion script...")
    print(f"Starting panel discussion for match {match_id}")
    
    try:
        # Create and initialize panel discussion
        panel = PanelDiscussion(match_id)
        
        # Generate discussion
        script = await panel.generate_discussion()
        
        if script:
            # Format and display script
            formatted_script = panel.format_script(script)
            
            # Save script to file
            script_dir = "generated_scripts"
            os.makedirs(script_dir, exist_ok=True)
            script_path = os.path.join(script_dir, f"match_{match_id}_discussion.txt")
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(formatted_script)
            print(f"\n✅ Full script saved to: {script_path}")
            
            # Show preview
            print("\nScript preview:")
            print("==================================================")
            print(formatted_script[:500] + "...\n")
            
            # Ask about audio generation
            print("\nWould you like to generate the audio for this script? (y/n)")
            choice = input().lower()
            if choice == 'y':
                await panel.generate_audio(script)
                
    except Exception as e:
        print(f"❌ Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 