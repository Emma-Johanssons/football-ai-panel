"""
Test panel discussion using ElevenLabs TTS
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
from agents.base_agent import BaseAgent
from pydub import AudioSegment
from ffmpeg_config import FFMPEG_EXECUTABLE  # Import FFmpeg configuration
from memory_system import PanelMemory  # Import PanelMemory from memory_system
from typing import List, Dict
from dotenv import load_dotenv

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

# Add this mapping at the top of your test_panel.py
TTS_SPEAKER_MAP = {
    "Show Host": "Show Host",
    "Tactical Analyst": "Tactical Analyst",
    "Stats Expert": "Stats Expert",
    "Home Fan": "Home Fan",
    "Away Fan": "Away Fan",
    "Inter Fan": "Inter Fan"
    # Add more if needed
}

async def run_panel_discussion(match_id: str = "1374812"):
    """Run a panel discussion about a match"""
    print(f"Starting panel discussion for match {match_id}")
    
    # Fetch match data for dynamic team assignment
    match_service = MatchService()
    match_data = match_service.get_match_data(match_id)
    if not match_data:
        print("❌ Could not fetch match data. Using default teams.")
        home_team = "Manchester United"
        away_team = "Liverpool"
    else:
        home_team = match_data["match_info"]["teams"]["home"]["name"]
        away_team = match_data["match_info"]["teams"]["away"]["name"]
    
    # Initialize agents with dynamic teams
    host = HostAgent()
    coach = CoachAgent()
    stats = StatsAgent()
    home_fan = FanAgent(team=home_team, is_home=True)
    away_fan = FanAgent(team=away_team, is_home=False)
    
    # Initialize TTS service
    tts = TTSService()
    
    # Dynamic discussion flow with interruptions, responses, and emotions
    discussion = [
        # Host introduction
        {
            "agent": host,
            "type": "Show Host",
            "text": "Welcome to our post-match analysis! What a thrilling game we just witnessed. Let's break it down with our expert panel. First, let's hear from our tactical analyst about the key battles we saw today."
        },
        # Coach responds to host - more neutral analysis
        {
            "agent": coach,
            "type": "Tactical Analyst",
            "text": "From a tactical perspective, it was fascinating to watch how both teams adapted their midfield structure throughout the game. The home team's pressing was effective, but the away team's ability to maintain possession under pressure was equally impressive.",
            "emotion": "analytical"
        },
        # Home fan interrupts excitedly
        {
            "agent": home_fan,
            "type": "Home Fan",
            "text": "Wait a second! What about that pressing?! Our boys were absolutely relentless! The energy levels were through the roof! You could feel the intensity from the stands!",
            "emotion": "excited",
            "overlap": 0.5
        },
        # Away fan responds passionately
        {
            "agent": away_fan,
            "type": "Away Fan",
            "text": "Excuse me! Your pressing was good, but we completely dominated possession! The stats don't lie! We were the better team out there!",
            "emotion": "passionate",
            "overlap": 0.3
        },
        # Host intervenes
        {
            "agent": host,
            "type": "Show Host",
            "text": "Let's hear what the numbers tell us. Stats expert, what do the statistics reveal about this match?",
            "emotion": "neutral"
        },
        # Stats expert interrupts - more neutral analysis
        {
            "agent": stats,
            "type": "Stats Expert",
            "text": "Let's look at the numbers objectively. Possession was 52-48 in favor of the away team, but the expected goals tell an interesting story. Both teams created quality chances, which explains why this was such a close contest.",
            "emotion": "analytical"
        },
        # Coach adds insight - balanced perspective
        {
            "agent": coach,
            "type": "Tactical Analyst",
            "text": "The xG numbers support what we saw on the pitch. While the away team had more possession, the home team created equally dangerous opportunities. It was a fascinating tactical battle between two well-organized sides.",
            "emotion": "analytical",
            "overlap": 0.2
        },
        # Home fan gets excited
        {
            "agent": home_fan,
            "type": "Home Fan",
            "text": "Hang on! What about that chance in the 75th minute?! If that had gone in, it would have been game over! The atmosphere was absolutely electric! The whole stadium was on its feet!",
            "emotion": "excited",
            "overlap": 0.4
        },
        # Away fan interrupts passionately
        {
            "agent": away_fan,
            "type": "Away Fan",
            "text": "Just a moment! That's exactly why we won! Our defense was solid throughout, and that last-minute goal was pure class! The way we kept our composure under pressure was outstanding!",
            "emotion": "passionate",
            "overlap": 0.6
        },
        # Host moderates
        {
            "agent": host,
            "type": "Show Host",
            "text": "Let's focus on the key moments. Coach, what was the turning point in this match?",
            "emotion": "neutral"
        },
        # Stats expert provides analysis - objective view
        {
            "agent": stats,
            "type": "Stats Expert",
            "text": "From a statistical perspective, the turning point came after that tactical switch in the 60th minute. The substitution changed the game's dynamics, leading to more open play and increased chance creation for both teams.",
            "emotion": "analytical"
        },
        # Coach agrees and adds insight - balanced analysis
        {
            "agent": coach,
            "type": "Tactical Analyst",
            "text": "The data supports that observation. The tactical change opened up the game, creating more space for both teams to exploit. It was a well-timed decision that led to an exciting final 30 minutes.",
            "emotion": "analytical",
            "overlap": 0.3
        },
        # Host leads to conclusion
        {
            "agent": host,
            "type": "Show Host",
            "text": "Now, let's get to the big question: Did the right team win today? Let's hear from our panel.",
            "emotion": "neutral"
        },
        # Stats expert gives final analysis - objective conclusion
        {
            "agent": stats,
            "type": "Stats Expert",
            "text": "Looking at the complete statistical picture - possession, expected goals, and chance creation - the away team showed slightly better efficiency in converting their opportunities. However, it was a very close contest that could have gone either way.",
            "emotion": "analytical"
        },
        # Coach agrees - balanced conclusion
        {
            "agent": coach,
            "type": "Tactical Analyst",
            "text": "I have to agree. While both teams showed quality, the away team's clinical finishing in key moments proved decisive. The home team can take pride in their performance, but the away team's composure in crucial situations made the difference.",
            "emotion": "analytical",
            "overlap": 0.2
        },
        # Home fan reluctantly accepts
        {
            "agent": home_fan,
            "type": "Home Fan",
            "text": "Look, I hate to admit it, but... they were better today. Our boys gave everything, but sometimes that's not enough. We'll get them next time!",
            "emotion": "passionate",
            "overlap": 0.3
        },
        # Away fan celebrates
        {
            "agent": away_fan,
            "type": "Away Fan",
            "text": "Absolutely! We showed our class when it mattered! That's what champions are made of! What a performance from the lads!",
            "emotion": "excited",
            "overlap": 0.4
        },
        # Host concludes
        {
            "agent": host,
            "type": "Show Host",
            "text": "Well, there you have it! A fascinating match with a deserving winner. Thank you all for your insights. That's all from our panel today!",
            "emotion": "neutral"
        }
    ]
    
    # Generate single mixed audio for the entire discussion
    print("\n🎤 Generating mixed panel discussion...")
    audio_file = await tts.generate_mixed_discussion(discussion)
    if audio_file:
        print(f"✅ Generated mixed audio: {audio_file}")
    else:
        print("❌ Failed to generate mixed audio")

async def run_dynamic_panel(match_id, max_turns=15):  # Reduced max turns for shorter discussion
    print(f"Starting panel discussion for match {match_id}")
    
    # Fetch match data for dynamic team assignment
    match_service = MatchService()
    match_data = match_service.get_match_data(match_id)
    if not match_data:
        print("❌ Could not fetch match data. Using default teams.")
        home_team = "Manchester United"
        away_team = "Liverpool"
    else:
        home_team = match_data["match_info"]["teams"]["home"]["name"]
        away_team = match_data["match_info"]["teams"]["away"]["name"]
    
    # Initialize specialized agents with match data
    print("Initializing agents...")
    host = HostAgent(match_id=match_id)
    coach = CoachAgent(match_id=match_id)
    stats = StatsAgent(match_id=match_id)
    
    agents = [host, coach, stats]
    
    # Wait for all agents to load their data
    print("Loading match data and knowledge...")
    for agent in agents:
        try:
            agent._load_match_data()
        except Exception as e:
            print(f"❌ Error loading data for {agent.role}: {str(e)}")
            return
    
    # Verify all agents have loaded their data
    if not all(agent.data_loaded for agent in agents):
        print("❌ Not all agents have loaded their data. Aborting discussion.")
        return
    
    print("✅ All data loaded successfully. Starting discussion...")
    
    # Initialize conversation state with match data
    state = {
        "match_data": match_data,
        "current_topic": "match_overview",
        "emotional_states": {},
        "flow": [],
        "match_id": match_id,
        "lineups": match_data.get("lineups", {}),
        "player_stats": match_data.get("player_stats", {})
    }
    
    # Initialize panel memory
    panel_memory = PanelMemory(match_id=match_id)
    for agent in agents:
        panel_memory.add_agent(agent.name)
    
    # Start with host introduction
    host_intro = host.analyze(match_data)
    conversation = [(host.name, host_intro)]
    state["flow"].append({"speaker": host.name, "content": host_intro})
    panel_memory.add_statement(host.name, host_intro, "neutral")
    
    # Dynamic discussion loop
    current_turn = 0
    while current_turn < max_turns:
        # Determine next speaker based on context and conversation flow
        next_speaker = None
        for agent in agents:
            if agent.should_speak(state):
                next_speaker = agent
                break
        
        if not next_speaker:
            # If no agent wants to speak, let the host guide the discussion
            next_speaker = host
        
        # Generate response
        response = next_speaker.get_response(state)
        
        # Add to conversation
        conversation.append((next_speaker.name, response))
        state["flow"].append({"speaker": next_speaker.name, "content": response})
        panel_memory.add_statement(next_speaker.name, response, "neutral")
        
        # Update emotional states
        state["emotional_states"][next_speaker.name] = "neutral"
        
        current_turn += 1
        
        # Check if we should end the discussion
        if "final question" in response.lower() or "right team win" in response.lower():
            break
    
    return conversation

async def conversation_to_audio(conversation: List[Dict], match_id: str) -> str:
    """Convert the conversation to audio using TTS service"""
    try:
        # Initialize TTS service
        tts_service = TTSService()
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), "audio")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate audio for each turn in the conversation
        audio_segments = []
        for turn in conversation:
            # Map team-specific fan types to generic fan types
            speaker_type = turn["type"]
            if "Paris Saint Germain" in speaker_type:
                speaker_type = "Paris Saint Germain Fan"
            elif "Inter" in speaker_type:
                speaker_type = "Inter Fan"
            elif "Fan" in speaker_type and not any(team in speaker_type for team in ["Paris Saint Germain", "Inter"]):
                # For other teams, use Home/Away Fan configuration
                speaker_type = "Home Fan" if "Home" in speaker_type else "Away Fan"
            
            # Generate audio for this turn
            audio_path = tts_service.generate_speech(turn["text"], speaker_type)
            if audio_path:
                audio_segments.append(audio_path)
        
        # Combine all audio segments
        if not audio_segments:
            return None
            
        # Create final mixed audio
        final_audio = AudioSegment.from_mp3(audio_segments[0])
        for segment_path in audio_segments[1:]:
            segment = AudioSegment.from_mp3(segment_path)
            final_audio += segment
        
        # Save final mixed audio
        output_path = os.path.join(output_dir, f"panel_conversation_{match_id}.mp3")
        final_audio.export(output_path, format="mp3")
        print(f"Mixed audio saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error converting conversation to audio: {e}")
        return None

async def generate_script(match_id, max_turns=15):
    """Generate the discussion script first"""
    # Fetch match data for dynamic team assignment
    match_service = MatchService()
    match_data = match_service.get_match_data(match_id)
    if not match_data:
        print("❌ Could not fetch match data. Using default teams.")
        home_team = "Manchester United"
        away_team = "Liverpool"
    else:
        home_team = match_data["match_info"]["teams"]["home"]["name"]
        away_team = match_data["match_info"]["teams"]["away"]["name"]
    
    # Initialize specialized agents with match data
    host = HostAgent(match_id=match_id)
    coach = CoachAgent(match_id=match_id)
    stats = StatsAgent(match_id=match_id)
    
    agents = [host, coach, stats]
    
    # Initialize conversation state with match data
    state = {
        "match_data": match_data,
        "current_topic": "match_overview",
        "emotional_states": {},
        "flow": [],
        "match_id": match_id,
        "lineups": match_data.get("lineups", {}),
        "player_stats": match_data.get("player_stats", {})
    }
    
    # Initialize panel memory
    panel_memory = PanelMemory(match_id=match_id)
    for agent in agents:
        panel_memory.add_agent(agent.name)
    
    # Scripted introduction
    host_intro = f"""Welcome to our post-match analysis of {home_team} versus {away_team}. 
I'm joined by our tactical analyst, a former professional player who understands the game from both a player's and coach's perspective, and our stats expert who will provide data-driven insights. 
Let's break down this fascinating match."""
    
    conversation = [(host.name, host_intro)]
    state["flow"].append({"speaker": host.name, "content": host_intro})
    
    # Dynamic discussion loop
    current_turn = 0
    while current_turn < max_turns:
        # Get responses from all agents
        responses = []
        for agent in agents:
            if agent != host:  # Skip host for now
                # Get response with full match context
                response = agent.get_response({
                    **state,
                    "match_data": match_data,
                    "lineups": match_data.get("lineups", {}),
                    "player_stats": match_data.get("player_stats", {}),
                    "team_stats": match_data.get("team_statistics", {}),
                    "formations": match_data.get("formations", {}),
                    "score": match_data.get("match_info", {}).get("score", {})
                })
                
                if response and len(response.strip()) > 0:
                    responses.append((agent, response))
        
        # If no responses, have host intervene
        if not responses:
            intervention = host.get_intervention_response(state)
            conversation.append((host.name, intervention))
            state["flow"].append({"speaker": host.name, "content": intervention})
            current_turn += 1
            continue
        
        # Select next speaker based on relevance and emotional state
        next_speaker, next_utterance = max(responses, key=lambda x: len(x[1]))
        
        # Add to conversation
        conversation.append((next_speaker.name, next_utterance))
        state["flow"].append({"speaker": next_speaker.name, "content": next_utterance})
        
        # Update emotional states
        state["emotional_states"][next_speaker.name] = "engaged"
        
        # Have host respond to expert's point
        if current_turn % 2 == 0:  # Every other turn
            host_response = host.get_intervention_response(state)
            if host_response:
                conversation.append((host.name, host_response))
                state["flow"].append({"speaker": host.name, "content": host_response})
        
        current_turn += 1
    
    # Scripted conclusion
    conclusion = f"""Now, let's address the big question: With everything we've discussed about the tactics, individual performances, and key moments - did the right team win today? Coach, what's your take?"""
    conversation.append((host.name, conclusion))
    state["flow"].append({"speaker": host.name, "content": conclusion})
    
    # Save conversation to file with better formatting
    script_path = f"panel_script_{match_id}.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(f"Match: {home_team} vs {away_team}\n")
        f.write("=" * 50 + "\n\n")
        
        for speaker, text in conversation:
            f.write(f"{speaker}:\n{text}\n\n")
            f.write("-" * 30 + "\n\n")
    
    print(f"✅ Script saved to {script_path}")
    return conversation, script_path

if __name__ == "__main__":
    import sys
    # Use environment variable as default if no match ID provided
    default_match_id = os.getenv('DEFAULT_MATCH_ID', '1374812')
    match_id = sys.argv[1] if len(sys.argv) > 1 else default_match_id
    
    # First generate and save the script
    print("\n📝 Generating panel discussion script...")
    conversation, script_path = asyncio.run(generate_script(match_id))
    
    # Ask for user confirmation before generating audio
    print("\nWould you like to generate the audio for this script? (y/n)")
    response = input().lower()
    
    if response == 'y':
        print("\n🎤 Generating audio from script...")
        # Convert conversation format to match what conversation_to_audio expects
        formatted_conversation = []
        for speaker, text in conversation:
            # Map speaker to appropriate type
            if speaker == "Show Host":
                speaker_type = "Show Host"
            elif speaker == "Tactical Analyst":
                speaker_type = "Tactical Analyst"
            elif speaker == "Stats Expert":
                speaker_type = "Stats Expert"
            else:
                speaker_type = speaker
                
            formatted_conversation.append({
                "type": speaker_type,
                "text": text,
                "emotion": "neutral"  # Default emotion
            })
        
        # Convert conversation to audio
        asyncio.run(conversation_to_audio(formatted_conversation, match_id))
    else:
        print("\nSkipping audio generation. You can review the script at:", script_path) 