"""JSON mode handler for LLM interactions."""
import json
from typing import Dict, Any

from openai import OpenAI

from ..config import Config
from ..exceptions import LLMError
from .prompts import get_system_prompt_json_mode
from .debug import print_payload_debug


class JSONModeClient:
    """LLM client using JSON mode (for OpenAI, GLM, etc.)."""
    
    def __init__(self, config: Config, client: OpenAI):
        """
        Initialize JSON mode client.
        
        Args:
            config: Configuration object
            client: OpenAI client instance
        """
        self.config = config
        self.client = client
    
    def get_decision(self, goal: str, screen_context: str) -> Dict[str, Any]:
        """
        Sends screen context to LLM using JSON mode and returns decision.
        
        Args:
            goal: The user's goal to achieve
            screen_context: JSON string representation of current screen state
            
        Returns:
            Dictionary containing the action decision from LLM
            
        Raises:
            LLMError: If LLM API call fails
        """
        print(
            f"🤖 {self.config.provider_name} API: Requesting decision (JSON mode) "
            f"(model: {self.config.model}, url: {self.config.api_url})"
        )
        
        payload = {
            "model": self.config.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": get_system_prompt_json_mode().strip()},
                {
                    "role": "user", 
                    "content": (
                        f"GOAL: {goal}\n\n"
                        f"SCREEN_CONTEXT:\n{screen_context}\n\n"
                        f"IMPORTANT: Output a JSON object with an 'action' field. "
                        f"For example: {{\"action\": \"home\", \"reason\": \"Going to home screen to find YouTube app\"}}\n\n"
                        f"CRITICAL: If the goal '{goal}' has been achieved based on the current screen state, "
                        f"you MUST return {{\"action\": \"done\", \"reason\": \"Goal achieved: [what was accomplished]\"}}. "
                        f"Do NOT continue taking actions after the goal is complete."
                    )
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
            
            # Handle JSON mode response
            content = message.content
            if content is None:
                raise LLMError("Content is None in LLM response")
            
            # Strip whitespace and check if empty
            content = content.strip()
            if not content:
                raise LLMError("Empty or whitespace-only content in LLM response")
            
            print(
                f"✅ {self.config.provider_name} API: Success "
                f"(status: {finish_reason})"
            )
            
            # Debug: Show the JSON response
            if self.config.debug_llm_payload:
                print(f"🔍 Debug - JSON Response: {content[:500]}")
            
            try:
                parsed_json = json.loads(content)
                if self.config.debug_llm_payload:
                    print(f"🔍 Debug - Parsed JSON: {json.dumps(parsed_json, indent=2)}")
                
                # Validate that the response has the required "action" field
                if not isinstance(parsed_json, dict):
                    raise LLMError(
                        f"LLM response is not a JSON object. Got: {type(parsed_json).__name__}\n"
                        f"Response: {content[:200]}"
                    )
                
                if "action" not in parsed_json:
                    raise LLMError(
                        f"LLM response missing required 'action' field.\n"
                        f"Response keys: {list(parsed_json.keys())}\n"
                        f"Response: {content[:300]}"
                    )
                
                return parsed_json
            except json.JSONDecodeError as e:
                # Log the actual content for debugging
                content_preview = content[:200] if len(content) > 200 else content
                error_msg = (
                    f"Failed to parse LLM response as JSON: {str(e)}\n"
                    f"Response content (first 200 chars): {repr(content_preview)}"
                )
                print(f"❌ {self.config.provider_name} API: {error_msg}")
                raise LLMError(error_msg) from e
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ {self.config.provider_name} API: Error - {error_msg}")
            raise LLMError(error_msg) from e
