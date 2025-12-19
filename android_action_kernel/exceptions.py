"""Custom exceptions for Android Action Kernel."""


class ADBError(Exception):
    """Exception raised when ADB command fails."""
    pass


class ScreenCaptureError(Exception):
    """Exception raised when screen capture fails."""
    pass


class LLMError(Exception):
    """Exception raised when LLM API call fails."""
    pass
