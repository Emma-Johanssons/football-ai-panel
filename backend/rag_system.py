"""
Retrieval Augmented Generation system for football knowledge
"""
import os
from typing import List, Dict
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from datetime import datetime
import json
from langchain_community.embeddings import OpenAIEmbeddings
import chromadb

class FootballKnowledgeRAG:
    def __init__(self):
        self.current_season = "2023/2024"
        self.last_update = None
        self.team_rosters = {}
        self.transfer_history = {}
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db_path = "data/chroma_db"
        # Ensure the directory exists
        os.makedirs(self.db_path, exist_ok=True)
        self.initialize_db()
        
    def initialize_db(self):
        """Initialize the vector database"""
        try:
            # Create ChromaDB client with clean persistence
            client = chromadb.PersistentClient(path=self.db_path)
            
            # Create or get collection
            self.db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings,
                client=client,
                collection_name="football_knowledge"
            )
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Fallback to in-memory database if persistence fails
            self.db = Chroma(
                embedding_function=self.embeddings,
                collection_name="football_knowledge"
            )
    
    def validate_player_mention(self, text: str, team_id: str) -> bool:
        """Check if mentioned player is currently in the team"""
        if team_id not in self.team_rosters:
            return True  # If we don't have roster data, don't filter
            
        current_roster = self.team_rosters[team_id]
        # Extract player names from text and check against roster
        # TODO: Implement player name extraction
        return True
        
    def update_team_roster(self, team_id: str, roster: List[Dict]):
        """Update current roster for a team"""
        self.team_rosters[team_id] = roster
        self.last_update = datetime.now()
        
    def query(self, query: str, role: str = None, team_id: str = None) -> List[Dict]:
        """Get relevant context, filtering out outdated player information"""
        results = self.db.similarity_search(query, k=5)
        
        # Filter results to remove mentions of transferred players
        filtered_results = []
        for result in results:
            content = result.page_content
            # Only include if players mentioned are current
            if team_id is None or self.validate_player_mention(content, team_id):
                filtered_results.append({"content": content, "source": result.metadata.get("source", "unknown")})
                
        return filtered_results
    
    def add_to_knowledge(self, text: str, metadata: Dict):
        """Add new knowledge to the RAG system"""
        # Validate information is current before adding
        if self.is_current_information(text, metadata):
            # Add to vector store
            self.db.add_texts(
                texts=[text],
                metadatas=[metadata]
            )
            
            # Persist changes
            self.db.persist()
            
    def is_current_information(self, text: str, metadata: Dict) -> bool:
        """Check if information is from current season"""
        # Extract date/season information
        # Compare against current_season
        return True  # TODO: Implement proper validation
        
    def learn_from_match(self, match_data: Dict):
        """Learn from match data, ensuring information is current"""
        if not match_data:
            return
            
        # Update team rosters
        for team in ["home", "away"]:
            if "teams" in match_data.get("match_info", {}):
                team_data = match_data["match_info"]["teams"][team]
                team_id = team_data.get("id")
                if team_id and "players" in team_data:
                    self.update_team_roster(team_id, team_data["players"])
                    
        # Add match events with timestamp
        events = match_data.get("events", [])
        for event in events:
            self.add_to_knowledge(
                text=str(event),
                metadata={
                    "timestamp": event.get("time"),
                    "match_id": match_data.get("match_info", {}).get("id"),
                    "season": self.current_season
                }
            )
        
        # Basic match summary
        summary = (
            f"Match between {team_data.get('name')} and {team_data.get('opponent', {}).get('name')}."
            f"Score: {match_data.get('score', {}).get('home', 0)}-{match_data.get('score', {}).get('away', 0)}."
        )
        self.add_to_knowledge(summary, {"type": "match_summary"})
        
        # Team statistics
        stats = match_data.get("team_statistics", {})
        for team_type, team_stats in stats.items():
            if team_stats:
                stats_text = f"{team_type.upper()} TEAM STATS:\n"
                stats_text += json.dumps(team_stats, indent=2)
                self.add_to_knowledge(
                    stats_text,
                    {"type": "team_statistics", "team_type": team_type}
                )
        
        # Coach data (formations, tactics)
        coach_data = match_data.get("coach_data", {})
        if coach_data:
            tactics_text = "TACTICAL ANALYSIS:\n"
            tactics_text += json.dumps(coach_data, indent=2)
            self.add_to_knowledge(
                tactics_text,
                {"type": "tactical_analysis"}
            )
        
        # Fan perspective (head-to-head history, team form)
        fan_data = match_data.get("fan_data", {})
        if fan_data:
            fan_text = "FAN PERSPECTIVE:\n"
            fan_text += f"Head-to-head history: {len(fan_data.get('h2h', []))} matches\n"
            fan_text += f"Team form: {fan_data.get('team_form', 'N/A')}"
            self.add_to_knowledge(
                fan_text,
                {"type": "fan_perspective"}
            )
        
        # Add raw match data for future reference
        self.add_to_knowledge(
            json.dumps(match_data, indent=2),
            {"type": "raw_match_data"}
        ) 