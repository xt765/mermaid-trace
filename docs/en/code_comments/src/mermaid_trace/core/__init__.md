# File: src/mermaid_trace/core/__init__.py

## Overview
The `__init__.py` file in the `core` directory serves as the package initialization file for the core functionality of MermaidTrace. It exposes the key components and functionality of the core module, making them available for import by other parts of the library and by users.

## Core Functionality Analysis

### 1. Module Exports
This file defines what components are exposed when importing from the `mermaid_trace.core` package:
- **Key Classes**: Exports core classes like `FlowEvent`, `MermaidFormatter`, and `LogContext` for direct use.
- **Decorators**: Exports the `trace_interaction` decorator (also aliased as `trace`) for user convenience.
- **Utilities**: Exports configuration and utility functions that might be needed by advanced users.

### 2. Package Structure
The `__init__.py` file helps organize the package structure by:
- **Simplifying Imports**: Allowing users to import core functionality directly from `mermaid_trace.core` instead of from specific submodules.
- **Providing Consistent Interface**: Creating a stable public API that hides internal implementation details and module structure changes.
- **Reducing Import Complexity**: Minimizing the number of import statements needed in user code.

### 3. Version and Metadata
While not always present, the `__init__.py` file can also include:
- **Version Information**: Package version number for tracking and compatibility.
- **Author Information**: Credits and contact details for the package maintainers.
- **License Information**: Legal terms under which the package is distributed.

## Source Code with English Comments

```python
"""
Core functionality package for MermaidTrace

This package contains the fundamental components of MermaidTrace,
including context management, event handling, formatting, and
the core decorator implementation.
"""

from .config import Config, config, ConfigOverrides
from .context import LogContext
from .decorators import trace_interaction, get_flow_logger
from .events import FlowEvent
from .formatter import MermaidFormatter
from .utils import (
    get_module_name,
    get_short_module_name,
    truncate_string,
    sanitize_string,
    safe_operation,
    format_exception,
    is_async_function,
    is_class_method,
    cache_result,
)


# Public API exports
__all__ = [
    # Configuration
    "Config",
    "config",
    "ConfigOverrides",
    
    # Context management
    "LogContext",
    
    # Decorators
    "trace_interaction",
    "get_flow_logger",
    
    # Events
    "FlowEvent",
    
    # Formatting
    "MermaidFormatter",
    
    # Utilities
    "get_module_name",
    "get_short_module_name",
    "truncate_string",
    "sanitize_string",
    "safe_operation",
    "format_exception",
    "is_async_function",
    "is_class_method",
    "cache_result",
]


# Alias for convenience
trace = trace_interaction


# Package version
__version__ = "0.1.0"


# Package metadata
__author__ = "MermaidTrace Team"
__license__ = "MIT"
__description__ = "Core functionality for MermaidTrace - The Python Logger That Draws Diagrams"
```