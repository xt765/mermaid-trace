"""
Configuration Module for Mermaid Trace
======================================

This module provides a centralized configuration system for the library.
It allows users to control behavior globally, such as argument capturing,
string truncation limits, and logging levels.
"""

from dataclasses import dataclass
import os


@dataclass
class MermaidConfig:
    """
    Global configuration settings for Mermaid Trace.

    Attributes:
        capture_args (bool): Whether to capture function arguments and return values.
                             Defaults to True. Set to False for performance or privacy.
        max_string_length (int): Maximum length for string representations of objects.
                                 Defaults to 50. Prevents huge log files.
        max_arg_depth (int): Maximum recursion depth for nested objects (lists/dicts).
                             Defaults to 1.
        queue_size (int): Size of the async queue. Defaults to 1000.
    """

    capture_args: bool = True
    max_string_length: int = 50
    max_arg_depth: int = 1
    queue_size: int = 1000

    @classmethod
    def from_env(cls) -> "MermaidConfig":
        """
        Loads configuration from environment variables.

        Env Vars:
            MERMAID_TRACE_CAPTURE_ARGS (bool): "true"/"false"
            MERMAID_TRACE_MAX_STRING_LENGTH (int)
            MERMAID_TRACE_MAX_ARG_DEPTH (int)
            MERMAID_TRACE_QUEUE_SIZE (int)
        """
        return cls(
            capture_args=os.getenv("MERMAID_TRACE_CAPTURE_ARGS", "true").lower()
            == "true",
            max_string_length=int(os.getenv("MERMAID_TRACE_MAX_STRING_LENGTH", "50")),
            max_arg_depth=int(os.getenv("MERMAID_TRACE_MAX_ARG_DEPTH", "1")),
            queue_size=int(os.getenv("MERMAID_TRACE_QUEUE_SIZE", "1000")),
        )


# Global configuration instance
config = MermaidConfig()
