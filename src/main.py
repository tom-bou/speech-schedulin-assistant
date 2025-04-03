import os
import sys
import autogen
from datetime import datetime, timedelta
from typing import Sequence
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agent_factory import create_agents

async def main():
    """Main function to run the scheduling assistant"""
    try:
        # Initialize the model client
        model_client = OpenAIChatCompletionClient(model="gpt-4")
        
        # Create the agents and its functions
        calender_agent, planning_agent = create_agents(model_client)
        
        # Define termination conditions
        text_mention_termination = TextMentionTermination("TERMINATE")
        max_messages_termination = MaxMessageTermination(max_messages=25)
        termination = text_mention_termination | max_messages_termination
        
        # Define the selector prompt
        selector_prompt = """Select an agent to perform task.

        {roles}

        Current conversation context:
        {history}

        Read the above conversation, then select an agent from {participants} to perform the next task.
        Make sure the calendar assistant has assigned tasks before other agents start working.
        Only select one agent.
        """
        
        user_proxy_agent = UserProxyAgent("UserProxyAgent", description="A proxy for the user to approve or disapprove tasks.")


        def selector_func_with_user_proxy(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
            if messages[-1].source != planning_agent.name and messages[-1].source != user_proxy_agent.name:
                # Planning agent should be the first to engage when given a new task, or check progress.
                return planning_agent.name
            if messages[-1].source == planning_agent.name:
                if messages[-2].source == user_proxy_agent.name and "APPROVE" in messages[-1].content.upper():  # type: ignore
                    # User has approved the plan, proceed to the next agent.
                    return None
                # Use the user proxy agent to get the user's approval to proceed.
                return user_proxy_agent.name
            if messages[-1].source == user_proxy_agent.name:
                # If the user does not approve, return to the planning agent.
                if "APPROVE" not in messages[-1].content.upper():  # type: ignore
                    return planning_agent.name
            return None
                
        # Create the team with all agents
        team = SelectorGroupChat(
            [calender_agent, planning_agent, user_proxy_agent],
            model_client=model_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            selector_func=selector_func_with_user_proxy,
            allow_repeated_speaker=True
        )
        
        # Print welcome message
        print("\nWelcome to the Scheduling Assistant!")
        print("I can help you with:")
        print("1. Adding new calendar events")
        print("2. Viewing your calendar events")
        print("3. Deleting calendar events")
        print("\nExample commands:")
        print("- Add a meeting tomorrow at 2 PM")
        print("- Show my events for next week")
        print("- Delete the team meeting on Friday")
        print("\nType 'exit' to quit or 'TERMINATE' to end the conversation.")
        
        # Start the chat
        await Console(team.run_stream(task="Hello! I'm your planning assistant. How can I help you today?"))
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
