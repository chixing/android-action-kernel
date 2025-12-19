"""Shared prompts and function definitions for LLM interactions."""
from typing import Dict, Any, List


def get_system_prompt_json_mode() -> str:
    """Returns the system prompt for JSON mode (OpenAI, GLM, etc.)."""
    return """
    You are an Android Driver Agent. Your job is to achieve the user's goal by navigating the UI.
    
    CRITICAL: You MUST output ONLY a valid JSON object with an "action" field. Do NOT output descriptions, explanations, or any other content.
    
    You will receive:
    1. The User's Goal (what the user wants to accomplish)
    2. A list of interactive UI elements (JSON) with their (x,y) center coordinates
    
    Your response MUST be a JSON object with one of these formats:
    
    For tapping on screen:
    {"action": "tap", "coordinates": [x, y], "reason": "Why you are tapping"}
    
    For typing text:
    {"action": "type", "text": "text to type", "reason": "Why you are typing"}
    
    For navigation:
    {"action": "home", "reason": "Go to home screen"}
    {"action": "back", "reason": "Go back"}
    {"action": "recent", "reason": "Open recent apps screen"}
    {"action": "settings", "reason": "Open Android settings"}
    {"action": "notification", "reason": "Open notification panel"}
    {"action": "wait", "reason": "Wait for loading"}
    {"action": "done", "reason": "Task complete"}
    
    Example Output:
    {"action": "tap", "coordinates": [540, 1200], "reason": "Clicking the 'Connect' button"}
    
    Remember: Output ONLY the JSON object, nothing else. The "action" field is REQUIRED.
    """


def get_system_prompt_function_calling() -> str:
    """Returns the system prompt for function calling mode (Ollama, etc.)."""
    return """
    You are an Android Driver Agent. Your job is to achieve the user's goal by navigating the UI.
    
    You will receive:
    1. The User's Goal.
    2. A list of interactive UI elements (JSON) with their (x,y) center coordinates.
    
    You must call one of the available action functions to perform the next step.
    Always provide a clear reason for your action.
    """


def get_action_tools() -> List[Dict[str, Any]]:
    """Returns the function definitions for available actions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "tap",
                "description": "Tap on the screen at the specified coordinates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "The [x, y] coordinates to tap",
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why you are tapping at this location"
                        }
                    },
                    "required": ["coordinates", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "type",
                "description": "Type text into the current input field",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to type"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why you are typing this text"
                        }
                    },
                    "required": ["text", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "home",
                "description": "Navigate to the home screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are going to the home screen"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "back",
                "description": "Go back to the previous screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are going back"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recent",
                "description": "Open the recent apps screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are opening recent apps"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "settings",
                "description": "Open Android settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are opening settings"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "notification",
                "description": "Open the notification panel",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are opening notifications"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "wait",
                "description": "Wait for the UI to load or update",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why you are waiting"
                        }
                    },
                    "required": ["reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "done",
                "description": "Indicate that the goal has been achieved and exit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why the task is complete"
                        }
                    },
                    "required": ["reason"]
                }
            }
        }
    ]
