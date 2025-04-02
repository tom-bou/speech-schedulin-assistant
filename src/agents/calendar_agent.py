"""
Calendar agent implementation for the scheduling assistant.
"""

import os
from typing import Dict, Any
from datetime import datetime, timezone
import pytz
import autogen
from ..utils.calender_utils import get_calendar_service, add_event, get_events, delete_event
from ..utils.event_utils import format_event_details


def create_calendar_agent():
    """Create and configure the calendar assistant agent with its functions"""
    try:
        # Initialize the calendar service
        calendar_service = get_calendar_service()
        
        now = datetime.now()
        local_now = now.astimezone()
        local_tz = local_now.tzinfo
        try:
            # Try to get system timezone
            import subprocess
            if os.name == 'nt':  # Windows
                import win32timezone
                local_tz = pytz.timezone(win32timezone.getTimeZoneName())
            else:  # Unix-like systems
                tz_str = subprocess.check_output(['date', '+%Z']).decode().strip()
                if tz_str:
                    local_tz = pytz.timezone(tz_str)
        except Exception as e:
            print(f"Warning: Could not determine system timezone, using default: {e}")
        
        # Get current times
        local_now = datetime.now(tz=local_tz)
        utc_now = datetime.now(pytz.UTC)
        
        # Create the assistant agent
        assistant = autogen.AssistantAgent(
            name="scheduling_assistant",
            system_message=f"""You are a helpful scheduling assistant. Your role is to:
            1. Process user requests for calendar operations
            2. Validate required information for calendar events
            3. Generate appropriate questions when information is missing
            4. Coordinate with the calendar agent to perform operations
            5. Provide clear responses to the user

            IMPORTANT: You MUST use the provided functions to perform calendar operations. Do not just say you've done something - actually call the function.

            You have access to the following functions:
            - add_event(event_details): Add a new event to the calendar
            - get_events(time_min, time_max): Get events in a time range
            - delete_event(event_id): Delete an event
            - format_event_details(event): Format event details for display

            When adding events, you need:
            - title: Event title
            - start_time: Start time in ISO format
            - end_time: End time in ISO format
            - description (optional): Event description

            When getting events, provide time_min and time_max in ISO format.
            When deleting events, provide the event_id from the event details.
            
            When using relative dates, convert them to the actual date.
            For example, if they say "next week", you need to convert that to the date.
            Today is {datetime.now().strftime("%Y-%m-%d")}.
            
            IMPORTANT: Store all times in UTC format (e.g., "2024-04-02T14:00:00Z")

            Example usage:
            To add an event:
            ```python
            add_event({{
                "event_details": {{
                    "title": "Team Meeting",
                    "start_time": "2024-04-02T14:00:00",
                    "end_time": "2024-04-02T15:00:00",
                    "description": "Weekly team sync"
                }} 
            }})
            ```

            To get events:
            ```python
            get_events({{
                "time_min": "2024-04-02T00:00:00",
                "time_max": "2024-04-02T23:59:59"
            }})
            ```

            To delete an event:
            ```python
            delete_event({{
                "event_id": "event_id_here"
            }})
            ```

            Remember: Always use the actual functions to perform operations. Do not just say you've done something without calling the appropriate function.""",
            llm_config={
                "config_list": [{"model": "gpt-4", "api_key": os.getenv("OPENAI_API_KEY")}]
            }
        )

        def add_event_wrapper(**kwargs: Dict[str, Any]) -> str:
            try:
                event_details = kwargs.get('event_details', {})
                print("Adding event with details:")
                print(f"Title: {event_details.get('title')}")
                print(f"Start: {event_details.get('start_time')}")
                print(f"End: {event_details.get('end_time')}")
                print(f"Description: {event_details.get('description', 'No description')}")

                start_time_str = event_details['start_time']
                end_time_str = event_details['end_time']

                # If the input is known to be local even if it ends with a "Z", remove the "Z"
                if start_time_str.endswith('Z'):
                    start_time_str = start_time_str[:-1]
                if end_time_str.endswith('Z'):
                    end_time_str = end_time_str[:-1]

                # Parse as naive datetimes
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                
                # Convert to UTC and format without double Z
                event_details['start_time'] = start_time.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                event_details['end_time'] = end_time.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

                print("Converted times:")
                print(f"Start (UTC): {event_details['start_time']}")
                print(f"End (UTC): {event_details['end_time']}")

                print("\nPreparing to add event to Google Calendar...")
                print("Making API call to Google Calendar...")
                result = add_event(calendar_service, event_details)
                print(f"\nEvent addition result: {'SUCCESS' if result else 'FAILED'}")
                return "Event successfully added to calendar" if result else "Failed to add event to calendar"
            except Exception as e:
                print(f"\nERROR adding event: {str(e)}")
                return f"Error adding event: {str(e)}"
                
        def get_events_wrapper(**kwargs: Dict[str, Any]) -> str:
            try:
                print(f"Fetching events from {kwargs['time_min']} to {kwargs['time_max']}")
                start_time_str = kwargs['time_min']
                end_time_str = kwargs['time_max']
                
                if start_time_str.endswith('Z'):
                    start_time_str = start_time_str[:-1]
                if end_time_str.endswith('Z'):
                    end_time_str = end_time_str[:-1]

                # Parse as naive datetimes
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                
                # Convert to UTC and format without double Z
                kwargs['time_min'] = start_time.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                kwargs['time_max'] = end_time.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                print(f"Fetching events from {kwargs['time_min']} to {kwargs['time_max']}")
                
                events = get_events(calendar_service, kwargs['time_min'], kwargs['time_max'])
                if events:
                    print(f"\nFound {len(events)} events:")
                    return "\n".join(format_event_details(event) for event in events)
                else:
                    return "No events found in the specified time range"
            except Exception as e:
                print(f"\nERROR getting events: {str(e)}")
                return f"Error getting events: {str(e)}"
        
        def delete_event_wrapper(**kwargs: Dict[str, Any]) -> str:
            try:
                print(f"Attempting to delete event with ID: {kwargs['event_id']}")
                
                result = delete_event(calendar_service, kwargs['event_id'])
                print(f"\nEvent deletion result: {'SUCCESS' if result else 'FAILED'}")
                if result:
                    return "Event successfully deleted from calendar"
                else:
                    return "Failed to delete event from calendar"
            except Exception as e:
                print(f"\nERROR deleting event: {str(e)}")
                return f"Error deleting event: {str(e)}"

        return assistant, {
            "add_event": (add_event_wrapper, "Add a new event to the calendar"),
            "get_events": (get_events_wrapper, "Get events from the calendar"),
            "delete_event": (delete_event_wrapper, "Delete an event from the calendar")
        }
    except Exception as e:
        print(f"Error creating calendar agent: {str(e)}")
        raise 