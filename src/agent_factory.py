from src.agents import create_calendar_agent
from src.agents import create_planning_agent

def create_agents(model_client):
    calendar_assistant = create_calendar_agent(model_client)
    planning_assistant = create_planning_agent(model_client)

    
    return calendar_assistant, planning_assistant