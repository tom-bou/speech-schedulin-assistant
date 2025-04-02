"""
Scheduling Assistant with AutoGen
A Python application for managing calendar events using AI agents.
"""

__version__ = "0.1.0"

from .agent_factory import create_agents
from .main import main

__all__ = ['create_agents', 'main']
