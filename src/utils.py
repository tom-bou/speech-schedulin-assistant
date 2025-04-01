from typing import Dict, List, Optional
from datetime import datetime

def validate_event_info(event_info: Dict) -> tuple[bool, List[str]]:
    """
    Validates the event information and returns a tuple of (is_valid, missing_fields)
    """
    required_fields = ['title', 'start_time', 'end_time']
    missing_fields = []
    
    for field in required_fields:
        if field not in event_info or not event_info[field]:
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

def generate_missing_info_question(missing_fields: List[str]) -> str:
    """
    Generates a natural question to ask for missing information
    """
    if len(missing_fields) == 1:
        field = missing_fields[0]
        if field == 'title':
            return "What would you like to name this event?"
        elif field == 'start_time':
            return "When would you like this event to start?"
        elif field == 'end_time':
            return "When would you like this event to end?"
    else:
        fields_str = ", ".join(missing_fields)
        return f"I need some additional information. Could you please provide the {fields_str}?"

def format_datetime(dt: datetime) -> str:
    """
    Formats datetime to ISO format for Google Calendar API
    """
    return dt.isoformat()

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parses datetime string to datetime object
    """
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None

def extract_event_info(text: str) -> Dict:
    """
    Extracts event information from natural language text
    """
    # This is a placeholder for more sophisticated NLP processing
    # In a real implementation, you might want to use a more robust NLP solution
    event_info = {
        'title': None,
        'description': None,
        'start_time': None,
        'end_time': None
    }
    
    # Basic keyword extraction
    if 'meeting' in text.lower():
        event_info['title'] = 'Meeting'
    elif 'appointment' in text.lower():
        event_info['title'] = 'Appointment'
    
    return event_info 