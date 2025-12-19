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
            "messages": [
                {"role": "system", "content": get_system_prompt_function_calling().strip()},
                {
                    "role": "user", 
                    "content": f"GOAL: {goal}\n\nSCREEN_CONTEXT:\n{screen_context}"
                }
            ]
        }
        
        # Only set tool_choice for non-Ollama providers
        # Ollama may not support "required" tool_choice
        if self.config.provider != "ollama":
            payload["tool_choice"] = "required"  # Force function call
        
        if self.config.debug_llm_payload:
            print_payload_debug(payload)
        
        try:
            response = self.client.chat.completions.create(**payload)
            
            if not response.choices:
                raise LLMError("No choices in LLM response")
            
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            message = choice.message
            
            # Debug: Print response details
            if self.config.debug_llm_payload:
                print(f"🔍 Debug - Finish reason: {finish_reason}")
                print(f"🔍 Debug - Message content: {message.content}")
                print(f"🔍 Debug - Tool calls: {message.tool_calls}")
                print(f"🔍 Debug - Message object: {message}")
            
            # Handle function calling response
            if not message.tool_calls or len(message.tool_calls) == 0:
                # Try to extract function call from content if tool_calls is missing
                # Some Ollama models might return function calls in content instead
                if message.content:
                    error_msg = (
                        f"No function call in LLM response. "
                        f"Finish reason: {finish_reason}, "
                        f"Content: {message.content[:200]}"
                    )
                else:
                    error_msg = (
                        f"No function call in LLM response. "
                        f"Finish reason: {finish_reason}"
                    )
                raise LLMError(error_msg)
            
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            
            # Parse function arguments
            try:
                function_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                # Try to handle malformed JSON from Ollama
                error_msg = (
                    f"Failed to parse function arguments as JSON: {str(e)}\n"
                    f"Raw arguments: {repr(tool_call.function.arguments)}"
                )
                print(f"❌ {self.config.provider_name} API: {error_msg}")
                raise LLMError(error_msg) from e
            
            # Convert function call to action format
            action = {
                "action": function_name,
                "reason": function_args.get("reason", "No reason provided")
            }
            
            # Add action-specific parameters with type conversion for Ollama
            if function_name == "tap":
                coordinates = function_args.get("coordinates", [])
                if not coordinates:
                    raise LLMError("Tap action missing 'coordinates' field")
                
                # Ollama may return coordinates as strings, convert to numbers
                try:
                    if isinstance(coordinates, list) and len(coordinates) == 2:
                        # Convert string coordinates to numbers if needed
                        coords = [
                            float(coordinates[0]) if isinstance(coordinates[0], str) else float(coordinates[0]),
                            float(coordinates[1]) if isinstance(coordinates[1], str) else float(coordinates[1])
                        ]
                        action["coordinates"] = [int(coords[0]), int(coords[1])]
                    else:
                        raise LLMError(f"Invalid coordinates format: {coordinates}")
                except (ValueError, TypeError, IndexError) as e:
                    raise LLMError(f"Failed to parse coordinates: {coordinates}") from e
                    
            elif function_name == "type":
                text = function_args.get("text")
                if not text:
                    raise LLMError("Type action missing 'text' field")
                action["text"] = str(text)
            
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
