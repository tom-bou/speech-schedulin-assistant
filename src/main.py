import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from typing import Dict, Any
from datetime import datetime, timezone
import autogen
from dotenv import load_dotenv
from src.agent_factory import create_agents

# Load environment variables
load_dotenv()

# Initialize dates
today = datetime.now().strftime("%Y-%m-%d")
dt = datetime.now(timezone.utc)  # Current UTC time
local_dt = datetime.now()  # Current local time with timezone info (if set)

def main():
    print("Initializing scheduling assistant...")
    
    calendar_assistant, user_proxy = create_agents()
    
    
    # Initialize the chat with function handler
    print("\n" + "="*50)
    print("SCHEDULING ASSISTANT STARTED")
    print("="*50 + "\n")
    print("You can now schedule events, view your calendar, or delete events.")
    print("\nExample commands:")
    print("- Schedule a meeting tomorrow at 2 PM")
    print("- Show me my events for today")
    print("- Cancel my meeting tomorrow at 2 PM")
    print("- Type 'exit' to end the conversation\n")
    
    user_proxy.initiate_chat(
        calendar_assistant,
        message="Hello! I'm your scheduling assistant. I can help you add, view, or delete calendar events. How can I help you today?",
    )

if __name__ == "__main__":
    main()
