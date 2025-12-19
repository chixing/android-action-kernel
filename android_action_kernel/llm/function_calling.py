"""Function calling handler for LLM interactions."""
import json
from typing import Dict, Any

from openai import OpenAI

from ..config import Config
from ..exceptions import LLMError
from .prompts import get_system_prompt_function_calling, get_action_tools
from .debug import print_payload_debug


class FunctionCallingClient:
    """LLM client using function calling (for Ollama, etc.)."""
    
    def __init__(self, config: Config, client: OpenAI):
        """
        Initialize function calling client.
        
        Args:
            config: Configuration object
            client: OpenAI client instance
        """
        self.config = config
        self.client = client
    
    def get_decision(self, goal: str, screen_context: str) -> Dict[str, Any]:
        """
        Sends screen context to LLM using function calling and returns decision.
        
        Args:
            goal: The user's goal to achieve
            screen_context: JSON string representation of current screen state
            
        Returns:
            Dictionary containing the action decision from LLM
            
        Raises:
            LLMError: If LLM API call fails
        """
        print(
            f"🤖 {self.config.provider_name} API: Requesting decision (Function Calling) "
            f"(model: {self.config.model}, url: {self.config.api_url})"
        )
        
        payload = {
            "model": self.config.model,
            "tools": get_action_tools(),
            "tool_choice": "required",  # Force function call
            "messages": [
                {"role": "system", "content": get_system_prompt_function_calling().strip()},
                {
                    "role": "user", 
                    "content": f"GOAL: {goal}\n\nSCREEN_CONTEXT:\n{screen_context}"
                }
            ]
        }
        
        if self.config.debug_llm_payload:
            print_payload_debug(payload)
        
        try:
            response = self.client.chat.completions.create(**payload)
            
            if not response.choices:
                raise LLMError("No choices in LLM response")
            
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            message = choice.message
            
            # Handle function calling response
            if not message.tool_calls or len(message.tool_calls) == 0:
                raise LLMError("No function call in LLM response")
            
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Convert function call to action format
            action = {
                "action": function_name,
                "reason": function_args.get("reason", "No reason provided")
            }
            
            # Add action-specific parameters
            if function_name == "tap":
                action["coordinates"] = function_args["coordinates"]
            elif function_name == "type":
                action["text"] = function_args["text"]
            
            print(
                f"✅ {self.config.provider_name} API: Success "
                f"(function: {function_name}, status: {finish_reason})"
            )
            
            return action
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse function arguments as JSON: {str(e)}"
            print(f"❌ {self.config.provider_name} API: {error_msg}")
            raise LLMError(error_msg) from e
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ {self.config.provider_name} API: Error - {error_msg}")
            raise LLMError(error_msg) from e
