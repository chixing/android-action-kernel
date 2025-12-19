"""Action execution handlers for Android actions."""
import time
import re
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
            "swipe": self._handle_swipe,
            "swipe_down": self._handle_swipe_down,
            "swipe_up": self._handle_swipe_up,
            "swipe_left": self._handle_swipe_left,
            "swipe_right": self._handle_swipe_right,
            "long_press": self._handle_long_press,
            "key": self._handle_key,
            "open_app": self._handle_open_app,
            "get_current_app": self._handle_get_current_app,
            "get_device_info": self._handle_get_device_info,
            "get_screen_info": self._handle_get_screen_info,
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
        
        # Map common invalid actions to valid ones
        action_mapping = {
            "launch_app": "open_app",
            "navigate": "home",
            "click": "tap",
            "press": "tap",
            "scroll": "swipe_down",
            "scroll_down": "swipe_down",
            "scroll_up": "swipe_up",
        }
        
        # Try to map invalid action to valid one
        if action_type not in self._action_handlers:
            mapped_action = action_mapping.get(action_type.lower())
            if mapped_action:
                print(f"⚠️ Mapped invalid action '{action_type}' to '{mapped_action}'")
                action_type = mapped_action
                action["action"] = mapped_action
        
        handler = self._action_handlers.get(action_type)
        if not handler:
            valid_actions = ", ".join(self._action_handlers.keys())
            raise ValueError(
                f"Unknown action type: {action_type}. "
                f"Valid actions are: {valid_actions}"
            )
        
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
    
    def _get_screen_dimensions(self):
        """
        Get screen dimensions from device.
        
        Returns:
            Tuple of (width, height)
        """
        try:
            # Get display size via ADB
            output = run_adb_command(
                ["shell", "wm", "size"], 
                self.config, 
                raise_on_error=False
            )
            # Output format: "Physical size: 1080x1920" or "1080x1920"
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
            else:
                size_str = output.strip()
            
            width, height = map(int, size_str.split("x"))
            return width, height
        except Exception:
            # Default to common Android screen size if query fails
            return 1080, 1920
    
    def _handle_swipe(self, action: Dict[str, Any]) -> None:
        """Handle swipe action."""
        start = action.get("start")
        end = action.get("end")
        duration = action.get("duration", 300)  # Default 300ms
        
        if not start or len(start) != 2:
            raise ValueError("Swipe action requires 'start' [x, y]")
        if not end or len(end) != 2:
            raise ValueError("Swipe action requires 'end' [x, y]")
        
        x1, y1 = start
        x2, y2 = end
        print(f"👆 Swiping: ({x1}, {y1}) → ({x2}, {y2})")
        run_adb_command([
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration)
        ], self.config)
    
    def _handle_swipe_down(self, action: Dict[str, Any]) -> None:
        """Handle swipe down (scroll down) action."""
        width, height = self._get_screen_dimensions()
        # Swipe from upper-middle to lower-middle
        start = [width // 2, height // 3]
        end = [width // 2, height * 2 // 3]
        duration = action.get("duration", 300)
        print("⬇️ Swiping Down")
        run_adb_command([
            "shell", "input", "swipe",
            str(start[0]), str(start[1]), str(end[0]), str(end[1]), str(duration)
        ], self.config)
    
    def _handle_swipe_up(self, action: Dict[str, Any]) -> None:
        """Handle swipe up (scroll up) action."""
        width, height = self._get_screen_dimensions()
        # Swipe from lower-middle to upper-middle
        start = [width // 2, height * 2 // 3]
        end = [width // 2, height // 3]
        duration = action.get("duration", 300)
        print("⬆️ Swiping Up")
        run_adb_command([
            "shell", "input", "swipe",
            str(start[0]), str(start[1]), str(end[0]), str(end[1]), str(duration)
        ], self.config)
    
    def _handle_swipe_left(self, action: Dict[str, Any]) -> None:
        """Handle swipe left action."""
        width, height = self._get_screen_dimensions()
        # Swipe from right-middle to left-middle
        start = [width * 2 // 3, height // 2]
        end = [width // 3, height // 2]
        duration = action.get("duration", 300)
        print("⬅️ Swiping Left")
        run_adb_command([
            "shell", "input", "swipe",
            str(start[0]), str(start[1]), str(end[0]), str(end[1]), str(duration)
        ], self.config)
    
    def _handle_swipe_right(self, action: Dict[str, Any]) -> None:
        """Handle swipe right action."""
        width, height = self._get_screen_dimensions()
        # Swipe from left-middle to right-middle
        start = [width // 3, height // 2]
        end = [width * 2 // 3, height // 2]
        duration = action.get("duration", 300)
        print("➡️ Swiping Right")
        run_adb_command([
            "shell", "input", "swipe",
            str(start[0]), str(start[1]), str(end[0]), str(end[1]), str(duration)
        ], self.config)
    
    def _handle_long_press(self, action: Dict[str, Any]) -> None:
        """Handle long press action."""
        coordinates = action.get("coordinates")
        duration = action.get("duration", 1000)  # Default 1 second
        
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Long press requires 'coordinates' [x, y]")
        
        x, y = coordinates
        print(f"👆 Long pressing: ({x}, {y}) for {duration}ms")
        # Long press = swipe from same point to same point with duration
        run_adb_command([
            "shell", "input", "swipe",
            str(x), str(y), str(x), str(y), str(duration)
        ], self.config)
    
    def _handle_key(self, action: Dict[str, Any]) -> None:
        """Handle keyboard key press action."""
        keycode = action.get("keycode")
        if not keycode:
            raise ValueError("Key action requires 'keycode' field")
        
        # Map common keycode names to ADB keyevent codes
        keycode_map = {
            "KEYCODE_ENTER": "66",
            "KEYCODE_DEL": "67",
            "KEYCODE_TAB": "61",
            "KEYCODE_DPAD_UP": "19",
            "KEYCODE_DPAD_DOWN": "20",
            "KEYCODE_DPAD_LEFT": "21",
            "KEYCODE_DPAD_RIGHT": "22",
            "KEYCODE_MENU": "82",
            "KEYCODE_SEARCH": "84",
            "KEYCODE_CLEAR": "28",
        }
        
        # Use mapped value or assume it's already a number
        keycode_value = keycode_map.get(keycode.upper(), keycode)
        
        print(f"⌨️ Pressing key: {keycode}")
        run_adb_command([
            "shell", "input", "keyevent", str(keycode_value)
        ], self.config)
    
    def _handle_open_app(self, action: Dict[str, Any]) -> None:
        """Handle open app action."""
        package = action.get("package")
        if not package:
            raise ValueError("Open app requires 'package' field")
        
        print(f"📱 Opening app: {package}")
        # Try monkey command first (simpler, doesn't need activity name)
        result = run_adb_command([
            "shell", "monkey", "-p", package,
            "-c", "android.intent.category.LAUNCHER", "1"
        ], self.config, raise_on_error=False)
        
        # Check if it failed by trying to verify the app is running
        # If monkey fails silently, we'll still try to verify
        time.sleep(0.5)  # Give app time to launch
        
        # Verify app launched by checking current package
        try:
            current_package = run_adb_command([
                "shell", "dumpsys", "window", "windows"
            ], self.config, raise_on_error=False)
            if package in current_package:
                return  # Success
        except Exception:
            pass
        
        # If verification unclear, assume it worked (monkey usually works)
        # Could raise error here if needed, but many apps launch successfully
    
    def _handle_get_current_app(self, action: Dict[str, Any]) -> None:
        """Handle get current app action - outputs current app package/activity."""
        print("🔍 Getting current app information...")
        
        try:
            # Get current focused app from window manager
            output = run_adb_command([
                "shell", "dumpsys", "window", "windows"
            ], self.config, raise_on_error=False)
            
            # Parse the output to find mCurrentFocus or mFocusedApp
            package = None
            activity = None
            
            for line in output.split('\n'):
                if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                    # Format: mCurrentFocus=Window{... package/activity}
                    # Or: mFocusedApp=AppWindowToken{... package/activity}
                    if '/' in line:
                        parts = line.split('/')
                        if len(parts) >= 2:
                            # Extract package and activity
                            pkg_part = parts[0]
                            act_part = parts[1].split()[0].split('}')[0]
                            
                            # Extract package name (usually before the last /)
                            if '.' in pkg_part:
                                package = pkg_part.split()[-1].split('/')[-1]
                            else:
                                # Try to extract from the full line
                                match = re.search(r'([a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*)', line)
                                if match:
                                    package = match.group(1)
                            
                            activity = act_part.strip()
                            break
            
            # Alternative method: use dumpsys activity
            if not package:
                try:
                    act_output = run_adb_command([
                        "shell", "dumpsys", "activity", "activities"
                    ], self.config, raise_on_error=False)
                    
                    # Look for mResumedActivity or mLastPausedActivity
                    for line in act_output.split('\n'):
                        if 'mResumedActivity' in line or 'mLastPausedActivity' in line:
                            if '/' in line:
                                parts = line.split('/')
                                if len(parts) >= 2:
                                    pkg = parts[0].split()[-1]
                                    act = parts[1].split()[0].split('}')[0]
                                    if '.' in pkg:
                                        package = pkg
                                        activity = act
                                        break
                except Exception:
                    pass
            
            if package:
                print(f"📱 Current App:")
                print(f"   Package: {package}")
                if activity:
                    print(f"   Activity: {activity}")
                print(f"   Full: {package}/{activity if activity else 'unknown'}")
            else:
                print("⚠️ Could not determine current app")
                print(f"   Raw output: {output[:200]}...")
                
        except Exception as e:
            print(f"❌ Failed to get current app: {str(e)}")
    
    def _handle_get_device_info(self, action: Dict[str, Any]) -> None:
        """Handle get device info action - outputs device information."""
        print("🔍 Getting device information...")
        
        try:
            info = {}
            
            # Get device model
            try:
                model = run_adb_command([
                    "shell", "getprop", "ro.product.model"
                ], self.config, raise_on_error=False).strip()
                if model:
                    info["model"] = model
            except Exception:
                pass
            
            # Get Android version
            try:
                version = run_adb_command([
                    "shell", "getprop", "ro.build.version.release"
                ], self.config, raise_on_error=False).strip()
                if version:
                    info["android_version"] = version
            except Exception:
                pass
            
            # Get API level
            try:
                api_level = run_adb_command([
                    "shell", "getprop", "ro.build.version.sdk"
                ], self.config, raise_on_error=False).strip()
                if api_level:
                    info["api_level"] = api_level
            except Exception:
                pass
            
            # Get manufacturer
            try:
                manufacturer = run_adb_command([
                    "shell", "getprop", "ro.product.manufacturer"
                ], self.config, raise_on_error=False).strip()
                if manufacturer:
                    info["manufacturer"] = manufacturer
            except Exception:
                pass
            
            # Get device name
            try:
                device = run_adb_command([
                    "shell", "getprop", "ro.product.device"
                ], self.config, raise_on_error=False).strip()
                if device:
                    info["device"] = device
            except Exception:
                pass
            
            # Get screen density
            try:
                density = run_adb_command([
                    "shell", "wm", "density"
                ], self.config, raise_on_error=False).strip()
                if density:
                    info["density"] = density
            except Exception:
                pass
            
            if info:
                print("📱 Device Information:")
                for key, value in info.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            else:
                print("⚠️ Could not retrieve device information")
                
        except Exception as e:
            print(f"❌ Failed to get device info: {str(e)}")
    
    def _handle_get_screen_info(self, action: Dict[str, Any]) -> None:
        """Handle get screen info action - outputs screen dimensions and orientation."""
        print("🔍 Getting screen information...")
        
        try:
            width, height = self._get_screen_dimensions()
            
            # Get orientation
            try:
                orientation_output = run_adb_command([
                    "shell", "dumpsys", "input"
                ], self.config, raise_on_error=False)
                
                orientation = "unknown"
                if "mSurfaceOrientation=0" in orientation_output or "mSurfaceOrientation=2" in orientation_output:
                    orientation = "portrait"
                elif "mSurfaceOrientation=1" in orientation_output or "mSurfaceOrientation=3" in orientation_output:
                    orientation = "landscape"
            except Exception:
                orientation = "unknown"
            
            # Get density
            try:
                density_output = run_adb_command([
                    "shell", "wm", "density"
                ], self.config, raise_on_error=False)
                density = density_output.strip() if density_output else "unknown"
            except Exception:
                density = "unknown"
            
            print("📱 Screen Information:")
            print(f"   Dimensions: {width}x{height}")
            print(f"   Orientation: {orientation}")
            print(f"   Density: {density}")
            print(f"   Aspect Ratio: {width/height:.2f}")
            
        except Exception as e:
            print(f"❌ Failed to get screen info: {str(e)}")
    
    def _handle_done(self, action: Dict[str, Any]) -> None:
        """Handle done action - task is complete."""
        print("✅ Goal Achieved.")
        # Note: The agent loop will handle exiting when it sees this action
