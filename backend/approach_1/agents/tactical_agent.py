from .base_agent import BaseAgent

class TacticalAgent(BaseAgent):
    def __init__(self, match_id: str = None):
        name = "Tactical Analyst"
        role = "Tactical Analyst"
        system_prompt = """You are a football tactical analyst and coach. Your job is to:
1. Analyze team formations and their effectiveness
2. Identify key tactical decisions and their impact
3. Evaluate player roles and positioning
4. Assess team strategies and adaptations
5. Always mention specific player names from the actual match data
6. Only mention formation numbers once, then use phrases like "this setup" or "their system"
7. Focus on how individual players execute their roles

Focus on tactical aspects and coaching decisions, always tied to specific players from the match."""
        
        personality = "analytical and insightful"
        super().__init__(name=name, role=role, system_prompt=system_prompt, personality=personality, match_id=match_id)
        
        # Track mentioned formations to avoid repetition
        self.mentioned_formations = {
            "home": False,
            "away": False
        }
        
    def _get_player_by_role(self, match_data: dict, team: str, role: str) -> tuple:
        """Get player info by their role"""
        try:
            # Get player stats from match data
            player_stats = match_data.get("match_info", {}).get("player_stats", {}).get(team, [])
            if not player_stats:
                return None, None
                
            # Find players matching the role
            role_players = [p for p in player_stats if p.get("position") == role]
            if not role_players:
                return None, None
                
            # Find the player with best rating in that role
            best_player = None
            best_rating = 0
            
            for player in role_players:
                stats = player.get("statistics", [{}])[0]  # Get first statistics entry
                try:
                    rating = float(stats.get("games", {}).get("rating", 0))
                except (ValueError, TypeError):
                    rating = 0
                    
                if rating > best_rating:
                    best_rating = rating
                    best_player = player.get("name")
                    
            return best_player, best_rating
            
        except Exception as e:
            print(f"Error getting player by role: {e}")
            return None, None
            
    def _get_formation_reference(self, team: str, formation: str) -> str:
        """Get appropriate formation reference based on whether it's been mentioned"""
        if not self.mentioned_formations[team]:
            self.mentioned_formations[team] = True
            return formation
        return "this setup"
            
    async def analyze_match(self, match_data: dict) -> str:
        """Analyze match from a tactical/coaching perspective"""
        try:
            # Get team info
            teams = match_data.get("match_info", {}).get("teams", {})
            formations = match_data.get("details", {}).get("formations", {})
            
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            home_formation = self._get_formation_reference("home", formations.get("home", "their formation"))
            away_formation = self._get_formation_reference("away", formations.get("away", "their setup"))
            
            # Get key players from different positions with their ratings
            mid_name, mid_rating = self._get_player_by_role(match_data, "home", "M")
            def_name, def_rating = self._get_player_by_role(match_data, "home", "D")
            fwd_name, fwd_rating = self._get_player_by_role(match_data, "home", "F")
            
            # Build analysis based on available player data
            analysis = f"{home_team} set up in {home_formation}"
            
            if mid_name and def_name and fwd_name:
                analysis += (
                    f", with {def_name} (rating {def_rating:.1f}) organizing the defense, "
                    f"{mid_name} (rating {mid_rating:.1f}) controlling the midfield, and "
                    f"{fwd_name} (rating {fwd_rating:.1f}) leading the attack. "
                )
            else:
                analysis += ". "
                
            analysis += f"{away_team} responded with {away_formation}"
            
            # Get key away team players
            away_mid_name, away_mid_rating = self._get_player_by_role(match_data, "away", "M")
            away_def_name, away_def_rating = self._get_player_by_role(match_data, "away", "D")
            
            if away_mid_name and away_def_name:
                analysis += (
                    f", with {away_mid_name} (rating {away_mid_rating:.1f}) orchestrating their play "
                    f"and {away_def_name} (rating {away_def_rating:.1f}) anchoring the defense."
                )
            else:
                analysis += "."
                
            return analysis
            
        except Exception as e:
            print(f"Error in tactical analysis: {e}")
            return self.get_fallback_response()
            
    def _analyze_tactical_changes(self, match_data: dict) -> str:
        """Analyze tactical changes and their impact"""
        try:
            events = match_data.get("match_info", {}).get("events", [])
            teams = match_data.get("match_info", {}).get("teams", {})
            
            home_team = teams.get("home", {}).get("name", "Home Team")
            away_team = teams.get("away", {}).get("name", "Away Team")
            
            # Find substitutions
            subs = [e for e in events if e.get("type") == "substitution"]
            
            if subs:
                # Get first substitution details
                first_sub = subs[0]
                player_in = first_sub.get("player", {}).get("name")
                player_out = first_sub.get("player", {}).get("name")
                team_name = first_sub.get("team", {}).get("name", home_team)
                minute = first_sub.get("time", {}).get("elapsed", "")
                
                if player_in and player_out and minute:
                    analysis = (
                        f"{team_name} made a tactical adjustment in the {minute}th minute by replacing "
                        f"{player_out} with {player_in}, which impacted their approach."
                    )
                else:
                    analysis = f"Both teams made tactical adjustments throughout the match."
            else:
                analysis = "Both teams maintained their tactical approach throughout the match."
                
            return analysis
            
        except Exception as e:
            print(f"Error analyzing tactical changes: {e}")
            return ""
            
    def _analyze_player_performances(self, match_data: dict) -> str:
        """Analyze individual player performances within tactical system"""
        try:
            teams = match_data.get("match_info", {}).get("teams", {})
            home_team = teams.get("home", {}).get("name", "Home Team")
            
            # Get key performers in different positions with ratings
            def_name, def_rating = self._get_player_by_role(match_data, "home", "D")
            mid_name, mid_rating = self._get_player_by_role(match_data, "home", "M")
            fwd_name, fwd_rating = self._get_player_by_role(match_data, "home", "F")
            
            if def_name and mid_name and fwd_name:
                analysis = (
                    f"Looking at individual roles, {def_name} was solid in defense with a {def_rating:.1f} rating, "
                    f"while {mid_name} dictated the tempo in midfield earning a {mid_rating:.1f}. "
                    f"Up front, {fwd_name} provided the attacking threat with a performance rated {fwd_rating:.1f}."
                )
            else:
                analysis = f"Players across all positions executed their tactical roles effectively."
                
            return analysis
            
        except Exception as e:
            print(f"Error analyzing player performances: {e}")
            return "" 