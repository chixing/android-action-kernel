"""Configuration management for Android Action Kernel."""
import os
from dataclasses import dataclass


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
        elif provider_env == "ollama":
            config.model = os.environ.get("OLLAMA_MODEL", "gemma3")
            config.api_url = os.environ.get(
                "OLLAMA_API_URL", 
                "http://localhost:11434/v1"
            )
            config.api_key = os.environ.get(
                "OLLAMA_API_KEY", 
                "ollama"  # Ollama doesn't require a real key, but some clients expect it
            )
            config.provider_name = "Ollama"
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
