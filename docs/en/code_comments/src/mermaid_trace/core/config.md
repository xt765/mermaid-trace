# File: src/mermaid_trace/core/config.py

## Overview
The `config.py` module provides a centralized configuration system for MermaidTrace. It defines default settings, environment variable overrides, and a global `config` object that's used throughout the library to control behavior such as argument capturing, string length limits, and depth restrictions.

## Core Functionality Analysis

### 1. `Config` Class
This class encapsulates all configuration options for MermaidTrace:
- **Default Values**: Provides sensible defaults for all configuration options to ensure out-of-the-box functionality.
- **Environment Variable Overrides**: Reads environment variables with the `MERMAID_TRACE_` prefix to allow configuration without code changes.
- **Type Conversion**: Automatically converts environment variable strings to appropriate types (e.g., strings to booleans or integers).
- **Validation**: Ensures configuration values are within reasonable ranges and types.

### 2. Configuration Options
The `Config` class includes the following key configuration options:
- **`capture_args`**: Controls whether function arguments are captured and displayed in diagrams.
- **`max_string_length`**: Limits the length of string representations to prevent log bloat.
- **`max_arg_depth`**: Restricts the recursive depth when formatting nested data structures.
- **`queue_size`**: Sets the size of the async event queue for high-throughput scenarios.

### 3. Global Config Instance
The module creates a global `config` instance that's imported and used throughout the library, ensuring consistent configuration across all components.

### 4. Environment Variable Handling
- **Prefix**: All environment variables use the `MERMAID_TRACE_` prefix to avoid conflicts with other applications.
- **Naming Convention**: Environment variable names match configuration attribute names in uppercase with underscores.
- **Fallback**: If environment variables are not set, the default values are used.

## Source Code with English Comments

```python
"""
Configuration module

This module defines the configuration system for MermaidTrace, including
default settings, environment variable overrides, and a global config
object used throughout the library.
"""

import os
from typing import Any, Dict, Optional


class Config:
    """
    Configuration class for MermaidTrace.
    
    This class manages all configurable options for the library, including
    default values and environment variable overrides.
    """

    def __init__(self) -> None:
        """
        Initialize configuration with defaults and environment variable overrides.
        """
        # Default values
        self._defaults: Dict[str, Any] = {
            "capture_args": True,
            "max_string_length": 200,
            "max_arg_depth": 3,
            "queue_size": 1000,
        }

        # Load from environment variables
        self._load_from_env()

    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables.
        
        Environment variables use the MERMAID_TRACE_ prefix followed by the
        configuration key in uppercase (e.g., MERMAID_TRACE_CAPTURE_ARGS).
        """
        for key, default in self._defaults.items():
            env_key = f"MERMAID_TRACE_{key.upper()}"
            env_value = os.environ.get(env_key)

            if env_value is not None:
                # Convert to appropriate type
                if isinstance(default, bool):
                    setattr(self, key, env_value.lower() == "true")
                elif isinstance(default, int):
                    try:
                        setattr(self, key, int(env_value))
                    except ValueError:
                        setattr(self, key, default)
                else:
                    setattr(self, key, env_value)
            else:
                setattr(self, key, default)

    def update(self, **kwargs: Any) -> None:
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if key in self._defaults:
                setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with optional default.
        
        Args:
            key: Configuration key
            default: Value to return if key not found
            
        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            key: getattr(self, key) for key in self._defaults
        }


# Global config instance
config = Config()


# Type alias for config overrides
ConfigOverrides = Optional[Dict[str, Any]]
```