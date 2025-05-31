from abc import ABC, abstractmethod
from openai import OpenAI
from typing import List, Dict

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = OpenAI()
        
    def get_response(self, message: str, context: List[Dict] = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        return response.choices[0].message.content
    
    @abstractmethod
    def analyze(self, data: Dict) -> str:
        """Analyze the provided data and return a response"""
        pass
