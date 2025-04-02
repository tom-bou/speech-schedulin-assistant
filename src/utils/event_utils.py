from typing import Dict
from dateutil import parser

def format_event_details(event: Dict) -> str:
    """Format event details for display"""
    try:
        start = parser.parse(event['start']['dateTime'])
        end = parser.parse(event['end']['dateTime'])
        return f"Event ID: {event['id']}\nEvent: {event['summary']}\nStart: {start.strftime('%Y-%m-%d %H:%M')}\nEnd: {end.strftime('%Y-%m-%d %H:%M')}\nDescription: {event.get('description', 'No description')}\n"
    except Exception as e:
        print(f"Error formatting event details: {str(e)}")
        return f"Event ID: {event.get('id', 'Unknown')}\nEvent: {event.get('summary', 'Unknown')}\nError formatting details\n" 