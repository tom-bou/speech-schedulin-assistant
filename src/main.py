import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import autogen
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
import sounddevice as sd
import numpy as np
import whisper
import pyttsx3
import pickle
from dateutil import parser
import pytz
# Load environment variables
load_dotenv()

#initializing todays date
today = datetime.now().strftime("%Y-%m-%d")
dt = datetime.now(timezone.utc) # Current UTC time

local_dt = datetime.now() # Current local time with timezone info (if set)
time_difference = local_dt.utcoffset()

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'



def format_event_details(event: Dict) -> str:
    """Format event details for display"""
    try:
        start = parser.parse(event['start']['dateTime'])
        end = parser.parse(event['end']['dateTime'])
        return f"Event ID: {event['id']}\nEvent: {event['summary']}\nStart: {start.strftime('%Y-%m-%d %H:%M')}\nEnd: {end.strftime('%Y-%m-%d %H:%M')}\nDescription: {event.get('description', 'No description')}\n"
    except Exception as e:
        print(f"Error formatting event details: {str(e)}")
        return f"Event ID: {event.get('id', 'Unknown')}\nEvent: {event.get('summary', 'Unknown')}\nError formatting details\n"

class CalendarAgent:
    def __init__(self):
        print("\nInitializing CalendarAgent...")
        self.creds = self._get_credentials()
        print("Building calendar service...")
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("Calendar service built successfully")
        
    def _get_credentials(self):
        print("Getting credentials...")
        creds = None
        if os.path.exists('token.pickle'):
            print("Found existing token.pickle, loading credentials...")
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Credentials expired, refreshing...")
                creds.refresh(Request())
            else:
                print("No valid credentials found, starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file('creds.json', SCOPES)
                creds = flow.run_local_server(port=0)
            print("Saving credentials to token.pickle...")
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        print("Credentials obtained successfully")
        return creds

    def find_event_by_title(self, title: str, time_min: str = None, time_max: str = None) -> Optional[str]:
        """Find an event by its title and return its ID"""
        try:
            print(f"\nSearching for event with title: {title}")
            if not time_min:
                time_min = datetime.now(timezone.utc).isoformat()
            if not time_max:
                time_max = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                
            print("Making API call to Google Calendar...")
            events_result = self.service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                if event.get('summary', '').lower() == title.lower():
                    print(f"Found event with ID: {event['id']}")
                    return event['id']
            
            print("No event found with that title")
            return None
        except Exception as e:
            print(f"Error finding event: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return None

    def add_event(self, event_details: Dict) -> bool:
        try:
            print("\nPreparing to add event to Google Calendar...")
            event = {
                'summary': event_details.get('title'),
                'description': event_details.get('description'),
                'start': {
                    'dateTime': event_details.get('start_time'),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_details.get('end_time'),
                    'timeZone': 'UTC',
                },
            }
            print("Making API call to Google Calendar...")
            self.service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            print("API call successful!")
            return True
        except Exception as e:
            print(f"Error adding event: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return False

    def get_events(self, time_min: str, time_max: str) -> List[Dict]:
        try:
            # Ensure timestamps are in UTC format with 'Z' suffix
            if not time_min.endswith('Z'):
                time_min = time_min + 'Z'
            if not time_max.endswith('Z'):
                time_max = time_max + 'Z'
                
            print(f"\nFetching events from {time_min} to {time_max}")
            print("Making API call to Google Calendar...")
            events_result = self.service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            print(f"API call successful! Found {len(events)} events")
            return events
        except Exception as e:
            print(f"Error getting events: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return []

    def delete_event(self, event_id_or_title: str) -> bool:
        """Delete an event by its ID or title"""
        try:
            print(f"\nAttempting to delete event with ID/title: {event_id_or_title}")
            
            # If it looks like an event ID (contains only alphanumeric characters and underscores)
            if event_id_or_title.replace('_', '').isalnum():
                print(f"Using provided event ID: {event_id_or_title}")
                event_id = event_id_or_title
            else:
                # Try to find event by title
                print(f"Searching for event with title: {event_id_or_title}")
                event_id = self.find_event_by_title(event_id_or_title)
            
            if not event_id:
                print("Could not find event to delete")
                return False
                
            print(f"Found event ID: {event_id}, attempting to delete...")
            print("Making API call to Google Calendar...")
            self.service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
            print("API call successful!")
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            return False

class AudioAgent:
    def __init__(self):
        try:
            self.whisper_model = whisper.load_model("base")
            self.engine = pyttsx3.init()
        except Exception as e:
            print(f"Error initializing audio components: {e}")
            raise
        
    def listen(self) -> str:
        try:
            duration = 5  # seconds
            sample_rate = 44100
            print("Listening... (5 seconds)")
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
            sd.wait()
            
            # Convert to the format expected by Whisper
            audio_data = recording.flatten().astype(np.float32)
            result = self.whisper_model.transcribe(audio_data)
            return result["text"]
        except Exception as e:
            print(f"Error during audio recording: {e}")
            return ""

    def speak(self, text: str):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error during text-to-speech: {e}")

def create_agents():
    try:
        # Create the calendar agent
        calendar_agent = CalendarAgent()
        
        # Create the audio agent
        audio_agent = AudioAgent()
        
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
            
            If the user uses relative dates, you need to convert them to the local timezone.
            For example, if they say "next week", you need to convert that to the date in the local timezone.
            Today is {today}.
            The local timezone is {local_dt.astimezone().tzinfo}.
            
            IMPORTANT: All times should be in UTC/GMT. When scheduling events:
            1. Convert the user's local time to UTC by adding the timezone offset
            2. Store all times in UTC format (e.g., "2024-04-02T14:00:00Z")
            3. When displaying times to the user, convert back to their local timezone
            
            These are the only functions you have access to:
            - add_event(event_details): Add a new event to the calendar
            - get_events(time_min, time_max): Get events in a time range
            - delete_event(event_id): Delete an event
            - format_event_details(event): Format event details for display
            
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
        
        # Create the user proxy agent
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={
                "work_dir": "workspace",
                "use_docker": False,
                "last_n_messages": 3,
                "execution_timeout": 60,
                "function_call_auto_approve": True
            },
            llm_config=False
        )

        # Register calendar functions
        def add_event_wrapper(**kwargs: Dict[str, Any]) -> str:
            return handle_function_call("add_event", calendar_agent=calendar_agent, **kwargs)
        
        def get_events_wrapper(**kwargs: Dict[str, Any]) -> str:
            return handle_function_call("get_events", calendar_agent=calendar_agent, **kwargs)
        
        def delete_event_wrapper(**kwargs: Dict[str, Any]) -> str:
            return handle_function_call("delete_event", calendar_agent=calendar_agent, **kwargs)

        # Register functions using register_function
        autogen.register_function(
            add_event_wrapper,
            caller=assistant,
            executor=user_proxy,
            name="add_event",
            description="Add a new event to the calendar",
        )

        autogen.register_function(
            get_events_wrapper,
            caller=assistant,
            executor=user_proxy,
            name="get_events",
            description="Get events from the calendar",
        )

        autogen.register_function(
            delete_event_wrapper,
            caller=assistant,
            executor=user_proxy,
            name="delete_event",
            description="Delete an event from the calendar",
        )
        
        return {
            "calendar_agent": calendar_agent,
            "audio_agent": audio_agent,
            "assistant": assistant,
            "user_proxy": user_proxy
        }
    except Exception as e:
        print(f"Error creating agents: {e}")
        raise

def handle_function_call(function_name: str, **kwargs):
    """Handle function calls from the assistant"""
    calendar_agent = kwargs.get('calendar_agent')
    
    try:
        print("\n" + "="*50)
        print(f"EXECUTING FUNCTION: {function_name}")
        print("="*50 + "\n")
        
        if function_name == 'add_event':
            event_details = kwargs.get('event_details', {})
            print(f"Adding event with details:")
            print(f"Title: {event_details.get('title')}")
            print(f"Start: {event_details.get('start_time')}")
            print(f"End: {event_details.get('end_time')}")
            print(f"Description: {event_details.get('description', 'No description')}")
            
            result = calendar_agent.add_event(event_details)
            print(f"\nEvent addition result: {'SUCCESS' if result else 'FAILED'}")
            if result:
                return "Event successfully added to calendar"
            else:
                return "Failed to add event to calendar"
        elif function_name == 'get_events':
            print(f"Fetching events from {kwargs['time_min']} to {kwargs['time_max']}")
            events = calendar_agent.get_events(kwargs['time_min'], kwargs['time_max'])
            if events:
                print(f"\nFound {len(events)} events:")
                return "\n".join(format_event_details(event) for event in events)
            else:
                return "No events found in the specified time range"
        elif function_name == 'delete_event':
            print(f"Attempting to delete event with ID: {kwargs['event_id']}")
            result = calendar_agent.delete_event(kwargs['event_id'])
            print(f"\nEvent deletion result: {'SUCCESS' if result else 'FAILED'}")
            if result:
                return "Event successfully deleted from calendar"
            else:
                return "Failed to delete event from calendar"
        else:
            raise ValueError(f"Unknown function: {function_name}")
    except Exception as e:
        print(f"\nERROR executing {function_name}: {str(e)}")
        return f"Error executing {function_name}: {str(e)}"

def main():

    print("Initializing scheduling assistant...")
    agents = create_agents()
    
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
    
    # Add debug logging for function calls
    def debug_function_handler(name, **kwargs):
        print(f"\nDEBUG: Function {name} called with args: {kwargs}")
        result = handle_function_call(name, calendar_agent=agents["calendar_agent"], **kwargs)
        print(f"DEBUG: Function {name} result: {result}")
        return result
    
    agents["user_proxy"].initiate_chat(
        agents["assistant"],
        message="Hello! I'm your scheduling assistant. I can help you add, view, or delete calendar events. How can I help you today?",
        function_call_handler=debug_function_handler
    )


if __name__ == "__main__":
    main()
