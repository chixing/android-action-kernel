"""LLM client with strategy pattern for JSON mode and function calling."""
from typing import Dict, Any

from openai import OpenAI

from ..config import Config
from ..exceptions import LLMError
from .json_mode import JSONModeClient
from .function_calling import FunctionCallingClient


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
        # Note: Ollama function calling may be unreliable, so we use JSON mode as fallback
        if config.provider == "ollama":
            # Try function calling first, but fallback to JSON mode if it fails
            self.handler = FunctionCallingClient(config, self.client)
            self.json_fallback = JSONModeClient(config, self.client)
        else:
            self.handler = JSONModeClient(config, self.client)
            self.json_fallback = None
    
    def get_decision(self, goal: str, screen_context: str) -> Dict[str, Any]:
        """
        Sends screen context to LLM and asks for the next move.
        
        Delegates to the appropriate handler (JSON mode or function calling).
        For Ollama, falls back to JSON mode if function calling fails.
        
        Args:
            goal: The user's goal to achieve
            screen_context: JSON string representation of current screen state
            
        Returns:
            Dictionary containing the action decision from LLM
        """
        try:
            return self.handler.get_decision(goal, screen_context)
        except LLMError as e:
            # If function calling fails for Ollama, try JSON mode as fallback
            if self.config.provider == "ollama" and self.json_fallback:
                error_msg = str(e)
                # Check if it's a function calling related error
                if any(keyword in error_msg.lower() for keyword in [
                    "function call", "tool_call", "tool call", "no function"
                ]):
                    print(
                        f"⚠️ Function calling failed, falling back to JSON mode. "
                        f"Error: {error_msg}"
                    )
                    return self.json_fallback.get_decision(goal, screen_context)
            raise
