"""
Planning agent implementation for the scheduling assistant.
"""

from typing import Dict, Any, List
from datetime import datetime
from autogen_core import RoutedAgent, message_handler, MessageContext, DefaultTopicId
from autogen_core.models import (
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    LLMMessage,
    SystemMessage,
)
from .group_chat_manager import GroupChatMessage, RequestToSpeak
from rich.console import Console
from rich.markdown import Markdown


class PlanningAgent(RoutedAgent):
    """Planning agent for coordinating scheduling tasks"""

    def __init__(
        self,
        description: str,
        group_chat_topic_type: str,
        model_client: ChatCompletionClient,
    ):
        super().__init__(description=description)
        self._model_client = model_client
        self._group_chat_topic_type = group_chat_topic_type
        self._chat_history: List[LLMMessage] = []

        # Set system message
        self._system_message = SystemMessage(
            content=f"""You are a helpful scheduling assistant. Your role is to:
        1. Process user requests for scheduling tasks
        2. Validate required information for scheduling
        3. Generate appropriate questions when information is missing
        4. Coordinate with the calendar agent to perform operations on the calendar
        5. Provide clear responses to the user

        When planning events, you need to ensure:
        - All required information is collected (title, start time, end time)
        - That there is no conflict, when you know the dates you need to check the calendar by asking the calendar agent
        - When you know the calender and your task, please give recommendations on the best time to do the task
        - If the activity is weather dependent, please ask the weather agent for the weather, for this you need to know the location and the date of the activity

        When using relative dates, convert them to the actual date.
        For example, if they say "next week", you need to convert that to the date.
        Today is {datetime.now().strftime("%Y-%m-%d")}
        
        IMPORTANT: Store all times in UTC format (e.g., "2024-04-02T14:00:00Z")

        
        """
        )

    @message_handler
    async def handle_message(
        self, message: GroupChatMessage, ctx: MessageContext
    ) -> None:
        """Handle incoming messages"""
        # Process the message and generate a response using the model
        self._chat_history.extend(
            [
                UserMessage(
                    content=f"Transferred to {message.body.source}", source="system"
                ),
                message.body,
            ]
        )

    @message_handler
    async def handle_request_to_speak(
        self, message: RequestToSpeak, ctx: MessageContext
    ) -> None:
        """Handle request to speak"""
        Console().print(Markdown(f"### {self.id.type}: "))
        self._chat_history.append(
            UserMessage(
                content=f"Transferred to {self.id.type}, adopt the persona immediately.",
                source="system",
            )
        )
        completion = await self._model_client.create(
            [self._system_message] + self._chat_history
        )
        assert isinstance(completion.content, str)
        self._chat_history.append(
            AssistantMessage(content=completion.content, source=self.id.type)
        )
        Console().print(Markdown(completion.content))
        # print(completion.content, flush=True)
        await self.publish_message(
            GroupChatMessage(
                body=UserMessage(content=completion.content, source=self.id.type)
            ),
            topic_id=DefaultTopicId(type=self._group_chat_topic_type),
        )
