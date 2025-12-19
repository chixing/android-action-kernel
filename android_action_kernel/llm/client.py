"""LLM client with strategy pattern for JSON mode and function calling."""
from typing import Dict, Any

from openai import OpenAI

from ..config import Config
from .json_mode import JSONModeClient


class LLMClient:
    """LLM client wrapper that selects the appropriate mode handler."""
    
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
        
        # Select handler based on provider
        self.handler = JSONModeClient(config, self.client)
    
    def get_decision(self, goal: str, screen_context: str) -> Dict[str, Any]:
        """
        Sends screen context to LLM and asks for the next move.
        
        Delegates to the appropriate handler (JSON mode or function calling).
        
        Args:
            goal: The user's goal to achieve
            screen_context: JSON string representation of current screen state
            
        Returns:
            Dictionary containing the action decision from LLM
        """
        return self.handler.get_decision(goal, screen_context)
