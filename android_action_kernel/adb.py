"""ADB command execution and screen capture functionality."""
import os
import json
import subprocess
from typing import List

from . import sanitizer
from .config import Config, SPACE_REPLACEMENT
from .exceptions import ADBError, ScreenCaptureError


def run_adb_command(command: List[str], config: Config, raise_on_error: bool = False) -> str:
    """
    Executes a shell command via ADB.
    
    Args:
        command: List of command arguments (without 'adb' prefix)
        config: Configuration object
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


def get_screen_state(config: Config) -> str:
    """
    Dumps the current UI XML and returns the sanitized JSON string.
    
    Args:
        config: Configuration object
        
    Returns:
        JSON string representation of interactive UI elements
        
    Raises:
        ScreenCaptureError: If screen capture fails
    """
    try:
        # 1. Capture XML
        run_adb_command(["shell", "uiautomator", "dump", config.screen_dump_path], config)
        
        # 2. Pull to local
        run_adb_command(["pull", config.screen_dump_path, config.local_dump_path], config)
        
        # 3. Read & Sanitize
        if not os.path.exists(config.local_dump_path):
            raise ScreenCaptureError("Could not capture screen - dump file not found")
        
        with open(config.local_dump_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        elements = sanitizer.get_interactive_elements(xml_content)
        return json.dumps(elements, indent=2)
        
    except (ADBError, IOError, sanitizer.XMLParseError) as e:
        raise ScreenCaptureError(f"Failed to capture screen state: {str(e)}") from e
