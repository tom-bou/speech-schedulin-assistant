import os
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

def get_calendar_service():
    """Get or create Google Calendar service with valid credentials"""
    print("\nInitializing Calendar service...")
    creds = _get_credentials()
    print("Building calendar service...")
    service = build('calendar', 'v3', credentials=creds)
    print("Calendar service built successfully")
    return service

def _get_credentials():
    """Get or refresh Google Calendar credentials"""
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

def find_event_by_title(service, title: str, time_min: str = None, time_max: str = None) -> Optional[str]:
    """Find an event by its title and return its ID"""
    try:
        print(f"\nSearching for event with title: {title}")
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        if not time_max:
            time_max = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            
        print("Making API call to Google Calendar...")
        events_result = service.events().list(
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

def add_event(service, event_details: Dict) -> bool:
    """Add a new event to Google Calendar"""
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
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print("API call successful!")
        return True
    except Exception as e:
        print(f"Error adding event: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        return False

def get_events(service, time_min: str, time_max: str) -> List[Dict]:
    """Get all events within a time range"""
    try:
        # Ensure timestamps are in UTC format with 'Z' suffix
        if not time_min.endswith('Z'):
            time_min = time_min + 'Z'
        if not time_max.endswith('Z'):
            time_max = time_max + 'Z'
            
        print(f"\nFetching events from {time_min} to {time_max}")
        print("Making API call to Google Calendar...")
        events_result = service.events().list(
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

def delete_event(service, event_id_or_title: str) -> bool:
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
            event_id = find_event_by_title(service, event_id_or_title)
        
        if not event_id:
            print("Could not find event to delete")
            return False
            
        print(f"Found event ID: {event_id}, attempting to delete...")
        print("Making API call to Google Calendar...")
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        print("API call successful!")
        return True
    except Exception as e:
        print(f"Error deleting event: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        return False 