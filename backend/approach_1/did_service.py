import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

class DIDService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("DID_API_KEY")
        if not self.api_key:
            raise ValueError("DID_API_KEY not found in environment variables")
            
    def get_headers(self) -> Dict[str, str]:
        """Get headers for D-ID API requests"""
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def create_agent(self, role: str, avatar_id: str, voice_id: str) -> Dict:
        """Create a D-ID agent with the specified avatar and voice"""
        response = requests.post(
            "https://api.d-id.com/agents",
            headers=self.get_headers(),
            json={
                "presenter": {
                    "type": "talk",
                    "source_url": f"https://d-id-talks-prod.s3.us-west-2.amazonaws.com/api~talks~{avatar_id}/image.jpg",
                    "voice": {
                        "type": "microsoft",
                        "voice_id": voice_id
                    }
                },
                "llm": {
                    "type": "openai",
                    "provider": "openai",
                    "model": "gpt-4",
                    "instructions": f"You are a {role} in a football analysis panel."
                },
                "preview_name": f"Football {role.capitalize()}"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create D-ID agent: {response.text}")
            
        return response.json()
        
    def create_chat(self, agent_id: str) -> Dict:
        """Create a new chat session with an agent"""
        response = requests.post(
            f"https://api.d-id.com/agents/{agent_id}/chat",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create chat: {response.text}")
            
        return response.json()
        
    def send_message(self, agent_id: str, chat_id: str, message: str) -> Dict:
        """Send a message to an agent in a chat session"""
        response = requests.post(
            f"https://api.d-id.com/agents/{agent_id}/chat/{chat_id}",
            headers=self.get_headers(),
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.text}")
            
        return response.json()
        
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get the status of an agent"""
        response = requests.get(
            f"https://api.d-id.com/agents/{agent_id}",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get agent status: {response.text}")
            
        return response.json()
        
    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent"""
        response = requests.delete(
            f"https://api.d-id.com/agents/{agent_id}",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to delete agent: {response.text}") 