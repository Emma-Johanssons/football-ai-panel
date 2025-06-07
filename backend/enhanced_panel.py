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
    STATS_PROMPT
)
from services.match_service import MatchService
from services.tts_service import TTSService
from services.data_store import DataStore
from services.stats_service import StatsService
from datetime import datetime

load_dotenv()

# Timing guidelines (in seconds) for a 5-minute (300 second) discussion
TIMING_GUIDELINES = {
    "introduction": 30,  # 30 seconds for intro
    "tactical_analysis": 75,  # 1 minute 15 seconds for tactics
    "statistical_analysis": 75,  # 1 minute 15 seconds for stats
    "key_moments": 60,  # 1 minute for key moments
    "conclusion": 60,  # 1 minute for conclusion
}

# Approximate words per minute for natural speech
WORDS_PER_MINUTE = 150

class EnhancedPanelDiscussion:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7
        )
        
        # Initialize services
        self.match_service = MatchService()
        self.stats_service = StatsService()
        self.tts_service = TTSService()
        self.data_store = DataStore()
        
        # Initialize agents with base LLM
        self.host = self.llm
        self.coach = self.llm
        self.stats = self.llm
        
        # Store prompts for each agent
        self.prompts = {
            "Show Host": HOST_PROMPT,
            "Tactical Analyst": TACTICAL_PROMPT,
            "Stats Expert": STATS_PROMPT
        }
        
        # Initialize discussion tracking
        self.stats_mentioned = {
            "possession": False,
            "shots": False,
            "shots_on_target": False,
            "passes": False,
            "pass_accuracy": False,
            "expected_goals": False,
            "cards": False,
            "fouls": False
        }
        self.tactics_mentioned = {
            "formation_comparison": False,
            "attacking_style": False,
            "defensive_setup": False,
            "pressing": False,
            "substitutions": False,
            "player_roles": False
        }
        self.players_discussed = set()
        self.events_discussed = set()
        self.discussion_history = []
        
        # Initialize match data cache
        self.current_match_data = None
        
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
            self.stats_mentioned = {k: False for k in self.stats_mentioned}
            self.tactics_mentioned = {k: False for k in self.tactics_mentioned}
            self.players_discussed.clear()
            self.events_discussed.clear()
            self.discussion_history.clear()
            
            # Store match data for later use
            self.current_match_data = match_data
            
            print("✅ Successfully initialized with match data")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing panel discussion: {e}")
            return False
            
    def _get_match_data(self) -> Optional[Dict]:
        """Get match data from cache or load if necessary"""
        if not self.current_match_data:
            print("❌ No match data available")
            return None
        return self.current_match_data

    def _generate_discussion_points(self, match_data: Dict) -> List[Tuple[str, str, str]]:
        """Dynamically generate discussion points based on match data"""
        try:
            # Extract key match information
            match_info = match_data.get("match_info", {})
            teams = match_info.get("teams", {})
            score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            home_score = score.get("home", 0)
            away_score = score.get("away", 0)
            
            # Get league information
            league_info = match_info.get("league", {})
            league_name = league_info.get("name", "")
            competition_round = league_info.get("round", "")
            competition_desc = f"{league_name} {competition_round}".strip()
            
            # Get formations and lineups
            formations = match_data.get("details", {}).get("formations", {})
            home_formation = formations.get("home", "their formation")
            away_formation = formations.get("away", "their setup")
            
            # Get events
            events = match_data.get("events", [])
            goals = [e for e in events if e.get("type") == "Goal"]
            cards = [e for e in events if e.get("type") in ["Yellow Card", "Red Card"]]
            subs = [e for e in events if e.get("type") == "Substitution"]
            
            # Get H2H data safely
            h2h = match_data.get("h2h", {})
            total_matches = h2h.get("summary", {}).get("total_matches", "several")
            h2h_context = f"These teams have met {total_matches} times before" if isinstance(total_matches, (int, str)) else "These teams have met before"
            
            # Generate dynamic discussion points
            points = [
                # Introduction
                ("Show Host", "introduction", 
                 f"Good evening and welcome to our post-match analysis of this {competition_desc} clash between {home_team} and {away_team}. "
                 f"The final score: {home_team} {home_score}, {away_team} {away_score}. "
                 f"I'm joined by our tactical analyst and statistics expert to break down what turned out to be "
                 f"{'a dominant display' if abs(home_score - away_score) > 2 else 'an intriguing match'}. "
                 f"Let's dive into how this result unfolded."),
                
                # First Half Analysis
                ("Tactical Analyst", "first_half",
                 f"Let's analyze the first half tactics. {home_team} lined up in a {home_formation}, while {away_team} opted for a {away_formation}. "
                 "How did these formations match up, and what key battles emerged in the opening 45 minutes?"),
                
                # Statistical Overview of First Half
                ("Stats Expert", "first_half_stats",
                 "Looking at the first half numbers, let's break down the key statistics and how they translated to the gameplay we witnessed."),
                
                # Key Turning Points
                ("Show Host", "turning_points",
                 f"We saw {len(goals)} goals today, along with {len(cards)} cards and {len(subs)} substitutions. "
                 "Let's identify the key moments that shaped this match. What were the turning points?"),
                
                # Second Half Tactical Changes
                ("Tactical Analyst", "second_half_tactics",
                 "The second half brought some interesting tactical adjustments. Let's analyze how both teams adapted their approach "
                 "and how these changes influenced the final result."),
                
                # Player Performances
                ("Stats Expert", "player_performances",
                 "Let's look at the individual performances that stood out today. Who were the key players statistically, "
                 "and how did their numbers impact the overall team performance?"),
                
                # Historical Context
                ("Show Host", "historical_context",
                 f"{h2h_context}. How does today's performance compare to their previous encounters?"),
                
                # Final Thoughts
                ("Show Host", "conclusion",
                 f"As we conclude our analysis of this {home_score}-{away_score} match, what are your final thoughts on the key factors "
                 "that determined today's result?"),
                
                # Tactical Summary
                ("Tactical Analyst", "conclusion",
                 "From a tactical perspective, let me summarize the key strategic elements that influenced this match..."),
                
                # Statistical Summary
                ("Stats Expert", "conclusion",
                 "Looking at the final statistics, let me highlight the most telling numbers that explain this result..."),
                
                # Host Closing
                ("Show Host", "closing",
                 f"And that brings us to the end of our analysis of this {'remarkable' if abs(home_score - away_score) > 2 else 'fascinating'} "
                 f"match between {home_team} and {away_team}. The final score: {home_team} {home_score}, {away_team} {away_score}. "
                 f"{'A dominant performance' if abs(home_score - away_score) > 2 else 'A close contest'} that will be remembered "
                 f"for {'its display of attacking football' if home_score + away_score > 3 else 'its tactical battle'}. "
                 "Thank you to our experts for their insights, and thank you for joining us. Good evening.")
            ]
            
            return points
            
        except Exception as e:
            print(f"❌ Error generating discussion points: {e}")
            return []
            
    async def generate_script(self) -> List[Dict]:
        """Generate a complete panel discussion"""
        if not await self.initialize():
            return []
            
        try:
            # Use stored match data for discussion points
            match_data = self._get_match_data()
            if not match_data:
                print("❌ No match data available")
                return []
                
            # Generate dynamic discussion points
            discussion_points = self._generate_discussion_points(match_data)
            
            script = []
            
            for speaker, segment, content in discussion_points:
                try:
                    # Prepare context for response generation
                    context = {
                        "current_topic": segment,
                        "content": content,
                        "match_data": match_data
                    }
                    
                    # Generate response
                    response = await self.generate_response(
                        agent_type=speaker,
                        context=context
                    )
                    
                    if response:
                        entry = {
                            "speaker": speaker,
                            "content": response,
                            "segment": segment,
                            "timing": f"{TIMING_GUIDELINES.get(segment, 60)/60:.1f} minutes"
                        }
                        script.append(entry)
                        
                except Exception as e:
                    print(f"Error generating response for {speaker}: {e}")
                    continue
                    
            return script
            
        except Exception as e:
            print(f"Error generating script: {e}")
            return []
            
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

    async def generate_response(self, agent_type: str, context: Dict) -> str:
        """Generate a response from an agent based on the context"""
        try:
            # Get the appropriate agent and prompt
            if agent_type == "Show Host":
                agent = self.host
            elif agent_type == "Tactical Analyst":
                agent = self.coach
            elif agent_type == "Stats Expert":
                agent = self.stats
            else:
                print(f"❌ Unknown agent type: {agent_type}")
                return None

            # Get the agent's prompt
            prompt = self.prompts.get(agent_type)
            if not prompt:
                print(f"❌ No prompt found for agent type: {agent_type}")
                return None

            # Get match data from cache
            match_data = self._get_match_data()
            if not match_data:
                print("❌ No match data available for response generation")
                return None

            # Handle introduction and conclusion specially for Show Host
            current_topic = context.get("current_topic", "")
            if agent_type == "Show Host" and current_topic in ["introduction", "conclusion"]:
                return context.get("content", "")

            # Get discussion history and fresh talking points
            discussion_history = self.discussion_history[-2:] if self.discussion_history else []
            fresh_points = self._get_fresh_talking_points(agent_type)
            
            # Prepare a focused context with only fresh/relevant information
            focused_context = {
                "current_topic": current_topic,
                "content": context.get("content", ""),
                "match_info": {
                    "teams": match_data.get("teams", {}),
                    "score": match_data.get("score", {}),
                    "goals": match_data.get("goals", []),
                    "fixture": match_data.get("fixture", {}),
                    "venue": match_data.get("fixture", {}).get("venue", {}),
                    "referee": match_data.get("fixture", {}).get("referee"),
                    "league": match_data.get("match_info", {}).get("league", {})
                },
                "fresh_talking_points": fresh_points,
                "discussion_history": discussion_history
            }

            # Add role-specific information that hasn't been discussed
            if agent_type == "Tactical Analyst":
                # Only add formations if not discussed
                if not self.tactics_mentioned["formation_comparison"]:
                    focused_context["formations"] = match_data.get("details", {}).get("formations", {})
                
                # Only add events for players not discussed
                focused_context["events"] = [
                    e for e in match_data.get("events", [])
                    if not any(p in self.players_discussed for p in [
                        e.get("player", {}).get("name", "").lower()
                    ])
                ]
                
                # Only add possession if not discussed
                if not self.stats_mentioned["possession"]:
                    focused_context["possession"] = match_data.get("details", {}).get("possession", {})
                    
            elif agent_type == "Stats Expert":
                # Only include undiscussed statistics
                stats_context = {"team_stats": {}, "player_stats": {}}
                
                team_stats = match_data.get("team_stats", {})
                for stat_type, value in team_stats.items():
                    stat_key = stat_type.lower().replace(" ", "_")
                    if stat_key in self.stats_mentioned and not self.stats_mentioned[stat_key]:
                        stats_context["team_stats"][stat_type] = value
                
                # Only include players not extensively discussed
                player_stats = match_data.get("player_stats", {})
                for team in ["home", "away"]:
                    stats_context["player_stats"][team] = [
                        p for p in player_stats.get(team, [])
                        if p.get("name", "").lower() not in self.players_discussed
                    ]
                
                focused_context["statistics"] = stats_context

            # Generate response using the agent with focused context
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=json.dumps(focused_context))
            ]
            
            response = await agent.ainvoke(messages)
            if response:
                content = response.content
                # Update discussion history
                self.discussion_history.append((agent_type, content))
                return content
            
            return None

        except Exception as e:
            print(f"❌ Error generating response for {agent_type}: {e}")
            return None

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
        panel = EnhancedPanelDiscussion(match_id)
        
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
        script_dir = "generated_scripts"
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, f"match_{match_id}_discussion.txt")
        
        # Save script
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(formatted_script)
            print(f"\n✅ Script saved to: {script_path}")
        except Exception as e:
            print(f"❌ Error saving script: {e}")
            return
            
        # Show preview
        print("\nScript preview:")
        print("=" * 50)
        preview_length = min(500, len(formatted_script))
        print(formatted_script[:preview_length] + "...\n")
        
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