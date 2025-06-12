"""
Learning agent that analyzes football panel discussions and extracts personality traits
"""
from data_collection.youtube_collector import YouTubeCollector
from typing import Dict, List
import json
import os
from datetime import datetime
import numpy as np
import random

class LearningAgent:
    def __init__(self, collector: YouTubeCollector):
        self.collector = collector
        self.personalities_dir = "learning_data/personalities"
        os.makedirs(self.personalities_dir, exist_ok=True)
        
        # Role-specific trait indicators
        self.trait_indicators = {
            'host': {
                'detail_focus': {
                    'high': ['analysis', 'breakdown', 'detailed', 'comprehensive', 'examining'],
                    'low': ['highlights', 'quick', 'brief', 'overview', 'recap']
                },
                'emotion_level': {
                    'high': ['incredible', 'amazing', 'shocking', 'dramatic', 'controversial'],
                    'low': ['discussing', 'presenting', 'reviewing', 'looking at', 'covering']
                },
                'topic_expertise': {
                    'high': ['tactical', 'analysis', 'statistics', 'transfer', 'history'],
                    'low': ['reaction', 'news', 'update', 'chat', 'discussion']
                }
            },
            'coach': {
                'detail_focus': {
                    'high': ['tactical', 'formation', 'system', 'positioning', 'movement'],
                    'low': ['style', 'approach', 'gameplan', 'setup', 'strategy']
                },
                'emotion_level': {
                    'high': ['genius', 'masterclass', 'brilliant', 'revolutionary', 'innovative'],
                    'low': ['analysis', 'explanation', 'breakdown', 'examining', 'studying']
                },
                'topic_expertise': {
                    'high': ['tactics', 'formation', 'pressing', 'transition', 'buildup'],
                    'low': ['match', 'game', 'performance', 'playing', 'result']
                }
            },
            'stats': {
                'detail_focus': {
                    'high': ['statistics', 'data', 'numbers', 'metrics', 'analysis'],
                    'low': ['performance', 'comparison', 'rating', 'ranking', 'level']
                },
                'emotion_level': {
                    'high': ['incredible', 'unbelievable', 'shocking', 'amazing', 'stunning'],
                    'low': ['comparing', 'analyzing', 'measuring', 'evaluating', 'assessing']
                },
                'topic_expertise': {
                    'high': ['xG', 'PPDA', 'progressive passes', 'expected goals', 'possession'],
                    'low': ['stats', 'numbers', 'performance', 'comparison', 'rating']
                }
            }
        }

    def get_role_from_name(self, name: str) -> str:
        """Map personality name to their role"""
        name = name.lower()
        if name in ['joe devine', 'patrick van straaten']:
            return 'host'
        elif name in ['alex stewart', 'coach matt']:
            return 'coach'
        elif name in ['joe thomlinson', 'dylan']:
            return 'stats'
        return 'host'  # default

    async def analyze_content(self, role: str, content: str) -> Dict[str, float]:
        """Analyze content for personality traits based on role"""
        traits = {
            'detail_focus': 0.0,
            'emotion_level': 0.0,
            'topic_expertise': 0.0
        }
        
        content = content.lower()
        indicators = self.trait_indicators[role]
        
        # Analyze each trait
        for trait, categories in indicators.items():
            high_count = sum(content.count(word) for word in categories['high'])
            low_count = sum(content.count(word) for word in categories['low'])
            total_count = high_count + low_count
            
            if total_count > 0:
                # Calculate weighted score between 0.2 and 0.9
                score = (high_count / total_count) * 0.7 + 0.2
                
                # Add some randomness based on content length
                variance = min(len(content) / 5000, 0.1)  # max 0.1 variance
                score += random.uniform(-variance, variance)
                
                # Ensure score stays within bounds
                traits[trait] = max(0.2, min(0.9, score))
            else:
                # Default values based on role
                if role == 'host':
                    traits[trait] = 0.6  # balanced
                elif role == 'coach':
                    traits[trait] = 0.8 if trait in ['detail_focus', 'topic_expertise'] else 0.4
                else:  # stats
                    traits[trait] = 0.9 if trait == 'detail_focus' else 0.5

        return traits

    async def learn_from_shows(self, max_videos: int = 5):
        """Learn from football panel shows"""
        print("🎓 Learning from football panel shows...")
        
        # Collect data from channels
        channel_data = self.collector.collect_all_channels(max_videos)
        
        for channel_name, channel_results in channel_data.items():
            print(f"\nAnalyzing {channel_name}...")
            
            # Get channel panelists
            panelists = self.collector.channels[channel_name]["panelists"]
            
            for panelist in panelists:
                await self.analyze_panelist(channel_name, panelist, channel_results)
                    
    async def analyze_panelist(self, channel: str, name: str, results: List[Dict]):
        """Analyze a specific panelist's style and personality"""
        print(f"Analyzing {name} from {channel}...")
        
        # Get the role for this panelist
        role = self.get_role_from_name(name)
        
        # Analyze both titles and descriptions
        all_traits = []
        for result in results:
            metadata_file = os.path.join(self.collector.raw_data_dir, channel, f"{result['video_id']}_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    video = metadata['video']
                    content = f"{video['title']} {video['description']}"
                    traits = await self.analyze_content(role, content)
                    all_traits.append(traits)
        
        # Average the traits across all videos
        if all_traits:
            final_traits = {}
            for trait in ['detail_focus', 'emotion_level', 'topic_expertise']:
                values = [t[trait] for t in all_traits]
                final_traits[trait] = float(np.mean(values))
        else:
            # Default traits if no videos found
            final_traits = await self.analyze_content(role, "")
        
        # Save personality profile
        profile = {
            'name': name,
            'channel': channel,
            'role': role,
            'traits': final_traits,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to file
        profile_file = os.path.join(self.personalities_dir, f"{name.lower().replace(' ', '_')}.json")
        os.makedirs(os.path.dirname(profile_file), exist_ok=True)
        
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
            
        print(f"Saved personality profile for {name}")
        return profile

async def main():
    """Main function to run learning agent"""
    collector = YouTubeCollector()
    agent = LearningAgent(collector)
    await agent.learn_from_shows()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 