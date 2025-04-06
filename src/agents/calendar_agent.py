"""
Calendar agent implementation for the scheduling assistant.
"""

from typing import Dict, Any, List
from datetime import datetime
import pytz
from autogen_core import (
    MessageContext,
    RoutedAgent,
    message_handler,
    DefaultTopicId,
    FunctionCall,
)
from autogen_core.models import (
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
    AssistantMessage,
)
from autogen_core.tools import FunctionTool
from rich.console import Console
from rich.markdown import Markdown
import json

from ..utils.calender_utils import (
    get_calendar_service,
    add_event,
    get_events,
    delete_event,
)
from ..utils.event_utils import format_event_details
from .group_chat_manager import GroupChatMessage, RequestToSpeak


class CalendarAgent(RoutedAgent):
    """Calendar agent for managing calendar operations"""

    def __init__(
        self,
        description: str,
        group_chat_topic_type: str,
        model_client: ChatCompletionClient,
    ):
        super().__init__(description=description)
        self._model_client = model_client
        self._group_chat_topic_type = group_chat_topic_type
        self._chat_history: List[UserMessage | AssistantMessage] = []

        # Initialize the calendar service
        self._calendar_service = get_calendar_service()

        # Initialize tools
        self._tools = self._create_tools()

        # Set system message
        self._system_message = SystemMessage(
            content=f"""You are a helpful scheduling assistant. Your role is to:

        IMPORTANT: You MUST use the provided functions to perform calendar operations. Do not just say you've done something - actually call the function.

        You have access to the following functions:
        - add_event(event_details): Add a new event to the calendar
        - get_events(time_min, time_max): Get events in a time range
        - delete_event(event_id): Delete an event
        
        When adding events, you need:
        - title: Event title
        - start_time: Start time in ISO format
        - end_time: End time in ISO format
        - description (optional): Event description

        When getting events, provide time_min and time_max in ISO format.
        When deleting events, provide the event_id from the event details.
        
        When using relative dates, convert them to the actual date.
        For example, if they say "next week", you need to convert that to the date.
        Today is {datetime.now().strftime("%Y-%m-%d")}
        

        Example usage:
        To add an event:
        ```python
        add_event(event_details: {{
            "title": "Team Meeting",
            "start_time": "2024-04-02T14:00:00",
            "end_time": "2024-04-02T15:00:00",
            "description": "Weekly team sync"
        }})
        ```

        To get events:
        ```python
        get_events(
            time_min="2024-04-02T00:00:00",
            time_max="2024-04-02T23:59:59"
        )
        ```

        To delete an event:
        ```python
        delete_event(event_id="event_id_here")
        ```
        """
        )

    def _create_tools(self) -> List[FunctionTool]:
        """Create the tools for the calendar agent"""

        async def add_event_wrapper(event_details: Dict[str, Any]) -> str:
            try:
                print("Adding event with details:")
                print(f"Title: {event_details.get('title')}")
                print(f"Start: {event_details.get('start_time')}")
                print(f"End: {event_details.get('end_time')}")
                print(
                    f"Description: {event_details.get('description', 'No description')}"
                )

                start_time_str = event_details["start_time"]
                end_time_str = event_details["end_time"]

                # If the input is known to be local even if it ends with a "Z", remove the "Z"
                if start_time_str.endswith("Z"):
                    start_time_str = start_time_str[:-1]
                if end_time_str.endswith("Z"):
                    end_time_str = end_time_str[:-1]

                # Parse as naive datetimes
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)

                # Convert to UTC and format without double Z
                event_details["start_time"] = start_time.astimezone(pytz.UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                event_details["end_time"] = end_time.astimezone(pytz.UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                print("Converted times:")
                print(f"Start (UTC): {event_details['start_time']}")
                print(f"End (UTC): {event_details['end_time']}")

                print("\nPreparing to add event to Google Calendar...")
                print("Making API call to Google Calendar...")
                result = await add_event(self._calendar_service, event_details)
                print(f"\nEvent addition result: {'SUCCESS' if result else 'FAILED'}")
                return (
                    "Event successfully added to calendar"
                    if result
                    else "Failed to add event to calendar"
                )
            except Exception as e:
                print(f"\nERROR adding event: {str(e)}")
                return f"Error adding event: {str(e)}"

        async def get_events_wrapper(time_min: str, time_max: str) -> str:
            try:
                print(f"Fetching events from {time_min} to {time_max}")
                start_time_str = time_min
                end_time_str = time_max

                if start_time_str.endswith("Z"):
                    start_time_str = start_time_str[:-1]
                if end_time_str.endswith("Z"):
                    end_time_str = end_time_str[:-1]

                # Parse as naive datetimes
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)

                # Convert to UTC and format without double Z
                time_min = start_time.astimezone(pytz.UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                time_max = end_time.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

                print(f"Fetching events from {time_min} to {time_max}")

                events = await get_events(self._calendar_service, time_min, time_max)
                if events:
                    print(f"\nFound {len(events)} events:")
                    return "\n".join(format_event_details(event) for event in events)
                else:
                    return "No events found in the specified time range"
            except Exception as e:
                print(f"\nERROR getting events: {str(e)}")
                return f"Error getting events: {str(e)}"

        async def delete_event_wrapper(event_id: str) -> str:
            try:
                print(f"Attempting to delete event with ID: {event_id}")
                result = await delete_event(self._calendar_service, event_id)
                print(f"\nEvent deletion result: {'SUCCESS' if result else 'FAILED'}")
                return (
                    "Event successfully deleted from calendar"
                    if result
                    else "Failed to delete event from calendar"
                )
            except Exception as e:
                print(f"\nERROR deleting event: {str(e)}")
                return f"Error deleting event: {str(e)}"

        return [
            FunctionTool(
                name="add_event",
                description="Add a new event to the calendar",
                func=add_event_wrapper,
            ),
            FunctionTool(
                name="get_events",
                description="Get events in a time range",
                func=get_events_wrapper,
            ),
            FunctionTool(
                name="delete_event",
                description="Delete an event from the calendar",
                func=delete_event_wrapper,
            ),
        ]

    @message_handler
    async def handle_message(
        self, message: GroupChatMessage, ctx: MessageContext
    ) -> None:
        """Handle incoming messages"""
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

        # Ensure that the calendar tools are used
        completion = await self._model_client.create(
            [self._system_message] + self._chat_history,
            tools=self._tools,
            extra_create_args={"tool_choice": "required"},
            cancellation_token=ctx.cancellation_token,
        )

        assert isinstance(completion.content, list) and all(
            isinstance(item, FunctionCall) for item in completion.content
        )

        results: List[str] = []
        for tool_call in completion.content:
            arguments = json.loads(tool_call.arguments)
            Console().print(arguments)
            # Find the matching tool by name
            tool = next(t for t in self._tools if t.name == tool_call.name)
            result = await tool.run_json(arguments, ctx.cancellation_token)
            results.append(tool.return_value_as_string(result))

        await self.publish_message(
            GroupChatMessage(
                body=UserMessage(content="\n".join(results), source=self.id.type)
            ),
            DefaultTopicId(type=self._group_chat_topic_type),
        )
