"""Main agent loop for Android automation."""
import time

from .config import Config, DEFAULT_WAIT_SECONDS
from .exceptions import ScreenCaptureError, LLMError, ADBError
from .adb import get_screen_state
from .llm import LLMClient
from .actions import ActionExecutor


class AndroidAgent:
    """Main agent that runs the perception -> reasoning -> action loop."""
    
    def __init__(self, config: Config):
        """
        Initialize Android agent.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.llm_client = LLMClient(config)
        self.action_executor = ActionExecutor(config)
    
    def run(self, goal: str, max_steps: int = 20) -> None:
        """
        Runs the Android agent loop: perception -> reasoning -> action.
        
        Args:
            goal: The goal to achieve
            max_steps: Maximum number of steps to execute
        """
        print(f"🚀 Android Use Agent Started. Goal: {goal}")
        print(f"📡 Using LLM Provider: {self.config.provider_name} ({self.config.model})")
        
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            
            try:
                # 1. Perception
                print("👀 Scanning Screen...")
                screen_context = get_screen_state(self.config)
                
                # 2. Reasoning
                print("🧠 Thinking...")
                decision = self.llm_client.get_decision(goal, screen_context)
                reason = decision.get('reason', 'No reason provided')
                print(f"💡 Decision: {reason}")
                
                # Check if task is complete
                if decision.get('action') == 'done':
                    print("✅ Goal Achieved.")
                    return
                
                # 3. Action
                self.action_executor.execute(decision)
                
                # Wait for UI to update
                time.sleep(DEFAULT_WAIT_SECONDS)
                
            except (ScreenCaptureError, LLMError, ValueError, ADBError) as e:
                print(f"❌ Error in step {step + 1}: {str(e)}")
                raise
