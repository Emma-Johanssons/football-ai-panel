from .base_agent import BaseAgent
from typing import Dict, List

class FanAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Du är en passionerad fotbollsfan med djup känsla för sporten.
        Din roll är att:
        - Ge emotionella och engagerade kommentarer
        - Beskriva matchstämning och atmosfär
        - Reagera på viktiga matchhändelser
        - Visa laglojalitet och passion
        - Ge en fans perspektiv på matchen
        
        Var engagerad och entusiastisk, men respektfull. Använd gärna fotbollsslang och uttryck som en riktig supporter skulle använda."""
        
        super().__init__(
            name="Supporter",
            role="Fans Röst",
            system_prompt=system_prompt
        )
    
    def analyze(self, data: Dict) -> str:
        if not data:
            return "Jag har tyvärr ingen matchdata att analysera just nu."
            
        # Extract relevant data
        match_info = data.get("match_info", {})
        statistics = data.get("statistics", {})
        h2h = data.get("h2h", [])
        team_stats = data.get("team_stats", {})
        recent_form = data.get("recent_form", {})
        
        # Create a detailed prompt for analysis
        prompt = f"""Som en passionerad supporter, ge dina tankar om följande:

MATCHINFORMATION:
{self._format_match_info(match_info)}

MATCHSTATISTIK:
{self._format_statistics(statistics)}

LAGSTATISTIK:
{self._format_team_stats(team_stats)}

SENASTE FORM:
{self._format_recent_form(recent_form)}

H2H STATISTIK:
{self._format_h2h(h2h)}

Ge en engagerad och passionerad analys från en supporters perspektiv!"""
        
        return self.get_response(prompt)
    
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
    
    def _format_team_stats(self, stats: Dict) -> str:
        if not stats:
            return "Ingen lagstatistik tillgänglig"
            
        home = stats.get("home", {})
        away = stats.get("away", {})
        
        return f"""HEMMALAG:
Form: {home.get('form', '')}
Mål: {home.get('goals', {}).get('for', {}).get('total', {})}
Insläppta mål: {home.get('goals', {}).get('against', {}).get('total', {})}

BORTALAG:
Form: {away.get('form', '')}
Mål: {away.get('goals', {}).get('for', {}).get('total', {})}
Insläppta mål: {away.get('goals', {}).get('against', {}).get('total', {})}"""
    
    def _format_recent_form(self, form: Dict) -> str:
        if not form:
            return "Ingen formstatistik tillgänglig"
            
        home = form.get("home", [])
        away = form.get("away", [])
        
        return f"""HEMMALAG SENASTE MATCHER:
{self._format_matches(home)}

BORTALAG SENASTE MATCHER:
{self._format_matches(away)}"""
    
    def _format_matches(self, matches: List) -> str:
        if not matches:
            return "Inga matcher tillgängliga"
            
        return "\n".join([
            f"{match.get('teams', {}).get('home', {}).get('name', '')} vs {match.get('teams', {}).get('away', {}).get('name', '')}: "
            f"{match.get('goals', {}).get('home', '')}-{match.get('goals', {}).get('away', '')} "
            f"({match.get('fixture', {}).get('status', {}).get('long', '')})"
            for match in matches[:5]  # Show last 5 matches
        ])
    
    def _format_h2h(self, h2h: List) -> str:
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