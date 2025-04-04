"""
Planning agent implementation for the scheduling assistant.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import pytz
from autogen_core import RoutedAgent, message_handler, MessageContext, DefaultTopicId
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage, AssistantMessage, LLMMessage, SystemMessage
from ..utils.event_utils import format_event_details
from .group_chat_manager import GroupChatMessage, RequestToSpeak
from rich.console import Console
from rich.markdown import Markdown

class PlanningAgent(RoutedAgent):
    """Planning agent for coordinating scheduling tasks"""
    
    def __init__(self, description: str, group_chat_topic_type: str, model_client: ChatCompletionClient):
        super().__init__(description=description)
        self._model_client = model_client
        self._group_chat_topic_type = group_chat_topic_type
        self._chat_history: List[LLMMessage] = []

        
        # Set system message
        self._system_message = SystemMessage(content=f"""You are a helpful scheduling assistant. Your role is to:
        1. Process user requests for scheduling tasks
        2. Validate required information for scheduling
        3. Generate appropriate questions when information is missing
        4. Coordinate with the calendar agent to perform operations
        5. Provide clear responses to the user

        When planning events, you need to ensure:
        - All required information is collected (title, start time, end time)
        - Times are properly formatted in UTC
        - Events are properly coordinated with existing calendar events
        - Conflicts are identified and resolved

        When using relative dates, convert them to the actual date.
        For example, if they say "next week", you need to convert that to the date.
        Today is {datetime.now().strftime("%Y-%m-%d")}
        
        IMPORTANT: Store all times in UTC format (e.g., "2024-04-02T14:00:00Z")

        Example usage:
        To plan an event:
        ```python
        # First check for conflicts
        get_events(
            time_min="2024-04-02T14:00:00Z",
            time_max="2024-04-02T15:00:00Z"
        )
        
        # Then add the event if no conflicts
        add_event({{
            "title": "Team Meeting",
            "start_time": "2024-04-02T14:00:00Z",
            "end_time": "2024-04-02T15:00:00Z",
            "description": "Weekly team sync"
        }})
        ```

        Remember: Always coordinate with the calendar agent to perform operations. Do not just say you've done something without calling the appropriate function.""")

    @message_handler
    async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        """Handle incoming messages"""
        # Process the message and generate a response using the model
        self._chat_history.extend([
                UserMessage(content=f"Transferred to {message.body.source}", source="system"),
                message.body,
            ])
        

    @message_handler
    async def handle_request_to_speak(self, message: RequestToSpeak, ctx: MessageContext) -> None:
        """Handle request to speak"""
        Console().print(Markdown(f"### {self.id.type}: "))
        self._chat_history.append(
            UserMessage(content=f"Transferred to {self.id.type}, adopt the persona immediately.", source="system")
        )
        completion = await self._model_client.create([self._system_message] + self._chat_history)
        assert isinstance(completion.content, str)
        self._chat_history.append(AssistantMessage(content=completion.content, source=self.id.type))
        Console().print(Markdown(completion.content))
        # print(completion.content, flush=True)
        await self.publish_message(
            GroupChatMessage(body=UserMessage(content=completion.content, source=self.id.type)),
            topic_id=DefaultTopicId(type=self._group_chat_topic_type),
        )
