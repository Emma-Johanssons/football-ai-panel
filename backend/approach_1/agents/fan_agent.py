"""
Fan agent for panel discussions
"""
from typing import Dict, List
from .base_agent import BaseAgent
from create_avatar import AvatarCreator
from .avatar_mapping import get_avatar_config
from services.match_service import MatchService
import random

class FanAgent(BaseAgent):
    def __init__(self, team: str, is_home: bool, match_id: str = None):
        name = f"{'Home' if is_home else 'Away'} Fan"
        role = f"{'Home' if is_home else 'Away'} Fan"
        system_prompt = f"""You are a passionate {team} fan.
        Your role is to:
        1. Share fan perspective and emotions
        2. Discuss team history and traditions
        3. Comment on player performances
        4. Express hopes and concerns
        5. Maintain fan loyalty while being respectful
        6. Add color and passion to the discussion"""
        personality = "passionate and knowledgeable fan"
        
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        self.team = team
        self.is_home = is_home
        
        # Initialize fan-specific attributes
        self.emotional_state = "neutral"  # Can be: excited, nervous, disappointed, elated
        self.confidence_level = 0.5  # 0.0 to 1.0
        
        # Track discussed topics
        self.discussed_topics = set()
        
        # Initialize response templates
        self.response_templates = {
            "positive": [
                "Absolutely brilliant from {player}!",
                "That's exactly what we expect from {team}!",
                "You can see why we fans love {player} so much!",
                "Classic {team} performance right there!",
                "This is why {team} is special!"
            ],
            "negative": [
                "We need to do better than that...",
                "Not what you expect from {team}...",
                "{player} needs to step up here.",
                "This isn't the {team} we know.",
                "We've got to improve this."
            ],
            "neutral": [
                "Interesting point about {team}.",
                "Let's see how {player} develops.",
                "There's more to come from {team}.",
                "We've seen both sides of {team} today.",
                "It's a work in progress."
            ]
        }
        
    async def _generate_response(self, current_state: Dict, recent_context: List[Dict], match_data: Dict, knowledge: Dict) -> str:
        """Generate a fan response based on the current state"""
        try:
            # Update emotional state based on match situation
            self._update_emotional_state(match_data)
            
            # Get last speaker and content
            last_exchange = recent_context[-1] if recent_context else None
            last_speaker = last_exchange["speaker"] if last_exchange else None
            last_content = last_exchange["content"].lower() if last_exchange else ""
            
            # Check if this is a conclusion question
            if self._is_conclusion_question(last_content):
                return self._give_fan_verdict(match_data)
                
            # If responding to stats expert
            if last_speaker == "Stats Expert":
                return self._respond_to_stats(last_content, match_data)
                
            # If responding to tactical analyst
            if last_speaker == "Tactical Analyst":
                return self._respond_to_tactics(last_content, match_data)
                
            # If responding to other fan
            if "Fan" in last_speaker:
                return self._respond_to_fan(last_content, match_data)
                
            # Default to sharing fan perspective
            return self._share_fan_perspective(match_data)
            
        except Exception as e:
            print(f"Error in FanAgent _generate_response: {e}")
            return f"As a {self.team} fan, I'm just hoping for the best here."
            
    def _update_emotional_state(self, match_data: Dict):
        """Update emotional state based on match situation"""
        match_info = match_data.get("match_info", {})
        score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
        
        my_score = score["home"] if self.is_home else score["away"]
        opponent_score = score["away"] if self.is_home else score["home"]
        
        if my_score > opponent_score:
            self.emotional_state = "elated"
            self.confidence_level = 0.8
        elif my_score < opponent_score:
            self.emotional_state = "disappointed"
            self.confidence_level = 0.3
        else:
            self.emotional_state = "neutral"
            self.confidence_level = 0.5
            
    def _respond_to_stats(self, stats_point: str, match_data: Dict) -> str:
        """Respond to statistical points from a fan perspective"""
        response = ""
        
        if "possession" in stats_point:
            response = self._comment_on_possession(match_data)
        elif "shots" in stats_point:
            response = self._comment_on_shooting(match_data)
        elif any(player in stats_point for player in self._get_team_players(match_data)):
            response = self._comment_on_player_stats(stats_point, match_data)
        else:
            response = self._get_general_stats_response(match_data)
            
        return self._add_fan_emotion(response)
        
    def _respond_to_tactics(self, tactical_point: str, match_data: Dict) -> str:
        """Respond to tactical points from a fan perspective"""
        response = ""
        
        if "formation" in tactical_point:
            response = self._comment_on_formation(match_data)
        elif "pressing" in tactical_point:
            response = self._comment_on_pressing(match_data)
        elif "attack" in tactical_point:
            response = self._comment_on_attack(match_data)
        else:
            response = self._get_general_tactical_response(match_data)
            
        return self._add_fan_emotion(response)
        
    def _respond_to_fan(self, fan_point: str, match_data: Dict) -> str:
        """Respond to other fan's point"""
        # If it's a rival fan
        if ("Home Fan" in self.name and "Away Fan" in fan_point) or \
           ("Away Fan" in self.name and "Home Fan" in fan_point):
            return self._give_rival_perspective(fan_point, match_data)
        else:
            return self._agree_with_fan(fan_point, match_data)
            
    def _share_fan_perspective(self, match_data: Dict) -> str:
        """Share a new fan perspective on the match"""
        # Choose an undiscussed aspect
        available_topics = self._get_available_topics()
        
        if not available_topics:
            self.discussed_topics.clear()
            available_topics = ["team_performance", "player_highlight", "atmosphere", "expectations"]
            
        topic = random.choice(available_topics)
        self.discussed_topics.add(topic)
        
        return self._generate_topic_response(topic, match_data)
        
    def _get_available_topics(self) -> List[str]:
        """Get list of available topics to discuss"""
        all_topics = ["team_performance", "player_highlight", "atmosphere", "expectations"]
        return [topic for topic in all_topics if topic not in self.discussed_topics]
        
    def _generate_topic_response(self, topic: str, match_data: Dict) -> str:
        """Generate response for a specific topic"""
        if topic == "team_performance":
            return self._comment_on_team_performance(match_data)
        elif topic == "player_highlight":
            return self._highlight_player_performance(match_data)
        elif topic == "atmosphere":
            return self._comment_on_atmosphere(match_data)
        else:  # expectations
            return self._share_expectations(match_data)
            
    def _comment_on_team_performance(self, match_data: Dict) -> str:
        """Comment on overall team performance"""
        match_info = match_data.get("match_info", {})
        score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
        
        my_score = score["home"] if self.is_home else score["away"]
        opponent_score = score["away"] if self.is_home else score["home"]
        
        if my_score > opponent_score:
            return f"This is exactly what we expect from {self.team}! The lads showed real character today."
        elif my_score < opponent_score:
            return f"Not the result we wanted, but {self.team} showed some promising moments."
        else:
            return f"A draw feels fair, but {self.team} had chances to win it."
            
    def _highlight_player_performance(self, match_data: Dict) -> str:
        """Highlight a specific player's performance"""
        players = self._get_team_players(match_data)
        if not players:
            return f"The whole {self.team} squad gave it their all today."
            
        player = random.choice(players)
        return random.choice(self.response_templates[self.emotional_state]).format(
            player=player,
            team=self.team
        )
        
    def _comment_on_atmosphere(self, match_data: Dict) -> str:
        """Comment on match atmosphere"""
        if self.is_home:
            return f"The atmosphere at our ground was electric today! The {self.team} faithful really got behind the team."
        else:
            return f"Our away support was fantastic as always. You could hear the {self.team} fans throughout the match!"
            
    def _share_expectations(self, match_data: Dict) -> str:
        """Share expectations for the team"""
        if self.emotional_state == "elated":
            return f"This is the kind of performance that shows what {self.team} is capable of!"
        elif self.emotional_state == "disappointed":
            return f"We know {self.team} can do better than this. We've seen it before."
        else:
            return f"There's definitely more to come from this {self.team} side."
            
    def _comment_on_possession(self, match_data: Dict) -> str:
        """Comment on possession statistics"""
        stats = match_data.get("match_statistics", {})
        my_stats = stats["home"] if self.is_home else stats["away"]
        
        possession = float(my_stats.get("Ball Possession", "0").rstrip("%"))
        
        if possession > 55:
            return f"That's what we like to see - {self.team} controlling the game!"
        elif possession < 45:
            return f"Sometimes you don't need the ball to be effective. {self.team} knows how to play smart!"
        else:
            return "It's not about possession, it's about what you do with it!"
            
    def _comment_on_shooting(self, match_data: Dict) -> str:
        """Comment on shooting statistics"""
        stats = match_data.get("match_statistics", {})
        my_stats = stats["home"] if self.is_home else stats["away"]
        
        shots = int(my_stats.get("Total Shots", 0))
        
        if shots > 15:
            return f"That's the {self.team} way - keep testing the keeper!"
        elif shots < 10:
            return "We need to be more adventurous in front of goal."
        else:
            return "Creating chances is good, but it's about taking them when they come!"
            
    def _comment_on_formation(self, match_data: Dict) -> str:
        """Comment on team formation"""
        return f"The setup looks good - it really plays to {self.team}'s strengths!"
        
    def _comment_on_pressing(self, match_data: Dict) -> str:
        """Comment on team pressing"""
        stats = match_data.get("match_statistics", {})
        my_stats = stats["home"] if self.is_home else stats["away"]
        
        duels_won = int(my_stats.get("Duels won", 0))
        
        if duels_won > 55:
            return f"Love seeing {self.team} getting stuck in! That's what the fans want to see!"
        else:
            return "We need to show more intensity in the challenges!"
            
    def _comment_on_attack(self, match_data: Dict) -> str:
        """Comment on attacking play"""
        match_info = match_data.get("match_info", {})
        score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
        
        my_score = score["home"] if self.is_home else score["away"]
        
        if my_score > 1:
            return f"This is the attacking football we love to see from {self.team}!"
        else:
            return "We've got the quality up front, just need to show it more consistently."
            
    def _get_general_stats_response(self, match_data: Dict) -> str:
        """Generate general response to statistics"""
        return f"Numbers are one thing, but what matters is how {self.team} performs on the pitch!"
        
    def _get_general_tactical_response(self, match_data: Dict) -> str:
        """Generate general response to tactical points"""
        return f"The tactics look good when {self.team} executes them properly!"
        
    def _give_rival_perspective(self, rival_point: str, match_data: Dict) -> str:
        """Respond to rival fan's point"""
        if self.emotional_state == "elated":
            return f"That's one way to look at it, but {self.team}'s performance speaks for itself!"
        elif self.emotional_state == "disappointed":
            return f"Fair point, but {self.team} has shown before that we can bounce back!"
        else:
            return "Let's focus on the football - both teams have their moments!"
            
    def _agree_with_fan(self, fan_point: str, match_data: Dict) -> str:
        """Agree with fellow fan's point"""
        return "Couldn't agree more! That's exactly what us fans have been saying!"
        
    def _add_fan_emotion(self, response: str) -> str:
        """Add emotional context to response"""
        if self.emotional_state == "elated":
            return response + " This is what being a fan is all about!"
        elif self.emotional_state == "disappointed":
            return response + " But we'll always support the team!"
        else:
            return response + " That's how we see it from the stands!"
            
    def _get_team_players(self, match_data: Dict) -> List[str]:
        """Get list of team players"""
        match_info = match_data.get("match_info", {})
        teams = match_info.get("teams", {})
        my_team = teams["home"] if self.is_home else teams["away"]
        
        players = []
        if "lineup" in my_team:
            players.extend([p.get("name", "") for p in my_team["lineup"]])
        if "substitutes" in my_team:
            players.extend([p.get("name", "") for p in my_team["substitutes"]])
            
        return [p for p in players if p]
        
    def _give_fan_verdict(self, match_data: Dict) -> str:
        """Give a fan's verdict on the match"""
        match_info = match_data.get("match_info", {})
        score = match_info.get("score", {}).get("fulltime", {"home": 0, "away": 0})
        
        my_score = score["home"] if self.is_home else score["away"]
        opponent_score = score["away"] if self.is_home else score["home"]
        
        verdict = f"From a {self.team} fan's perspective, "
        
        if my_score > opponent_score:
            verdict += "this was exactly the kind of performance we love to see! "
            verdict += "The team showed real character and deserved the win."
        elif my_score < opponent_score:
            verdict += "it's a disappointing result, but we've got to keep supporting the team. "
            verdict += "We know they can do better, and they'll show it next time."
        else:
            verdict += "there were positives and negatives to take from this. "
            verdict += "A draw feels fair, but we always want to see our team win."
            
        return verdict
    
    async def _analyze_match_outcome(self, match_data: Dict, current_state: Dict) -> Dict:
        """Analyze match outcome from fan perspective"""
        team_stats = match_data.get("statistics", {})
        match_info = match_data.get("match_info", {})
        
        # Get team performance metrics
        team_performance = await self._analyze_team_performance(team_stats)
        key_moments = await self._analyze_key_moments(match_data)
        
        # Get actual result
        score = match_info.get("score", {"home": 0, "away": 0})
        team_won = (self.is_home and score["home"] > score["away"]) or \
                  (not self.is_home and score["away"] > score["home"])
        
        return {
            "team_performance": team_performance,
            "key_moments": key_moments,
            "team_won": team_won,
            "emotional_response": await self._get_emotional_response(team_won, team_performance),
            "fan_perspective": await self._generate_fan_perspective(match_data)
        }
    
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