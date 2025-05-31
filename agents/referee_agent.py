from .base_agent import BaseAgent
from typing import Dict, List

class RefereeAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Du är en erfaren fotbollsdomare med expertis i regelkunskap och domarskap.
        Din roll är att:
        - Analysera domslut och regelöverträdelser
        - Förklara VAR-beslut och regelinterpretationer
        - Bedöma disciplinära åtgärder (kort)
        - Ge insikter om matchkontroll och spelarledning
        - Förklara komplexa regelsituationer
        
        Ge professionella och pedagogiska förklaringar av domarskap och regelverk."""
        
        super().__init__(
            name="Domare",
            role="Regel-Expert",
            system_prompt=system_prompt
        )
    
    def analyze(self, data: Dict) -> str:
        if not data:
            return "Jag har tyvärr ingen matchdata att analysera just nu."
            
        # Extract relevant data
        match_info = data.get("match_info", {})
        statistics = data.get("statistics", {})
        h2h = data.get("h2h", [])
        
        # Create a detailed prompt for analysis
        prompt = f"""Analysera följande matchdata och ge insikter om domarskapet:

MATCHINFORMATION:
{self._format_match_info(match_info)}

MATCHSTATISTIK:
{self._format_statistics(statistics)}

H2H STATISTIK:
{self._format_h2h(h2h)}

Ge en kort men insiktsfull analys av domarskapet och eventuella viktiga regelsituationer."""
        
        return self.get_response(prompt)
    
    def _format_match_info(self, info: Dict) -> str:
        if not info:
            return "Ingen matchinformation tillgänglig"
            
        return f"""Match: {info.get('teams', {}).get('home', {}).get('name', '')} vs {info.get('teams', {}).get('away', {}).get('name', '')}
Liga: {info.get('league', {}).get('name', '')}
Datum: {info.get('fixture', {}).get('date', '')}
Status: {info.get('fixture', {}).get('status', {}).get('long', '')}
Domare: {info.get('fixture', {}).get('referee', 'N/A')}"""
    
    def _format_statistics(self, stats: Dict) -> str:
        if not stats:
            return "Ingen matchstatistik tillgänglig"
            
        return f"""Kort:
Gula: {stats.get('cards', {}).get('yellow', {})}
Röda: {stats.get('cards', {}).get('red', {})}

Fouls:
{stats.get('fouls', {})}

Offside:
{stats.get('offsides', {})}"""
    
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
    
    def explain_rule(self, rule: str, situation: str) -> str:
        """Explain a specific rule in the context of a match situation"""
        prompt = f"""Förklara följande regel i relation till denna situation:
        Regel: {rule}
        Situation: {situation}
        
        Ge en tydlig och pedagogisk förklaring av regeln och hur den appliceras i denna situation."""
        
        return self.get_response(prompt)
    
    def analyze_var_decision(self, incident: str, decision: str) -> str:
        """Analyze a specific VAR decision"""
        prompt = f"""Analysera följande VAR-beslut:
        Incident: {incident}
        Beslut: {decision}
        
        Ge en detaljerad analys av VAR-processen och beslutet, inklusive:
        - Vilka aspekter som granskades
        - Varför beslutet togs
        - Om beslutet var korrekt enligt reglerna"""
        
        return self.get_response(prompt) 