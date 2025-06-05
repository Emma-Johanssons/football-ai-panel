import os
from dotenv import load_dotenv

def test_env():
    print("Testing environment variables...")
    load_dotenv()
    
    # Test required environment variables
    required_vars = [
        "FOOTBALL_API_KEY",
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Print first 4 characters of the key for verification
            print(f"{var}: {value[:4]}...")
    
    if missing_vars:
        print("\nMissing environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    
    print("\nAll required environment variables are present!")
    return True

if __name__ == "__main__":
    test_env() 