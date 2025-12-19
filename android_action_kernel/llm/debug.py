"""Debug utilities for LLM payload formatting."""
import json
from typing import Dict, Any

from ..config import DEBUG_SEPARATOR_WIDTH


def format_message_content(content: str, role: str) -> str:
    """
    Formats message content for debug output.
    
    Args:
        content: Message content string
        role: Message role (system/user)
        
    Returns:
        Formatted content string
    """
    if role == 'system':
        return "  " + content.replace('\n', '\n  ')
    
    if 'GOAL:' in content:
        parts = content.split('\n\nSCREEN_CONTEXT:\n', 1)
        if len(parts) == 2:
            goal_part, screen_part = parts
            formatted = "  " + goal_part.replace('\n', '\n  ')
            formatted += "\n\n  SCREEN_CONTEXT:\n"
            try:
                screen_data = json.loads(screen_part)
                formatted += "  " + json.dumps(
                    screen_data, 
                    indent=4, 
                    ensure_ascii=False
                ).replace('\n', '\n  ')
            except json.JSONDecodeError:
                formatted += "  " + screen_part.replace('\n', '\n  ')
            return formatted
    
    return "  " + content.replace('\n', '\n  ')


def print_payload_debug(payload: Dict[str, Any]) -> None:
    """
    Pretty prints the LLM payload for debugging purposes.
    
    Args:
        payload: The payload dictionary to print
    """
    separator = "=" * DEBUG_SEPARATOR_WIDTH
    print(f"\n{separator}")
    print("📤 Payload being sent to LLM:")
    print(separator)
    print(f"\n🔧 Model: {payload['model']}")
    
    if 'response_format' in payload:
        print(f"📋 Response Format: {json.dumps(payload['response_format'], indent=2)}")
    elif 'tools' in payload:
        print(f"🔧 Function Calling: Enabled ({len(payload['tools'])} functions)")
        if 'tool_choice' in payload:
            print(f"📋 Tool Choice: {payload['tool_choice']}")
    
    print(f"\n💬 Messages ({len(payload['messages'])}):")
    print("-" * DEBUG_SEPARATOR_WIDTH)
    
    for i, msg in enumerate(payload['messages'], 1):
        print(f"\n  Message {i} - Role: {msg['role'].upper()}")
        print("  " + "-" * (DEBUG_SEPARATOR_WIDTH - 2))
        formatted_content = format_message_content(msg['content'], msg['role'])
        print(formatted_content)
    
    print(f"\n{separator}\n")
