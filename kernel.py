"""
Android Action Kernel - Main entry point.
"""
import sys

from android_action_kernel import Config, AndroidAgent

if __name__ == "__main__":
    # Example Goal: "Open settings and turn on Wi-Fi"
    # Or your demo goal: "Find the 'Connect' button and tap it"
    try:
        goal = input("Enter your goal: ")
        if not goal.strip():
            print("❌ Error: Goal cannot be empty")
            sys.exit(1)
        
        config = Config.from_env()
        agent = AndroidAgent(config)
        agent.run(goal.strip())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
