"""
Generate dynamic football match panel discussions with AI-powered video avatars
"""
import os
import sys
import json
import requests
import openai
import subprocess
import time
import random
from dotenv import load_dotenv
from typing import Dict, List, Tuple
from agents import (
    get_avatar_config,
    HostAgent,
    StatsAgent,
    CoachAgent,
    FanAgent
)
from rag_system import FootballKnowledgeRAG
from memory_system import PanelMemory
from video_manager import VideoManager

class PanelDiscussion:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.match_data = None
        
        # Initialize panel memory and video manager
        self.memory = PanelMemory()
        self.video_manager = VideoManager()
        
        # Initialize all panel members
        self.host = HostAgent()
        self.stats_analyst = StatsAgent()
        self.coach = CoachAgent()
        self.home_fan = FanAgent(team="", is_home=True)
        self.away_fan = FanAgent(team="", is_home=False)
        
        # Add agents to memory system
        self.memory.add_agent("Show Host")
        self.memory.add_agent("Stats Expert")
        self.memory.add_agent("Tactical Analyst")
        self.memory.add_agent("Home Fan")
        self.memory.add_agent("Away Fan")
        
        # Track discussion state
        self.discussion_state = {
            "current_topic": None,
            "last_speaker": None,
            "speaking_counts": {"Show Host": 0, "Stats Expert": 0, "Tactical Analyst": 0},
            "discussed_topics": set(),
            "emotional_states": {"Show Host": "neutral", "Stats Expert": "neutral", "Tactical Analyst": "neutral"},
            "player_mentions": {},
            "interesting_facts": [],
            "banter_moments": [],
            "key_events": []
        }
        
        # Load personality traits and fun facts
        self.personality_traits = {
            "Stats Expert": {
                "style": "analytical but engaging",
                "quirks": ["loves using unexpected analogies", "gets excited about rare statistical occurrences"],
                "background": "former data analyst for top clubs"
            },
            "Tactical Analyst": {
                "style": "insightful and passionate",
                "quirks": ["often references games from decades ago", "uses hands a lot while explaining"],
                "background": "played professionally for 15 years"
            },
            "Show Host": {
                "style": "charismatic and knowledgeable",
                "quirks": ["great at spotting tension and lightening the mood", "master of smooth transitions"],
                "background": "20 years in football broadcasting"
            }
        }
        
        # Track current speaker and discussion state
        self.current_speaker = None
        self.discussion_active = True
        
    def fetch_match_data(self):
        """Fetch match data and initialize team names"""
        api_key = os.environ.get("FOOTBALL_API_KEY")
        if not api_key:
            raise ValueError("FOOTBALL_API_KEY not set")
            
        # Initialize RAG system
        self.rag = FootballKnowledgeRAG()
        
        # Fetch basic match info
        response = requests.get(
            f"https://v3.football.api-sports.io/fixtures?id={self.match_id}",
            headers={"x-apisports-key": api_key}
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
            
        response_data = response.json()
        if not response_data.get("response"):
            raise Exception("No response data from API")
            
        raw_match_data = response_data["response"][0]
        
        # Fetch additional data for each agent
        team_ids = [
            raw_match_data["teams"]["home"]["id"],
            raw_match_data["teams"]["away"]["id"]
        ]
        
        # Stats Analyst: Get detailed statistics and team form
        team_statistics = {"home": {}, "away": {}}
        for i, team_id in enumerate(team_ids):
            team_type = "home" if i == 0 else "away"
            stats_response = requests.get(
                f"https://v3.football.api-sports.io/teams/statistics",
                headers={"x-apisports-key": api_key},
                params={
                    "team": team_id,
                    "league": raw_match_data["league"]["id"],
                    "season": raw_match_data["league"]["season"]
                }
            )
            if stats_response.status_code == 200:
                team_statistics[team_type] = stats_response.json().get("response", {})
        
        # Coach: Get lineups, formations, and events
        coach_data = {
            "lineups": raw_match_data.get("lineups", []),
            "events": raw_match_data.get("events", []),
            "formations": {},
            "tactics": {}
        }
        
        # Get historical formations for both teams
        for team_id in team_ids:
            formation_response = requests.get(
                f"https://v3.football.api-sports.io/fixtures",
                headers={"x-apisports-key": api_key},
                params={
                    "team": team_id,
                    "last": 5,
                    "status": "FT"
                }
            )
            if formation_response.status_code == 200:
                coach_data["formations"][team_id] = [
                    match.get("lineups", [{}])[0].get("formation")
                    for match in formation_response.json().get("response", [])
                ]
        
        # Fans: Get head-to-head history and team form
        h2h_response = requests.get(
            f"https://v3.football.api-sports.io/fixtures/headtohead",
            headers={"x-apisports-key": api_key},
            params={"h2h": f"{team_ids[0]}-{team_ids[1]}"}
        )
        
        fan_data = {
            "h2h": h2h_response.json().get("response", []) if h2h_response.status_code == 200 else [],
            "home_form": team_statistics["home"].get("form", ""),
            "away_form": team_statistics["away"].get("form", "")
        }
        
        # Transform all data into our expected format
        self.match_data = {
            "match_info": {
                "teams": raw_match_data.get("teams", {}),
                "score": raw_match_data.get("goals", {"home": 0, "away": 0}),
                "fixture": raw_match_data.get("fixture", {}),
                "league": raw_match_data.get("league", {})
            },
            "team_statistics": team_statistics,
            "coach_data": coach_data,
            "fan_data": fan_data
        }
        
        # Add match data to RAG system for future reference
        self.rag.add_knowledge(
            json.dumps(self.match_data, indent=2),
            {"type": "match_data", "match_id": self.match_id}
        )
        
        # Set team names for fans
        try:
            teams_data = self.match_data["match_info"]["teams"]
            if not teams_data or "home" not in teams_data or "away" not in teams_data:
                raise KeyError("Invalid teams data structure")
                
            home_team = teams_data["home"].get("name")
            away_team = teams_data["away"].get("name")
            
            if not home_team or not away_team:
                raise KeyError("Team names not found")
                
            print(f"Found teams: {home_team} vs {away_team}")
            self.home_fan = FanAgent(team=home_team, is_home=True)
            self.away_fan = FanAgent(team=away_team, is_home=False)
        except KeyError as e:
            print("Match data structure:", json.dumps(self.match_data, indent=2))
            raise Exception(f"Could not find team data in response: {e}")
    
    def _get_next_speaker(self, state: Dict) -> Tuple[str, str]:
        """Determine next speaker based on context and natural flow"""
        last_speaker = state["last_speaker"]
        current_topic = state["current_topic"]
        
        # If no one has spoken yet, host starts
        if not last_speaker:
            return "Show Host", self._get_host_introduction()
            
        # If host just spoke, determine most relevant expert
        if last_speaker == "Show Host":
            if "tactical" in current_topic.lower():
                return "Tactical Analyst", self._get_tactical_insight(state)
            elif "stats" in current_topic.lower():
                return "Stats Expert", self._get_statistical_insight(state)
            else:
                # Let the most relevant expert speak
                coach_relevance = self._calculate_topic_relevance("Tactical Analyst", current_topic)
                stats_relevance = self._calculate_topic_relevance("Stats Expert", current_topic)
                return ("Tactical Analyst" if coach_relevance > stats_relevance else "Stats Expert",
                        self._get_expert_insight(state))
        
        # If an expert just spoke, maybe add some banter or interesting fact
        if random.random() < 0.3:  # 30% chance of banter or interesting fact
            return self._get_banter_or_fact(last_speaker, state)
            
        # Otherwise, let the other expert build on the point or host moderate
        if last_speaker == "Tactical Analyst":
            if self._should_host_moderate(state):
                return "Show Host", self._get_host_moderation(state)
            return "Stats Expert", self._get_statistical_insight(state)
        
        if last_speaker == "Stats Expert":
            if self._should_host_moderate(state):
                return "Show Host", self._get_host_moderation(state)
            return "Tactical Analyst", self._get_tactical_insight(state)
            
        return "Show Host", self._get_host_moderation(state)
    
    def _get_banter_or_fact(self, last_speaker: str, state: Dict) -> Tuple[str, str]:
        """Generate natural banter or interesting fact based on context"""
        # Get relevant player or team being discussed
        current_topic = state["current_topic"]
        player_mentions = state["player_mentions"]
        
        # If a player was mentioned, maybe add some personality
        if player_mentions:
            latest_player = list(player_mentions.keys())[-1]
            if latest_player == "Dembélé":
                return ("Show Host", 
                       "Speaking of Dembélé, I heard he's quite the character in training - "
                       "apparently he's always the last one to arrive but first one to master any new skill!")
            elif latest_player == "Kvaratskhelia":
                return ("Tactical Analyst",
                       "You know what's fascinating about Kvara? He used to practice his dribbling "
                       "by running through the mountains in Georgia. Talk about dedication!")
        
        # Add some tactical banter
        if "formation" in current_topic.lower():
            return ("Stats Expert",
                   "You know what they say about formations - they're like your favorite coffee order. "
                   "Everyone thinks theirs is the best until they try something new!")
        
        # Add statistical humor
        if "stats" in current_topic.lower():
            return ("Tactical Analyst",
                   "All these numbers remind me of my playing days. The only stat I cared about "
                   "was how many minutes until the final whistle when we were winning!")
                   
        return (last_speaker, self._get_expert_insight(state))
    
    def _should_host_moderate(self, state: Dict) -> bool:
        """Determine if host should moderate based on conversation flow"""
        # Check if discussion needs direction
        if len(state["discussed_topics"]) < 3:
            return True
            
        # Check if experts are dominating
        expert_count = (state["speaking_counts"]["Stats Expert"] + 
                       state["speaking_counts"]["Tactical Analyst"])
        host_count = state["speaking_counts"]["Show Host"]
        if expert_count > host_count * 2:
            return True
            
        # Check if we need to move to a new topic
        if state["current_topic"] in state["discussed_topics"]:
            return True
            
        return False
    
    def _get_expert_insight(self, state: Dict) -> str:
        """Get contextual insight from an expert"""
        # Implementation details...
        pass
    
    def _calculate_topic_relevance(self, expert: str, topic: str) -> float:
        """Calculate how relevant a topic is to an expert"""
        # Implementation details...
        pass
    
    def _get_host_introduction(self) -> str:
        """Get host introduction"""
        # Implementation details...
        pass
    
    def _get_tactical_insight(self, state: Dict) -> str:
        """Get tactical insight"""
        # Implementation details...
        pass
    
    def _get_statistical_insight(self, state: Dict) -> str:
        """Get statistical insight"""
        # Implementation details...
        pass
    
    def _get_host_moderation(self, state: Dict) -> str:
        """Get host moderation"""
        # Implementation details...
        pass
    
    def generate_discussion(self) -> str:
        """Generate a dynamic and engaging panel discussion"""
        # Start with host introduction
        host_intro = self.host.analyze(self.match_data)
        self.memory.add_statement("Show Host", host_intro)
        self.video_manager.add_segment(
            "Show Host",
            host_intro,
            get_avatar_config("Show Host")
        )
        
        # Initialize all agents with match data
        self.stats_analyst.learn_from_match(self.match_data)
        self.coach.learn_from_match(self.match_data)
        self.home_fan.learn_from_match(self.match_data)
        self.away_fan.learn_from_match(self.match_data)
        
        # Continue discussion until natural conclusion
        max_turns = 30
        turn = 0
        
        # Track discussion state
        discussion_state = {
            "current_topic": None,
            "last_speaker": "Show Host",
            "emotional_intensity": 0.0,
            "speaking_counts": {agent: 0 for agent in self.memory.agents}
        }
        
        while self.discussion_active and turn < max_turns:
            # Get current state
            state = self.memory.get_discussion_state()
            
            # Let each agent decide if they want to speak
            potential_speakers = []
            for agent_name, agent in [
                ("Stats Expert", self.stats_analyst),
                ("Tactical Analyst", self.coach),
                ("Home Fan", self.home_fan),
                ("Away Fan", self.away_fan)
            ]:
                # Agent decides based on context if they want to speak
                if agent.should_speak(state):
                    response = agent.get_response(state)
                    if response:
                        potential_speakers.append((agent_name, response, agent.calculate_relevance(state)))
            
            # If no one wants to speak, host moves discussion forward
            if not potential_speakers:
                host_prompt = self.host.get_discussion_prompt(state)
                self.memory.add_statement("Show Host", host_prompt)
                self.video_manager.add_segment(
                    "Show Host",
                    host_prompt,
                    get_avatar_config("Show Host")
                )
                discussion_state["speaking_counts"]["Show Host"] += 1
                continue
                
            # Sort potential speakers by relevance and randomness
            random.shuffle(potential_speakers)  # Add some randomness
            potential_speakers.sort(key=lambda x: x[2], reverse=True)  # Sort by relevance
            
            # Take the top 1-2 speakers
            num_speakers = min(2, len(potential_speakers))
            for speaker_name, content, _ in potential_speakers[:num_speakers]:
                # Add main response
                self.memory.add_statement(speaker_name, content)
                self.video_manager.add_segment(
                    speaker_name,
                    content,
                    get_avatar_config(speaker_name)
                )
                discussion_state["speaking_counts"][speaker_name] += 1
                
                # Other agents might react immediately
                reactions = self._get_immediate_reactions(speaker_name, content, state)
                for reactor_name, reaction in reactions:
                    self.memory.add_statement(reactor_name, reaction, sentiment="excited")
                    self.video_manager.add_segment(
                        reactor_name,
                        reaction,
                        get_avatar_config(reactor_name)
                    )
                    discussion_state["speaking_counts"][reactor_name] += 1
            
            # Host intervenes if discussion gets too heated
            if self._needs_host_intervention(state):
                intervention = self.host.get_intervention_response(state)
                self.memory.add_statement("Show Host", intervention, sentiment="neutral")
                self.video_manager.add_segment(
                    "Show Host",
                    intervention,
                    get_avatar_config("Show Host")
                )
                discussion_state["speaking_counts"]["Show Host"] += 1
            
            # Check if discussion should end
            if self._should_end_discussion():
                conclusion = self.host.get_conclusion(state)
                self.memory.add_statement("Show Host", conclusion)
                self.video_manager.add_segment(
                    "Show Host",
                    conclusion,
                    get_avatar_config("Show Host")
                )
                self.discussion_active = False
            
            turn += 1
        
        # Create final video
        output_path = f"panel_discussion_{self.match_id}.mp4"
        self.video_manager.create_panel_video(output_path)
        
        # Save discussion history
        self.memory.save_to_file(f"panel_discussion_{self.match_id}.json")
        
        return output_path

    def _get_immediate_reactions(self, speaker: str, content: str, state: Dict) -> List[Tuple[str, str]]:
        """Get immediate reactions from other agents"""
        reactions = []
        
        # Each agent decides if they want to react immediately
        for agent_name, agent in [
            ("Stats Expert", self.stats_analyst),
            ("Tactical Analyst", self.coach),
            ("Home Fan", self.home_fan),
            ("Away Fan", self.away_fan)
        ]:
            if agent_name != speaker and agent.should_interrupt(speaker, content):
                reaction = agent.get_reaction(content)
                if reaction:
                    reactions.append((agent_name, reaction))
        
        # Limit to 1-2 reactions to avoid chaos
        random.shuffle(reactions)
        return reactions[:2]

    def _needs_host_intervention(self, state: Dict) -> bool:
        """Determine if host needs to intervene"""
        return (
            state["interruptions"] > 3 or  # Too many interruptions
            any(e in ["angry", "frustrated"] for e in state["emotional_states"].values()) or  # High emotions
            self._is_discussion_unbalanced(state)  # Unbalanced participation
        )
    
    def _is_discussion_unbalanced(self, state: Dict) -> bool:
        """Check if discussion participation is unbalanced"""
        counts = state.get("speaking_counts", {})
        if not counts:
            return False
        
        # Calculate average speaking count
        avg_count = sum(counts.values()) / len(counts)
        
        # Check if any agent is speaking too much or too little
        for count in counts.values():
            if count > avg_count * 2 or count < avg_count * 0.5:
                return True
        
        return False

    def _should_end_discussion(self) -> bool:
        """Determine if discussion should end"""
        state = self.memory.get_discussion_state()
        
        # Ensure minimum discussion length (about 5-10 minutes)
        # Assuming each segment is about 20-30 seconds
        min_exchanges = 15  # This should give us at least 5 minutes
        if len(state["flow"]) < min_exchanges:
            return False
        
        # End if too many interruptions
        if state["interruptions"] > 15:  # Increased from 10
            return True
            
        # End if too many host interventions
        if state["host_interventions"] > 8:  # Increased from 5
            return True
            
        # End if discussion has covered main points and is long enough
        if len(state["flow"]) > 25:  # Increased from 15 (about 8-10 minutes)
            return True
            
        # End if all agents are calm and we've had minimum exchanges
        emotional_states = state.get("emotional_states", {})
        if len(state["flow"]) >= min_exchanges:
            all_neutral = True
            for emotion in emotional_states.values():
                if emotion != "neutral":
                    all_neutral = False
                    break
            if all_neutral:
                return True
        
        return False

def main(match_id: str):
    # Initialize panel discussion
    panel = PanelDiscussion(match_id)
    
    try:
        # Fetch match data
        print("Fetching match data...")
        panel.fetch_match_data()
        
        # Generate discussion
        print("Generating panel discussion...")
        output_path = panel.generate_discussion()
        print(f"✅ Panel discussion video saved to: {output_path}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_match_discussion.py <match_id>")
        sys.exit(1)
        
    main(sys.argv[1]) 