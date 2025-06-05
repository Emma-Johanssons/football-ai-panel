from typing import Dict, Optional
from services.match_service import MatchService
from services.football_stats_service import FootballStatsService
from services.rag_utils import rag_retrieve
import json

class MatchDataStore:
    _instance = None
    _match_data = {}
    _knowledge_base = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MatchDataStore, cls).__new__(cls)
            cls._instance.match_service = MatchService()
            cls._instance.stats_service = FootballStatsService()
        return cls._instance
    
    def load_match_data(self, match_id: str) -> bool:
        """Load and store match data for a specific match ID"""
        try:
            # Fetch comprehensive match data
            match_data = self.match_service.get_match_data(match_id)
            if not match_data:
                print(f"❌ No match data found for ID: {match_id}")
                return False
                
            # Fetch detailed statistics
            stats = self.stats_service.get_match_statistics(match_id)
            if stats:
                match_data["statistics"] = stats
                print(f"✅ Successfully added detailed statistics")
            else:
                print(f"⚠️ No statistics found for match ID: {match_id}")
            
            # Store the compiled data
            self._match_data[match_id] = match_data
            print(f"✅ Successfully loaded match data for ID: {match_id}")
            
            # Print data structure for debugging
            print(f"Match data structure: {json.dumps(match_data, indent=2)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading match data: {e}")
            return False
    
    def get_match_data(self, match_id: str) -> Optional[Dict]:
        """Get stored match data for a specific match ID"""
        data = self._match_data.get(match_id)
        if not data:
            print(f"⚠️ No data found for match ID: {match_id}")
            print(f"Available match IDs: {list(self._match_data.keys())}")
        return data
    
    def get_football_knowledge(self, match_id: str, topic: str) -> Dict:
        """Get football knowledge for a specific topic"""
        try:
            # Check if we have cached knowledge
            cache_key = f"{match_id}_{topic}"
            if cache_key in self._knowledge_base:
                return self._knowledge_base[cache_key]
            
            # Get knowledge from RAG
            rag_response = rag_retrieve(match_id, f"football rules and statistics about {topic}")
            
            # Structure the response
            if isinstance(rag_response, tuple):
                stats, rules, tactics, historical = rag_response
            else:
                stats = rag_response
                rules = []
                tactics = []
                historical = []
            
            knowledge = {
                "stats": stats,
                "rules": rules,
                "tactics": tactics,
                "historical": historical,
                "context": f"Knowledge about {topic} for match {match_id}"
            }
            
            # Cache the knowledge
            self._knowledge_base[cache_key] = knowledge
            return knowledge
            
        except Exception as e:
            print(f"Error getting football knowledge: {e}")
            return {
                "stats": [],
                "rules": [],
                "tactics": [],
                "historical": [],
                "context": ""
            }
    
    def clear_data(self, match_id: str = None):
        """Clear stored data for a specific match or all matches"""
        if match_id:
            self._match_data.pop(match_id, None)
            # Clear related knowledge
            self._knowledge_base = {k: v for k, v in self._knowledge_base.items() 
                                  if not k.startswith(f"{match_id}_")}
        else:
            self._match_data.clear()
            self._knowledge_base.clear() 