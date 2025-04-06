"""
Main entry point for the scheduling assistant.
"""

import os
import asyncio
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import SingleThreadedAgentRuntime, TypeSubscription, TopicId
from .agents.group_chat_manager import (
    GroupChatManager,
    GroupChatMessage,
    RequestToSpeak,
)
from .agents.user_agent import UserAgent
from autogen_core.models import UserMessage
import uuid
from .agents.calendar_agent import CalendarAgent
from .agents.planning_agent import PlanningAgent


async def main():
    """Initialize and run the scheduling assistant."""
    # Load environment variables
    load_dotenv()

    # Initialize the model client
    model_client = OpenAIChatCompletionClient(
        api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4-turbo-preview"
    )

    # Create the runtime
    runtime = SingleThreadedAgentRuntime()

    # Define topic types
    calendar_topic_type = "CalendarAgent"
    planning_topic_type = "PlanningAgent"
    user_topic_type = "User"
    group_chat_topic_type = "planning"

    # Define descriptions
    calendar_description = "Calendar agent for managing calendar operations"
    planning_description = "Planning agent for coordinating scheduling tasks"
    user_description = "User for providing final approval and giving "

    # Register calendar agent
    calendar_agent_type = await CalendarAgent.register(
        runtime,
        calendar_topic_type,
        lambda: CalendarAgent(
            description=calendar_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=model_client,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=calendar_topic_type, agent_type=calendar_agent_type.type
        )
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=group_chat_topic_type, agent_type=calendar_agent_type.type
        )
    )

    # Register planning agent
    planning_agent_type = await PlanningAgent.register(
        runtime,
        planning_topic_type,
        lambda: PlanningAgent(
            description=planning_description,
            group_chat_topic_type=group_chat_topic_type,
            model_client=model_client,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=planning_topic_type, agent_type=planning_agent_type.type
        )
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=group_chat_topic_type, agent_type=planning_agent_type.type
        )
    )

    # Register user agent
    user_agent_type = await UserAgent.register(
        runtime,
        user_topic_type,
        lambda: UserAgent(
            description=user_description, group_chat_topic_type=group_chat_topic_type
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(topic_type=user_topic_type, agent_type=user_agent_type.type)
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=group_chat_topic_type, agent_type=user_agent_type.type
        )
    )

    # Register group chat manager
    group_chat_manager_type = await GroupChatManager.register(
        runtime,
        "group_chat_manager",
        lambda: GroupChatManager(
            participant_topic_types=[
                calendar_topic_type,
                planning_topic_type,
                user_topic_type,
            ],
            model_client=model_client,
            participant_descriptions=[
                calendar_description,
                planning_description,
                user_description,
            ],
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=group_chat_topic_type, agent_type=group_chat_manager_type.type
        )
    )

    # Print welcome message
    print("\nWelcome to the Scheduling Assistant!")
    print("You can interact with me using natural language.")
    print("Example commands:")
    print("- Schedule a meeting with John this week")
    print("- Check my calendar for next week")
    print("- Plan tomorrow's schedule")
    print("- Delete the team meeting on Friday")
    print("\nType 'exit' to quit.\n")

    # Start the runtime
    runtime.start()
    session_id = str(uuid.uuid4())

    # Wait for user input
    user_input = input("\nYou: ")

    # Create a topic ID for this message
    topic_id = TopicId(type=group_chat_topic_type, source=session_id)

    # Publish the user's message
    await runtime.publish_message(
        GroupChatMessage(body=UserMessage(content=user_input, source="User")), topic_id
    )

    # Stop the runtime
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
