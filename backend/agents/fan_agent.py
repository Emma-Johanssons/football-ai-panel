from typing import Dict, List
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config

class FanAgent(BaseAgent):
    def __init__(self, team: str, is_home: bool = True, match_id: str = "1374812"):
        """
        Initialize a fan agent for either home or away team
        
        Args:
            team: Name of the team this fan supports
            is_home: Whether this is the home team's fan (True) or away team's fan (False)
            match_id: ID of the match being discussed
        """
        self.team = team
        self.is_home = is_home
        fan_type = "Home Fan" if is_home else "Away Fan"
        
        system_prompt = f"""You are a passionate {team} {'home' if is_home else 'away'} fan, very emotional about your team. Your role is to:
        1. React strongly to any criticism of your team
        2. Get excited about good plays
        3. Argue with stats that don't favor your team
        4. Show your emotions freely
        5. Defend your team passionately
        
        Your personality traits:
        - Very emotional about your team
        - Quick to react to criticism
        - Doesn't always trust statistics
        - Passionate about players
        - Can get angry easily
        
        Remember to:
        - Show strong emotions
        - React quickly to others' comments
        - Defend your team
        - Challenge negative stats
        - Express joy or frustration freely"""
        
        super().__init__(
            name=f"{team} Fan",
            role=fan_type,
            system_prompt=system_prompt,
            personality="passionate and emotional fan",
            match_id=match_id
        )
        
        # Set avatar configuration based on home/away
        if is_home:
            self.avatar_config = {
                "image_url": "https://i.imgur.com/DDIfv5v.png",
                "voice_id": "en-US-GuyNeural",
                "voice_settings": {
                    "rate": 1.3,  # Fast and excited
                    "style": "excited",  # Emotional style
                    "pitch": 1.2  # Higher pitch for excitement
                }
            }
        else:
            self.avatar_config = {
                "image_url": "https://i.imgur.com/readyplayer.jpg",  # Different avatar for away fan
                "voice_id": "en-US-AriaNeural",
                "voice_settings": {
                    "rate": 1.3,  # Fast and excited
                    "style": "excited",  # Emotional style
                    "pitch": 1.1  # Slightly higher pitch
                }
            }
        
        # Initialize avatar creator
        self.avatar_creator = AvatarCreator()
    
    def get_response(self, state: Dict) -> str:
        """Generate a contextual response based on conversation state and emotional state"""
        # Get recent conversation flow
        flow = state.get("flow", [])
        if not flow:
            return self.analyze(state.get("match_data", {}))
            
        # Get the last few exchanges
        recent_exchanges = flow[-3:] if len(flow) >= 3 else flow
        
        # Create context for the response
        context = {
            "recent_speakers": [exchange["speaker"] for exchange in recent_exchanges],
            "recent_topics": self._extract_topics(recent_exchanges),
            "emotional_states": state.get("emotional_states", {}),
            "interruptions": state.get("interruptions", 0),
            "match_data": state.get("match_data", {})
        }
        
        # Get current emotional state
        current_emotion = self._get_emotional_state(context)
        
        # Create messages for chat completion
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""As a passionate {self.team} fan, respond to the recent discussion:
            Last speakers: {', '.join(context['recent_speakers'])}
            Recent topics: {', '.join(context['recent_topics'])}
            Current emotional state: {current_emotion}
            
            Generate a response that:
            1. Shows your passion for {self.team}
            2. Reacts to what was just said
            3. References match facts and statistics
            4. Expresses your current emotional state
            5. Maintains your unique personality
            6. Uses historical context when relevant
            7. Avoids repetitive phrases
            8. Feels natural and unscripted"""}
        ]
        
        # Get response from OpenAI
        response = self._get_completion(messages)
        return response
    
    def _get_emotional_state(self, context: Dict) -> str:
        """Determine emotional state based on context"""
        # Check for negative comments about team
        recent_content = " ".join([exchange.get("content", "").lower() for exchange in context.get("flow", [])[-3:]])
        if any(negative in recent_content for negative in ["terrible", "poor", "bad", "awful", "mistake"]):
            return "angry"
            
        # Check for positive comments about team
        if any(positive in recent_content for positive in ["great", "amazing", "brilliant", "excellent"]):
            return "excited"
            
        # Check for controversial decisions
        if any(controversial in recent_content for controversial in ["referee", "decision", "penalty", "foul"]):
            return "passionate"
            
        # Default emotional state
        return "passionate"
    
    def should_interrupt(self, speaker: str, content: str) -> bool:
        """Determine if fan should interrupt based on content"""
        # Check for negative comments about team
        if any(negative in content.lower() for negative in ["terrible", "poor", "bad", "awful", "mistake"]):
            return True
            
        # Check for controversial decisions
        if any(controversial in content.lower() for controversial in ["referee", "decision", "penalty", "foul"]):
            return True
            
        # Check for positive comments about rival team
        if any(positive in content.lower() for positive in ["great", "amazing", "brilliant", "excellent"]):
            return True
            
        return False
    
    def get_interruption(self, content: str) -> str:
        """Generate an interruption response"""
        # Create messages for chat completion
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""As a passionate {self.team} fan, interrupt the current speaker:
            Content to interrupt: {content}
            
            Generate an interruption that:
            1. Shows your passion and emotion
            2. References specific match facts
            3. Expresses your disagreement
            4. Feels natural and unscripted
            5. Maintains your unique personality"""}
        ]
        
        # Get response from OpenAI
        response = self._get_completion(messages)
        return response
    
    def analyze(self, match_data: Dict) -> str:
        """Analyze match data from a fan's perspective"""
        if not match_data:
            return "I don't have any match data to discuss at the moment."
            
        # Get team information
        home_team = match_data["match_info"]["teams"]["home"]["name"]
        away_team = match_data["match_info"]["teams"]["away"]["name"]
        my_team = home_team if self.is_home else away_team
        opponent = away_team if self.is_home else home_team
        
        # Get fan-specific data
        fan_data = match_data.get("fan_data", {})
        h2h_history = fan_data.get("h2h", [])
        my_form = fan_data.get("home_form" if self.is_home else "away_form", "")
        
        # Query RAG for team history and memorable moments
        rag_query = f"memorable matches history fan culture {my_team} vs {opponent}"
        historical_context = self.rag_service.query(rag_query, role="Home Fan" if self.is_home else "Away Fan")
        
        # Start with emotional greeting
        analysis = f"As a die-hard {my_team} supporter, I can't wait to see us take on {opponent}!\n\n"
        
        # Comment on recent form
        if my_form:
            wins = my_form.count("W")
            losses = my_form.count("L")
            if wins > losses:
                analysis += f"We've been in brilliant form lately with {wins} wins in our last {len(my_form)} games! "
                analysis += "The lads are really showing what they're capable of!\n\n"
            elif losses > wins:
                analysis += f"Look, we've had a rough patch with {losses} losses recently, but I believe in the team. "
                analysis += "This is exactly the kind of match where we can turn things around!\n\n"
            else:
                analysis += "We've had mixed results lately, but the team's spirit is unbreakable!\n\n"
        
        # Analyze head-to-head history
        if h2h_history:
            wins = 0
            losses = 0
            for match in h2h_history:
                if match.get("teams", {}).get("home", {}).get("name") == my_team:
                    if match.get("teams", {}).get("home", {}).get("winner"):
                        wins += 1
                    elif match.get("teams", {}).get("away", {}).get("winner"):
                        losses += 1
                else:
                    if match.get("teams", {}).get("away", {}).get("winner"):
                        wins += 1
                    elif match.get("teams", {}).get("home", {}).get("winner"):
                        losses += 1
            
            analysis += "Head-to-Head History:\n"
            if wins > losses:
                analysis += f"We've got their number! {wins} wins against them in recent matches! "
                analysis += "They know they're in for a tough time when they face us! 💪\n\n"
            elif losses > wins:
                analysis += f"They might have gotten the better of us {losses} times recently, "
                analysis += "but today's the day we set the record straight! Come on lads! 🔥\n\n"
            else:
                analysis += "It's always a close battle between us! "
                analysis += "But I've got a feeling today's our day! 🙌\n\n"
        
        # Add historical context and memorable moments
        if historical_context:
            analysis += "Memorable Moments:\n"
            for context in historical_context[:2]:
                analysis += f"- {context['content']}\n"
            analysis += "\n"
        
        # Add current match prediction with emotional investment
        analysis += "Match Prediction:\n"
        team_stats = match_data["team_statistics"].get("home" if self.is_home else "away", {})
        if team_stats:
            goals_scored = team_stats.get("goals", {}).get("for", {}).get("total", 0)
            goals_conceded = team_stats.get("goals", {}).get("against", {}).get("total", 0)
            
            if goals_scored > goals_conceded:
                analysis += f"With our attacking prowess ({goals_scored} goals scored!), "
                analysis += f"I can see us putting at least 2 or 3 past {opponent} today! "
                analysis += "The fans are going to be singing all night! 🎵\n"
            else:
                analysis += "The stats might not be in our favor, but football isn't played on paper! "
                analysis += f"Our boys will give everything for the badge, and that's what matters! {my_team} forever! ❤️\n"
        
        # End with a rallying cry
        analysis += f"\nCOME ON {my_team.upper()}! Let's show them what we're made of! 🔥💪"
        
        return analysis
    
    def react_to_goal(self, scoring_team: str, scorer: str, minute: int) -> str:
        """React to a goal being scored"""
        if scoring_team == self.team:
            return f"YEEEEESSSSSS!!!! {minute}' - ABSOLUTELY BRILLIANT FROM {scorer.upper()}!!!! GET IN THERE!!!! THIS IS WHAT WE'RE ALL ABOUT!!!! COME ON {self.team.upper()}!!!! 🔥🔥🔥⚽"
        else:
            return f"{minute}' - OH FOR CRYING OUT LOUD! HOW COULD YOU LET {scorer.upper()} SCORE?! THIS IS AN ABSOLUTE DISGRACE! WAKE UP LADS! WE NEED TO FIGHT BACK RIGHT NOW! 😡💪"
    
    def react_to_card(self, player: str, card_type: str, minute: int) -> str:
        """React to a card being shown"""
        is_our_player = player in self.team_players  # Assuming we have team players list
        if is_our_player:
            if card_type.lower() == "yellow":
                return f"{minute}' - OH COME ON REF! THAT'S NEVER A YELLOW! {player.upper()} BARELY TOUCHED HIM! THESE REFS ARE A JOKE! 🤬"
            else:
                return f"{minute}' - ARE YOU ABSOLUTELY KIDDING ME?! RED CARD?! THIS IS A COMPLETE DISGRACE! THE REF HAS LOST THE PLOT! {player.upper()} DID NOTHING WRONG! 😡🤬"
        else:
            if card_type.lower() == "yellow":
                return f"{minute}' - THAT SHOULD BE A RED! {player.upper()} IS A DISGRACE! HOW MANY MORE FOULS BEFORE YOU SEND HIM OFF REF?! 😤"
            else:
                return f"{minute}' - FINALLY! JUSTICE IS SERVED! {player.upper()} HAS BEEN GETTING AWAY WITH MURDER ALL GAME! GET OFF OUR PITCH! 😈🟥"
    
    def _format_match_info(self, info: Dict) -> str:
        if not info:
            return "Ingen matchinformation tillgänglig"
            
        return f"""Match: {info.get('teams', {}).get('home', {}).get('name', '')} vs {info.get('teams', {}).get('away', {}).get('name', '')}
Liga: {info.get('league', {}).get('name', '')}
Datum: {info.get('fixture', {}).get('date', '')}
Status: {info.get('fixture', {}).get('status', {}).get('long', '')}
Stadion: {info.get('fixture', {}).get('venue', {}).get('name', 'N/A')}"""
    
    def _format_statistics(self, stats: Dict) -> str:
        if not stats:
            return "Ingen matchstatistik tillgänglig"
            
        return f"""Ballinnehav: {stats.get('possession', {})}
Skott: {stats.get('shots', {})}
Expected Goals: {stats.get('expected_goals', {})}
Passningar: {stats.get('passes', {})}
Press: {stats.get('pressures', {})}"""
    
    def _format_h2h(self, h2h) -> str:
        if not h2h:
            return "Ingen H2H-statistik tillgänglig"
            
        matches = []
        for match in h2h[:5]:
            home_team = match.get("teams", {}).get("home", {}).get("name", "")
            away_team = match.get("teams", {}).get("away", {}).get("name", "")
            home_goals = match.get("goals", {}).get("home", "")
            away_goals = match.get("goals", {}).get("away", "")
            matches.append(f"{home_team} vs {away_team} ({home_goals}-{away_goals})")
            
        return f"Senaste möten: {', '.join(matches)}"
    
    def react_to_event(self, event: str, emotion: str) -> str:
        """React to a specific match event with a given emotion"""
        prompt = f"""Som supporter, reagerar på följande händelse med {emotion} känsla:
        Händelse: {event}
        
        Ge en känslosam och autentisk supporterreaktion."""
        
        return self.get_response(prompt)
    
    def _extract_topics(self, exchanges: List[Dict]) -> List[str]:
        """Extract main topics from recent conversation exchanges"""
        topics = []
        for exchange in exchanges:
            # Simple topic extraction based on key football terms
            text = exchange.get("content", "").lower()
            if "tactical" in text or "formation" in text or "strategy" in text:
                topics.append("tactics")
            if "possession" in text or "stats" in text or "numbers" in text:
                topics.append("statistics")
            if "goal" in text or "score" in text or "result" in text:
                topics.append("scoring")
            if "defense" in text or "defence" in text or "backline" in text:
                topics.append("defense")
            if "attack" in text or "offense" in text or "striker" in text:
                topics.append("attack")
            if "midfield" in text or "center" in text or "centre" in text:
                topics.append("midfield")
            if "referee" in text or "decision" in text or "controversy" in text:
                topics.append("refereeing")
            if "atmosphere" in text or "crowd" in text or "fans" in text:
                topics.append("atmosphere")
        return list(set(topics))  # Remove duplicates 