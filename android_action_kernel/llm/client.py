"""LLM client using JSON mode."""
from typing import Dict, Any

from openai import OpenAI

from ..config import Config
from .json_mode import JSONModeClient


class LLMClient:
    """LLM client wrapper that uses JSON mode."""
    
    def __init__(self, config: Config):
        """
        Initialize LLM client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_url
        )
        self.handler = JSONModeClient(config, self.client)
    
    def get_decision(self, goal: str, screen_context: str) -> Dict[str, Any]:
        """
        Sends screen context to LLM and asks for the next move.
        
        Args:
            goal: The user's goal to achieve
            screen_context: JSON string representation of current screen state
            
        Returns:
            Dictionary containing the action decision from LLM
        """
        return self.handler.get_decision(goal, screen_context)
