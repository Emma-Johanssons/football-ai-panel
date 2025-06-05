import sys
import asyncio
from test_env import test_env
from services.panel_service import main

if __name__ == "__main__":
    print("Starting application...")
    
    # Test environment variables
    if not test_env():
        print("Environment test failed. Exiting...")
        sys.exit(1)
    
    # Run the main application
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1) 