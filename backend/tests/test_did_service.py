import asyncio
from services.did_service import DIDService
from agents.avatar_mapping import AVATAR_MAPPINGS

async def test_did_service():
    """Test the D-ID service with our avatars"""
    try:
        # Initialize D-ID service
        did_service = DIDService()
        
        # Test creating agents for each role
        agents = {}
        for role, config in AVATAR_MAPPINGS.items():
            print(f"\n🤖 Creating {role} agent...")
            agent = did_service.create_agent(
                role=role,
                avatar_id=config["id"],
                voice_id=config["voice_id"]
            )
            agents[role] = agent
            print(f"✅ Created {role} agent with ID: {agent['id']}")
            
            # Create a chat session
            chat = did_service.create_chat(agent['id'])
            print(f"✅ Created chat session with ID: {chat['id']}")
            
            # Send a test message
            message = f"Hello, I am the {role} in this football panel. What do you think about the match?"
            response = did_service.send_message(agent['id'], chat['id'], message)
            print(f"✅ Got response from {role}: {response}")
            
        print("\n🎉 All agents created and tested successfully!")
        
    except Exception as e:
        print(f"❌ Error testing D-ID service: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_did_service()) 