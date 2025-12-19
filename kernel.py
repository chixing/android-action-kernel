import os
import time
import subprocess
import json
from typing import Dict, Any, List
from openai import OpenAI
import sanitizer

# --- CONFIGURATION ---
ADB_PATH = "adb"  # Ensure adb is in your PATH
SCREEN_DUMP_PATH = "/sdcard/window_dump.xml"
LOCAL_DUMP_PATH = "window_dump.xml"

# Debug Configuration
# Set DEBUG_LLM_PAYLOAD environment variable to "1" or "true" to enable payload debugging
DEBUG_LLM_PAYLOAD = os.environ.get("DEBUG_LLM_PAYLOAD", "false").lower() in ("1", "true", "yes")

# LLM Provider Configuration
# Set LLM_PROVIDER environment variable to "openai" or "glm" (default: "openai")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()

if LLM_PROVIDER == "glm":
    # GLM-4.6 Configuration (Zhipu AI)
    MODEL = "GLM-4.6"
    API_URL = os.environ.get("GLM_API_URL", "https://api.z.ai/api/coding/paas/v4")
    API_KEY = os.environ.get("ZHIPU_API_KEY", os.environ.get("LOCAL_API_KEY", "your-api-key-1"))
    PROVIDER_NAME = "GLM-4.6"
else:
    # OpenAI Configuration (default) - uses localhost API
    MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.1-codex")
    API_URL = os.environ.get("OPENAI_API_URL", "http://localhost:8317/v1")
    API_KEY = os.environ.get("OPENAI_API_KEY", os.environ.get("LOCAL_API_KEY", "your-api-key-1"))
    PROVIDER_NAME = "OpenAI"

client = OpenAI(
    api_key=API_KEY,
    base_url=API_URL
)

def run_adb_command(command: List[str]):
    """Executes a shell command via ADB."""
    full_command = [ADB_PATH] + command
    print(f"🔧 ADB: {' '.join(full_command)}")
    
    result = subprocess.run(full_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ ADB failed (code {result.returncode}): {result.stderr.strip()}")
    
    return result.stdout.strip()

def get_screen_state() -> str:
    """Dumps the current UI XML and returns the sanitized JSON string."""
    # 1. Capture XML
    run_adb_command(["shell", "uiautomator", "dump", SCREEN_DUMP_PATH])
    
    # 2. Pull to local
    run_adb_command(["pull", SCREEN_DUMP_PATH, LOCAL_DUMP_PATH])
    
    # 3. Read & Sanitize
    if not os.path.exists(LOCAL_DUMP_PATH):
        return "Error: Could not capture screen."
        
    with open(LOCAL_DUMP_PATH, "r", encoding="utf-8") as f:
        xml_content = f.read()
        
    elements = sanitizer.get_interactive_elements(xml_content)
    return json.dumps(elements, indent=2)

def execute_action(action: Dict[str, Any]):
    """Executes the action decided by the LLM."""
    act_type = action.get("action")
    
    if act_type == "tap":
        x, y = action.get("coordinates")
        print(f"👉 Tapping: ({x}, {y})")
        run_adb_command(["shell", "input", "tap", str(x), str(y)])
        
    elif act_type == "type":
        text = action.get("text").replace(" ", "%s") # ADB requires %s for spaces
        print(f"⌨️ Typing: {action.get('text')}")
        run_adb_command(["shell", "input", "text", text])
        
    elif act_type == "home":
        print("🏠 Going Home")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_HOME"])
        
    elif act_type == "back":
        print("🔙 Going Back")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
        
    elif act_type == "recent":
        print("📱 Opening Recent Apps")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_APP_SWITCH"])
        
    elif act_type == "settings":
        print("⚙️ Opening Settings")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_SETTINGS"])
        
    elif act_type == "notification":
        print("🔔 Opening Notification Panel")
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_NOTIFICATION"])
        
    elif act_type == "wait":
        print("⏳ Waiting...")
        time.sleep(2)
        
    elif act_type == "done":
        print("✅ Goal Achieved.")
        exit(0)

def print_payload_debug(payload: Dict[str, Any]):
    """Pretty prints the LLM payload for debugging purposes."""
    print("\n" + "="*80)
    print("📤 Payload being sent to LLM:")
    print("="*80)
    print(f"\n🔧 Model: {payload['model']}")
    print(f"📋 Response Format: {json.dumps(payload['response_format'], indent=2)}")
    print(f"\n💬 Messages ({len(payload['messages'])}):")
    print("-"*80)
    
    for i, msg in enumerate(payload['messages'], 1):
        print(f"\n  Message {i} - Role: {msg['role'].upper()}")
        print("  " + "-"*76)
        content = msg['content']
        
        if msg['role'] == 'system':
            # Print system prompt with indentation
            print("  " + content.replace('\n', '\n  '))
        else:
            # Parse and pretty print the user message
            if 'GOAL:' in content:
                goal_part, screen_part = content.split('\n\nSCREEN_CONTEXT:\n', 1)
                print("  " + goal_part.replace('\n', '\n  '))
                print("\n  SCREEN_CONTEXT:")
                try:
                    # Parse the JSON screen context and pretty print it
                    screen_data = json.loads(screen_part)
                    print("  " + json.dumps(screen_data, indent=4, ensure_ascii=False).replace('\n', '\n  '))
                except json.JSONDecodeError:
                    # If it's not valid JSON, just print as-is
                    print("  " + screen_part.replace('\n', '\n  '))
            else:
                print("  " + content.replace('\n', '\n  '))
    
    print("\n" + "="*80 + "\n")

def get_llm_decision(goal: str, screen_context: str) -> Dict[str, Any]:
    """Sends screen context to LLM and asks for the next move."""
    system_prompt = """
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
    
    print(f"🤖 {PROVIDER_NAME} API: Requesting decision (model: {MODEL}, url: {API_URL})")
    
    # Construct the payload
    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"GOAL: {goal}\n\nSCREEN_CONTEXT:\n{screen_context}"}
        ]
    }
    
    # Display the payload if debugging is enabled
    if DEBUG_LLM_PAYLOAD:
        print_payload_debug(payload)
    
    try:
        response = client.chat.completions.create(**payload)
        
        print(f"✅ {PROVIDER_NAME} API: Success (status: {response.choices[0].finish_reason})")
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ {PROVIDER_NAME} API: Error - {type(e).__name__}: {str(e)}")
        raise

def run_agent(goal: str, max_steps=10):
    print(f"🚀 Android Use Agent Started. Goal: {goal}")
    print(f"📡 Using LLM Provider: {PROVIDER_NAME} ({MODEL})")
    
    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")
        
        # 1. Perception
        print("👀 Scanning Screen...")
        screen_context = get_screen_state()
        
        # 2. Reasoning
        print("🧠 Thinking...")
        decision = get_llm_decision(goal, screen_context)
        print(f"💡 Decision: {decision.get('reason')}")
        
        # 3. Action
        execute_action(decision)
        
        # Wait for UI to update
        time.sleep(2)

if __name__ == "__main__":
    # Example Goal: "Open settings and turn on Wi-Fi"
    # Or your demo goal: "Find the 'Connect' button and tap it"
    GOAL = input("Enter your goal: ")
    run_agent(GOAL)
