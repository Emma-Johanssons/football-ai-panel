from .base_agent import BaseAgent
from typing import Dict, List

class StatsAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Du är en expert på fotbollsstatistik och dataanalys.
        Din roll är att:
        - Analysera matchstatistik och trender
        - Tolka siffror och mönster
        - Ge insikter baserade på data
        - Förklara statistiska samband
        - Identifiera viktiga nyckeltal
        
        Var objektiv och basera dina analyser på fakta och siffror."""
        
        super().__init__(
            name="Statistiker",
            role="Dataanalytiker",
            system_prompt=system_prompt
        )
    
    def analyze(self, data: Dict) -> str:
        if not data:
            return "Jag har tyvärr ingen matchdata att analysera just nu."
            
        # Extract relevant data
        match_stats = data.get("match_statistics", {})
        home_team_stats = data.get("home_team_stats", {})
        away_team_stats = data.get("away_team_stats", {})
        h2h = data.get("h2h", [])
        
        # Create a detailed prompt for analysis
        prompt = f"""Analysera följande matchdata och ge statistiska insikter:

MATCHSTATISTIK:
{self._format_match_stats(match_stats)}

HEMMALAG STATISTIK:
{self._format_team_stats(home_team_stats)}

BORTALAG STATISTIK:
{self._format_team_stats(away_team_stats)}

H2H STATISTIK:
{self._format_h2h(h2h)}

Ge en detaljerad statistisk analys av matchen, med fokus på viktiga trender och mönster."""
        
        return self.get_response(prompt)
    
    def _format_match_stats(self, stats: Dict) -> str:
        if not stats:
            return "Ingen matchstatistik tillgänglig"
            
        return f"""Ballinnehav: {stats.get('possession', {})}
Skott: {stats.get('shots', {})}
Skott på mål: {stats.get('shots_on_target', {})}
Expected Goals: {stats.get('expected_goals', {})}
Passningar: {stats.get('passes', {})}
Passningsprocent: {stats.get('passes_accuracy', {})}%"""
    
    def _format_team_stats(self, stats: Dict) -> str:
        if not stats:
            return "Ingen lagstatistik tillgänglig"
            
        return f"""Form: {stats.get('form', '')}
Mål: {stats.get('goals', {}).get('for', {}).get('total', {})}
Insläppta mål: {stats.get('goals', {}).get('against', {}).get('total', {})}
Clean Sheets: {stats.get('clean_sheet', {}).get('total', {})}
Failed to Score: {stats.get('failed_to_score', {}).get('total', {})}"""
    
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
