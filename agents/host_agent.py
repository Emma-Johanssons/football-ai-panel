from .base_agent import BaseAgent
from typing import Dict, List

class HostAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Du är en erfaren fotbollskommentator och programledare.
        Din roll är att:
        - Ledda diskussionen mellan panelmedlemmarna
        - Ställa relevanta och insiktsfulla frågor
        - Byta ämne på ett naturligt sätt
        - Hålla koll på tiden och tempot
        - Sammanfatta viktiga punkter
        
        Var professionell men engagerad, och se till att alla panelmedlemmar får komma till tals."""
        
        super().__init__(
            name="Programledare",
            role="Moderator",
            system_prompt=system_prompt
        )
    
    def analyze(self, data: Dict) -> str:
        if not data:
            return "Jag har tyvärr ingen matchdata att analysera just nu."
            
        # Extract panel context
        current_topic = data.get("current_topic", "")
        time_elapsed = data.get("time_elapsed", "")
        last_speaker = data.get("last_speaker", "")
        key_points = data.get("key_points", [])
        panel_members = data.get("panel_members", [])
        
        # Create a detailed prompt for analysis
        prompt = f"""Som programledare, ledda diskussionen baserat på följande kontext:

AKTUELLT ÄMNE: {current_topic}
TID FÖRFLUTEN: {time_elapsed}
SENASTE TALARE: {last_speaker}
PANELMEDLEMMAR: {', '.join(panel_members)}

Viktiga punkter från panelen:
{self._format_key_points(key_points)}

Ge en naturlig övergång eller fråga för att fortsätta diskussionen. 
Se till att alla panelmedlemmar får komma till tals och att diskussionen flödar naturligt."""
        
        return self.get_response(prompt)
    
    def _format_key_points(self, points: List) -> str:
        if not points:
            return "Inga viktiga punkter har tagits upp än."
            
        return "\n".join([f"- {point}" for point in points])
    
    def transition_to_topic(self, current_topic: str, new_topic: str) -> str:
        """Create a smooth transition between topics"""
        prompt = f"""Vi har just diskuterat {current_topic}. 
        Skapa en naturlig övergång till ämnet {new_topic}."""
        
        return self.get_response(prompt)
    
    def summarize_discussion(self, key_points: List) -> str:
        """Summarize the main points of the discussion"""
        prompt = f"""Sammanfatta följande viktiga punkter från diskussionen:
        {self._format_key_points(key_points)}
        
        Ge en kort men sammanfattande kommentar som knyter ihop diskussionen."""
        
        return self.get_response(prompt)
