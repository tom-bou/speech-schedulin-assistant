# Scheduling Assistant with AutoGen

This is a scheduling assistant that uses AutoGen to coordinate multiple agents for handling calendar operations and audio interactions.

## Features

- Voice input/output using Whisper and pyttsx3
- Google Calendar integration for managing events
- Intelligent conversation using AutoGen agents
- Automatic information validation and request generation

## Prerequisites

- Python 3.8 or higher
- Google Calendar API credentials
- OpenAI API key

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env`:

```
OPENAI_API_KEY=your_openai_api_key
```

3. Set up Google Calendar API:
   - Go to the Google Cloud Console
   - Create a new project
   - Enable the Google Calendar API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials and save as `creds.json` in the project root

## Usage

Run the main script:

```bash
python src/main.py
```

The system will:

1. Initialize all agents (Calendar, Audio, Assistant, and User Proxy)
2. Start a conversation with the user
3. Process voice input and provide voice output
4. Manage calendar events based on user requests

## Agent Roles

- **Calendar Agent**: Handles all Google Calendar operations
- **Audio Agent**: Manages voice input/output
- **Assistant Agent**: Coordinates between agents and processes user requests
- **User Proxy Agent**: Interfaces with the human user

## Example Interactions

1. Adding an event:

   - User: "Schedule a meeting tomorrow at 2 PM"
   - Assistant will ask for missing information if needed
   - Calendar Agent will create the event

2. Viewing events:

   - User: "What meetings do I have today?"
   - Calendar Agent will fetch and display the events

3. Deleting events:
   - User: "Cancel my meeting tomorrow"
   - Assistant will confirm and Calendar Agent will delete the event
