"""
RAG (Retrieval Augmented Generation) service for enhancing agent responses with learned knowledge
"""

import os
import json
from typing import List, Dict
import chromadb
from chromadb.config import Settings
import openai

class RAGService:
    def __init__(self):
        # Initialize ChromaDB for vector storage
        self.client = chromadb.Client(Settings(
            persist_directory="backend/data/chroma_db"
        ))
        
        # Create collections for different types of knowledge
        self.discussion_collection = self.client.get_or_create_collection("football_discussions")
        self.match_collection = self.client.get_or_create_collection("match_history")
        self.tactics_collection = self.client.get_or_create_collection("football_tactics")
        
    def add_to_knowledge(self, text: str, metadata: Dict, collection_name: str = "football_discussions"):
        """Add new knowledge to the appropriate collection"""
        collection = self.client.get_collection(collection_name)
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[f"{collection_name}_{len(collection.get()['ids']) + 1}"]
        )
    
    def learn_from_discussion(self, discussion_segments: List[Dict]):
        """Learn from a panel discussion by storing relevant segments"""
        for segment in discussion_segments:
            metadata = {
                "speaker_role": segment["speaker"],
                "context": "panel_discussion",
                "timestamp": segment.get("timestamp", "")
            }
            self.add_to_knowledge(
                text=segment["content"],
                metadata=metadata
            )
    
    def learn_from_match(self, match_data: Dict):
        """Store match data for future reference"""
        match_summary = json.dumps(match_data)
        metadata = {
            "match_id": match_data.get("fixture", {}).get("id", ""),
            "teams": f"{match_data['teams']['home']['name']} vs {match_data['teams']['away']['name']}",
            "date": match_data.get("fixture", {}).get("date", "")
        }
        self.add_to_knowledge(
            text=match_summary,
            metadata=metadata,
            collection_name="match_history"
        )
    
    def get_relevant_knowledge(self, query: str, role: str, k: int = 3) -> List[str]:
        """Retrieve relevant knowledge based on query and role"""
        # Search across all collections with role-specific weighting
        results = []
        
        # Get from discussions
        discussion_results = self.discussion_collection.query(
            query_texts=[query],
            n_results=k,
            where={"speaker_role": role} if role else None
        )
        if discussion_results["documents"]:
            results.extend(discussion_results["documents"][0])
        
        # Get from match history
        match_results = self.match_collection.query(
            query_texts=[query],
            n_results=k
        )
        if match_results["documents"]:
            results.extend(match_results["documents"][0])
        
        # Get from tactics (especially for coach)
        if role == "Football Coach":
            tactics_results = self.tactics_collection.query(
                query_texts=[query],
                n_results=k
            )
            if tactics_results["documents"]:
                results.extend(tactics_results["documents"][0])
        
        return results
    
    def enhance_response(self, prompt: str, role: str, context: Dict = None) -> str:
        """Enhance an agent's response using learned knowledge"""
        # Get relevant knowledge
        knowledge = self.get_relevant_knowledge(prompt, role)
        
        # Create an enhanced prompt with retrieved knowledge
        enhanced_prompt = f"""Based on the following relevant knowledge and your role as {role}, respond to: {prompt}

Relevant Knowledge:
{chr(10).join(knowledge)}

Additional Context:
{json.dumps(context) if context else 'No additional context'}

Remember to:
1. Use the knowledge naturally, don't just repeat it
2. Maintain your unique perspective and personality
3. Be ready to disagree or agree with others based on your role
4. Keep your emotional style (especially for fans)
"""
        
        # Generate enhanced response
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are a {role} in a football panel discussion."},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content 