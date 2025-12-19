import os
import sys
import time
import subprocess
import json
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from openai import OpenAI
import sanitizer


# --- CONSTANTS ---
DEFAULT_WAIT_SECONDS = 2
DEBUG_SEPARATOR_WIDTH = 80
SPACE_REPLACEMENT = "%s"  # ADB requires %s for spaces in text input


@dataclass
class Config:
    """Configuration for the Android Action Kernel."""
    
    # ADB Configuration
    adb_path: str = "adb"
    screen_dump_path: str = "/sdcard/window_dump.xml"
    local_dump_path: str = "window_dump.xml"
    
    # Debug Configuration
    debug_llm_payload: bool = False
    
    # LLM Provider Configuration
    provider: str = "openai"
    model: str = ""
    api_url: str = ""
    api_key: str = ""
    provider_name: str = ""
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()
        
        # Debug configuration
        debug_env = os.environ.get("DEBUG_LLM_PAYLOAD", "false").lower()
        config.debug_llm_payload = debug_env in ("1", "true", "yes")
        
        # LLM Provider configuration
        provider_env = os.environ.get("LLM_PROVIDER", "openai").lower()
        config.provider = provider_env
        
        if provider_env == "glm":
            config.model = "GLM-4.6"
            config.api_url = os.environ.get(
                "GLM_API_URL", 
                "https://api.z.ai/api/coding/paas/v4"
            )
            config.api_key = os.environ.get(
                "ZHIPU_API_KEY", 
                os.environ.get("LOCAL_API_KEY", "your-api-key-1")
            )
            config.provider_name = "GLM-4.6"
        else:
            config.model = os.environ.get("OPENAI_MODEL", "gpt-5.1-codex")
            config.api_url = os.environ.get(
                "OPENAI_API_URL", 
                "http://localhost:8317/v1"
            )
            config.api_key = os.environ.get(
                "OPENAI_API_KEY", 
                os.environ.get("LOCAL_API_KEY", "your-api-key-1")
            )
            config.provider_name = "OpenAI"
        
        return config


# Initialize configuration
config = Config.from_env()

# Initialize OpenAI client
client = OpenAI(
    api_key=config.api_key,
    base_url=config.api_url
)

class ADBError(Exception):
    """Exception raised when ADB command fails."""
    pass


def run_adb_command(command: List[str], raise_on_error: bool = False) -> str:
    """
    Executes a shell command via ADB.
    
    Args:
        command: List of command arguments (without 'adb' prefix)
        raise_on_error: If True, raise ADBError on failure instead of just printing
        
    Returns:
        Command output as string
        
    Raises:
        ADBError: If command fails and raise_on_error is True
    """
    full_command = [config.adb_path] + command
    print(f"🔧 ADB: {' '.join(full_command)}")
    
    result = subprocess.run(full_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        error_msg = f"ADB failed (code {result.returncode}): {result.stderr.strip()}"
        print(f"❌ {error_msg}")
        if raise_on_error:
            raise ADBError(error_msg)
    
    return result.stdout.strip()

class ScreenCaptureError(Exception):
    """Exception raised when screen capture fails."""
    pass


def get_screen_state() -> str:
    """
    Dumps the current UI XML and returns the sanitized JSON string.
    
    Returns:
        JSON string representation of interactive UI elements
        
    Raises:
        ScreenCaptureError: If screen capture fails
    """
    try:
        # 1. Capture XML
        run_adb_command(["shell", "uiautomator", "dump", config.screen_dump_path])
        
        # 2. Pull to local
        run_adb_command(["pull", config.screen_dump_path, config.local_dump_path])
        
        # 3. Read & Sanitize
        if not os.path.exists(config.local_dump_path):
            raise ScreenCaptureError("Could not capture screen - dump file not found")
        
        with open(config.local_dump_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        elements = sanitizer.get_interactive_elements(xml_content)
        return json.dumps(elements, indent=2)
        
    except (ADBError, IOError, sanitizer.XMLParseError) as e:
        raise ScreenCaptureError(f"Failed to capture screen state: {str(e)}") from e

class ActionExecutor:
    """Handles execution of actions decided by the LLM."""
    
    def __init__(self):
        self._action_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {
            "tap": self._handle_tap,
            "type": self._handle_type,
            "home": self._handle_home,
            "back": self._handle_back,
            "recent": self._handle_recent,
            "settings": self._handle_settings,
            "notification": self._handle_notification,
            "wait": self._handle_wait,
            "done": self._handle_done,
        }
    
    def execute(self, action: Dict[str, Any]) -> None:
        """
        Executes the action decided by the LLM.
        
        Args:
            action: Dictionary containing action type and parameters
            
        Raises:
            ValueError: If action type is not recognized
        """
        action_type = action.get("action")
        if not action_type:
            raise ValueError("Action missing 'action' field")
        
        handler = self._action_handlers.get(action_type)
        if not handler:
            raise ValueError(f"Unknown action type: {action_type}")
        
        handler(action)
    
    def _handle_tap(self, action: Dict[str, Any]) -> None:
        """Handle tap action."""
        coordinates = action.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Tap action requires 'coordinates' [x, y]")
        
        x, y = coordinates
        print(f"👉 Tapping: ({x}, {y})")
        run_adb_command(["shell", "input", "tap", str(x), str(y)])
    
    def _handle_type(self, action: Dict[str, Any]) -> None:
        """Handle type action."""
        text = action.get("text")
        if not text:
            raise ValueError("Type action requires 'text' field")
        
        # ADB requires %s for spaces
        adb_text = text.replace(" ", SPACE_REPLACEMENT)
        print(f"⌨️ Typing: {text}")
        run_adb_command(["shell", "input", "text", adb_text])
    
    def _handle_home(self, action: Dict[str, Any]) -> None:
        """Handle home action."""
        print("🏠 Going Home")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_HOME"])
    
    def _handle_back(self, action: Dict[str, Any]) -> None:
        """Handle back action."""
        print("🔙 Going Back")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
    
    def _handle_recent(self, action: Dict[str, Any]) -> None:
        """Handle recent apps action."""
        print("📱 Opening Recent Apps")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_APP_SWITCH"])
    
    def _handle_settings(self, action: Dict[str, Any]) -> None:
        """Handle settings action."""
        print("⚙️ Opening Settings")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_SETTINGS"])
    
    def _handle_notification(self, action: Dict[str, Any]) -> None:
        """Handle notification panel action."""
        print("🔔 Opening Notification Panel")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_NOTIFICATION"])
    
    def _handle_wait(self, action: Dict[str, Any]) -> None:
        """Handle wait action."""
        print("⏳ Waiting...")
        time.sleep(DEFAULT_WAIT_SECONDS)
    
    def _handle_done(self, action: Dict[str, Any]) -> None:
        """Handle done action - exits the program."""
        print("✅ Goal Achieved.")
        sys.exit(0)


# Global action executor instance
_action_executor = ActionExecutor()


def execute_action(action: Dict[str, Any]) -> None:
    """Executes the action decided by the LLM."""
    _action_executor.execute(action)

def _format_message_content(content: str, role: str) -> str:
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
    print(f"📋 Response Format: {json.dumps(payload['response_format'], indent=2)}")
    print(f"\n💬 Messages ({len(payload['messages'])}):")
    print("-" * DEBUG_SEPARATOR_WIDTH)
    
    for i, msg in enumerate(payload['messages'], 1):
        print(f"\n  Message {i} - Role: {msg['role'].upper()}")
        print("  " + "-" * (DEBUG_SEPARATOR_WIDTH - 2))
        formatted_content = _format_message_content(msg['content'], msg['role'])
        print(formatted_content)
    
    print(f"\n{separator}\n")

class LLMError(Exception):
    """Exception raised when LLM API call fails."""
    pass


def _get_system_prompt() -> str:
    """Returns the system prompt for the Android Driver Agent."""
    return """
    You are an Android Driver Agent. Your job is to achieve the user's goal by navigating the UI.
    
    You will receive:
    1. The User's Goal.
    2. A list of interactive UI elements (JSON) with their (x,y) center coordinates.
    
    You must output ONLY a valid JSON object with your next action.
    
    Available Actions:
    - {"action": "tap", "coordinates": [x, y], "reason": "Why you are tapping"}
    - {"action": "type", "text": "Hello World", "reason": "Why you are typing"}
    - {"action": "home", "reason": "Go to home screen"}
    - {"action": "back", "reason": "Go back"}
    - {"action": "recent", "reason": "Open recent apps screen"}
    - {"action": "settings", "reason": "Open Android settings"}
    - {"action": "notification", "reason": "Open notification panel"}
    - {"action": "wait", "reason": "Wait for loading"}
    - {"action": "done", "reason": "Task complete"}
    
    Example Output:
    {"action": "tap", "coordinates": [540, 1200], "reason": "Clicking the 'Connect' button"}
    """


def get_llm_decision(goal: str, screen_context: str) -> Dict[str, Any]:
    """
    Sends screen context to LLM and asks for the next move.
    
    Args:
        goal: The user's goal to achieve
        screen_context: JSON string representation of current screen state
        
    Returns:
        Dictionary containing the action decision from LLM
        
    Raises:
        LLMError: If LLM API call fails
    """
    print(
        f"🤖 {config.provider_name} API: Requesting decision "
        f"(model: {config.model}, url: {config.api_url})"
    )
    
    payload = {
        "model": config.model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _get_system_prompt().strip()},
            {
                "role": "user", 
                "content": f"GOAL: {goal}\n\nSCREEN_CONTEXT:\n{screen_context}"
            }
        ]
    }
    
    if config.debug_llm_payload:
        print_payload_debug(payload)
    
    try:
        response = client.chat.completions.create(**payload)
        
        if not response.choices:
            raise LLMError("No choices in LLM response")
        
        choice = response.choices[0]
        finish_reason = choice.finish_reason
        content = choice.message.content
        
        if not content:
            raise LLMError("Empty content in LLM response")
        
        print(
            f"✅ {config.provider_name} API: Success "
            f"(status: {finish_reason})"
        )
        
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"❌ {config.provider_name} API: {error_msg}")
        raise LLMError(error_msg) from e
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ {config.provider_name} API: Error - {error_msg}")
        raise LLMError(error_msg) from e

def run_agent(goal: str, max_steps: int = 10) -> None:
    """
    Runs the Android agent loop: perception -> reasoning -> action.
    
    Args:
        goal: The goal to achieve
        max_steps: Maximum number of steps to execute
    """
    print(f"🚀 Android Use Agent Started. Goal: {goal}")
    print(f"📡 Using LLM Provider: {config.provider_name} ({config.model})")
    
    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")
        
        try:
            # 1. Perception
            print("👀 Scanning Screen...")
            screen_context = get_screen_state()
            
            # 2. Reasoning
            print("🧠 Thinking...")
            decision = get_llm_decision(goal, screen_context)
            reason = decision.get('reason', 'No reason provided')
            print(f"💡 Decision: {reason}")
            
            # 3. Action
            execute_action(decision)
            
            # Wait for UI to update
            time.sleep(DEFAULT_WAIT_SECONDS)
            
        except (ScreenCaptureError, LLMError, ValueError, ADBError) as e:
            print(f"❌ Error in step {step + 1}: {str(e)}")
            raise

if __name__ == "__main__":
    # Example Goal: "Open settings and turn on Wi-Fi"
    # Or your demo goal: "Find the 'Connect' button and tap it"
    try:
        goal = input("Enter your goal: ")
        if not goal.strip():
            print("❌ Error: Goal cannot be empty")
            sys.exit(1)
        run_agent(goal.strip())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
