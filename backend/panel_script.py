import json
import os
from datetime import datetime
from agents.host_agent import HostAgent
from agents.coach_agent import CoachAgent
from agents.stats_agent import StatsAgent
from services.match_service import MatchService

class Panel:
    def __init__(self, match_id):
        self.host = HostAgent()
        self.coach = CoachAgent(match_id)
        self.stats = StatsAgent(match_id)
        self.match_id = match_id
        self.match_service = MatchService()
        self.current_topic = "match_overview"
        self.flow = []
        self.discussed_topics = set()
        self.conclusion_reached = False
        
        # Load historical data from logs
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical match data from logs"""
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        latest_timestamp = None
        latest_files = {}
        
        # Find latest log files
        for file in os.listdir(log_dir):
            if file.endswith(".json"):
                timestamp = file.split("_")[1]  # Get timestamp from filename
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    
        if latest_timestamp:
            # Load each type of log
            for agent in ["stats", "coach", "referee", "fan"]:
                file_path = os.path.join(log_dir, f"{agent}_{latest_timestamp}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        latest_files[agent] = json.load(f)
        
        self.historical_data = latest_files
    
    def generate_discussion(self):
        """Generate a dynamic panel discussion"""
        # Get match data
        match_data = self.match_service.get_match_data(self.match_id)
        lineups = self.match_service.get_lineups(self.match_id)
        player_stats = self.match_service.get_player_stats(self.match_id)
        
        # Initialize state
        state = {
            "match_data": match_data,
            "lineups": lineups,
            "player_stats": player_stats,
            "historical_data": self.historical_data,
            "current_topic": "match_overview",
            "flow": self.flow,
            "discussed_topics": self.discussed_topics
        }
        
        # Start with host introduction
        self._add_to_discussion(self.host.get_response(state))
        
        # Continue discussion until conclusion is reached
        while not self.conclusion_reached:
            state["flow"] = self.flow
            state["discussed_topics"] = self.discussed_topics
            
            # Get last exchange
            last_exchange = self.flow[-1]
            last_speaker = last_exchange["role"]
            last_content = last_exchange["content"]
            
            # Determine who should speak next based on context
            next_speaker = self._determine_next_speaker(state)
            
            # Get response from next speaker
            if next_speaker == "host":
                response = self.host.get_response(state)
            elif next_speaker == "coach":
                response = self.coach.get_response(state)
            else:  # stats
                response = self.stats.get_response(state)
                
            # Add response to discussion
            self._add_to_discussion(response, next_speaker)
            
            # Check if conclusion has been reached
            self.conclusion_reached = self._check_conclusion_reached()
            
        return self.format_discussion()
    
    def _determine_next_speaker(self, state):
        """Dynamically determine who should speak next based on context"""
        last_exchange = state["flow"][-1]
        last_speaker = last_exchange["role"]
        last_content = last_exchange["content"].lower()
        
        # If host just spoke, determine based on content
        if last_speaker == "host":
            if "tactical" in last_content or "formation" in last_content:
                return "coach"
            elif "statistics" in last_content or "numbers" in last_content:
                return "stats"
            else:
                # Let the most relevant expert speak
                coach_relevance = self.coach.calculate_relevance(state)
                stats_relevance = self.stats.calculate_relevance(state)
                return "coach" if coach_relevance > stats_relevance else "stats"
        
        # If an expert just spoke, let other expert respond or host moderate
        if last_speaker == "coach":
            if self._should_host_intervene(state):
                return "host"
            return "stats"
        
        if last_speaker == "stats":
            if self._should_host_intervene(state):
                return "host"
            return "coach"
        
        return "host"  # Default to host if unclear
    
    def _should_host_intervene(self, state):
        """Determine if host should intervene to guide discussion"""
        recent_exchanges = state["flow"][-3:]  # Look at last 3 exchanges
        
        # Count consecutive expert exchanges
        expert_count = sum(1 for ex in recent_exchanges 
                         if ex["role"] in ["coach", "stats"])
        
        # Intervene if:
        # 1. Too many expert exchanges without host
        # 2. Discussion is getting off track from goal
        # 3. Need to move to new topic
        return (expert_count >= 3 or
                len(self.discussed_topics) < 3 or
                self._is_discussion_off_track(state))
    
    def _is_discussion_off_track(self, state):
        """Check if discussion has deviated from goal of determining if right team won"""
        recent_content = " ".join(ex["content"].lower() 
                                for ex in state["flow"][-3:])
        
        goal_keywords = ["deserve", "victory", "result", "outcome", "winner",
                        "performance", "better team", "justified"]
                        
        return not any(keyword in recent_content for keyword in goal_keywords)
    
    def _check_conclusion_reached(self):
        """Check if a conclusion about the right team winning has been reached"""
        if len(self.flow) < 5:  # Need minimum exchanges
            return False
            
        recent_exchanges = self.flow[-5:]
        recent_content = " ".join(ex["content"].lower() for ex in recent_exchanges)
        
        # Check if both experts have given their verdict
        coach_concluded = any("verdict" in ex["content"].lower() 
                            for ex in recent_exchanges 
                            if ex["role"] == "coach")
        
        stats_concluded = any("verdict" in ex["content"].lower() 
                            for ex in recent_exchanges 
                            if ex["role"] == "stats")
        
        return coach_concluded and stats_concluded
    
    def _add_to_discussion(self, response, role="host"):
        """Add a response to the discussion flow"""
        self.flow.append({
            "role": role,
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update discussed topics based on content
        self._update_discussed_topics(response)
    
    def _update_discussed_topics(self, content):
        """Track discussed topics from response content"""
        content_lower = content.lower()
        
        topic_keywords = {
            "tactics": ["formation", "tactical", "setup", "approach"],
            "statistics": ["numbers", "stats", "percentage", "accuracy"],
            "players": ["player", "performance", "individual"],
            "key_moments": ["moment", "turning point", "chance"],
            "conclusion": ["verdict", "deserve", "rightful", "winner"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                self.discussed_topics.add(topic)
    
    def format_discussion(self):
        """Format the discussion for display"""
        output = []
        
        # Add match title
        match_data = self.match_service.get_match_data(self.match_id)
        teams = match_data.get("response", [{}])[0].get("teams", {})
        home_team = teams.get("home", {}).get("name", "Home Team")
        away_team = teams.get("away", {}).get("name", "Away Team")
        
        output.append(f"Match: {home_team} vs {away_team}")
        output.append("=" * 50)
        output.append("")
        
        # Add each exchange
        for exchange in self.flow:
            role = exchange["role"]
            content = exchange["content"]
            
            # Format the speaker's name
            if role == "host":
                speaker = "Show Host"
            elif role == "coach":
                speaker = "Tactical Analyst"
            elif role == "stats":
                speaker = "Stats Expert"
            
            output.append(f"{speaker}:")
            output.append(content)
            output.append("")
            output.append("-" * 30)
            output.append("")
        
        return "\n".join(output) 