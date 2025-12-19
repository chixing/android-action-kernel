"""Action execution handlers for Android actions."""
import sys
import time
from typing import Dict, Any, Callable

from .config import Config, DEFAULT_WAIT_SECONDS, SPACE_REPLACEMENT
from .adb import run_adb_command


class ActionExecutor:
    """Handles execution of actions decided by the LLM."""
    
    def __init__(self, config: Config):
        """
        Initialize action executor.
        
        Args:
            config: Configuration object
        """
        self.config = config
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
        run_adb_command(["shell", "input", "tap", str(x), str(y)], self.config)
    
    def _handle_type(self, action: Dict[str, Any]) -> None:
        """Handle type action."""
        text = action.get("text")
        if not text:
            raise ValueError("Type action requires 'text' field")
        
        # ADB requires %s for spaces
        adb_text = text.replace(" ", SPACE_REPLACEMENT)
        print(f"⌨️ Typing: {text}")
        run_adb_command(["shell", "input", "text", adb_text], self.config)
    
    def _handle_home(self, action: Dict[str, Any]) -> None:
        """Handle home action."""
        print("🏠 Going Home")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_HOME"], self.config)
    
    def _handle_back(self, action: Dict[str, Any]) -> None:
        """Handle back action."""
        print("🔙 Going Back")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"], self.config)
    
    def _handle_recent(self, action: Dict[str, Any]) -> None:
        """Handle recent apps action."""
        print("📱 Opening Recent Apps")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_APP_SWITCH"], self.config)
    
    def _handle_settings(self, action: Dict[str, Any]) -> None:
        """Handle settings action."""
        print("⚙️ Opening Settings")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_SETTINGS"], self.config)
    
    def _handle_notification(self, action: Dict[str, Any]) -> None:
        """Handle notification panel action."""
        print("🔔 Opening Notification Panel")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_NOTIFICATION"], self.config)
    
    def _handle_wait(self, action: Dict[str, Any]) -> None:
        """Handle wait action."""
        print("⏳ Waiting...")
        time.sleep(DEFAULT_WAIT_SECONDS)
    
    def _handle_done(self, action: Dict[str, Any]) -> None:
        """Handle done action - exits the program."""
        print("✅ Goal Achieved.")
        sys.exit(0)
