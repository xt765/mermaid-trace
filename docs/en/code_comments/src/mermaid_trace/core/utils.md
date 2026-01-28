# File: src/mermaid_trace/core/utils.py

## Overview
The `utils.py` module provides utility functions and helper methods for MermaidTrace. These functions support various internal operations such as module path resolution, string manipulation, and error handling utilities that are used across different components of the library.

## Core Functionality Analysis

### 1. Module Path Utilities
- **`get_module_name`**: Extracts the module name from a given object, function, or class. This is used to identify participants when they're not explicitly specified.
- **`get_short_module_name`**: Returns only the last part of the module path (e.g., `mermaid_trace.core.utils` becomes `utils`), making participant names more concise in diagrams.

### 2. String Manipulation
- **`truncate_string`**: Safely truncates strings to a specified length, adding an ellipsis if the string is longer than the limit. This prevents excessive parameter or return value strings from cluttering diagrams.
- **`sanitize_string`**: Removes or escapes characters that might cause issues in Mermaid syntax, ensuring generated diagrams are syntactically correct.

### 3. Error Handling
- **`safe_operation`**: A generic wrapper that catches exceptions during operations, ensuring that errors in non-critical functionality don't affect the main application flow.
- **`format_exception`**: Formats exception objects into readable strings, including stack traces when available, for better error display in diagrams.

### 4. Type Checking
- **`is_async_function`**: Detects if a given function is an asynchronous coroutine function, allowing the decorator system to properly handle both sync and async functions.
- **`is_class_method`**: Identifies if a function is a class method, which affects how participant names are resolved.

### 5. Performance Optimization
- **`cache_result`**: A simple caching decorator for functions with expensive computations, improving performance when the same value is requested multiple times.

## Source Code with English Comments

```python
"""
Utility functions module

This module provides helper functions for various internal operations
including module path resolution, string manipulation, error handling,
and type checking utilities used across MermaidTrace components.
"""

import inspect
import re
from functools import lru_cache
from typing import Any, Callable, Optional, TypeVar, cast


T = TypeVar('T')


def get_module_name(obj: Any) -> str:
    """
    Get the module name for a given object, function, or class.
    
    Args:
        obj: Object to get module name for
        
    Returns:
        str: Full module name
    """
    if inspect.ismodule(obj):
        return obj.__name__
    module = inspect.getmodule(obj)
    if module:
        return module.__name__
    return "__main__"


def get_short_module_name(obj: Any) -> str:
    """
    Get the short module name (last part) for a given object.
    
    Args:
        obj: Object to get short module name for
        
    Returns:
        str: Short module name (e.g., "utils" from "mermaid_trace.core.utils")
    """
    full_name = get_module_name(obj)
    return full_name.split(".")[-1]


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Truncate string to specified length with ellipsis.
    
    Args:
        s: String to truncate
        max_length: Maximum length before truncation
        
    Returns:
        str: Truncated string with ellipsis if needed
    """
    if len(s) <= max_length:
        return s
    return s[:max_length] + "..."


def sanitize_string(s: str) -> str:
    """
    Sanitize string for Mermaid syntax.
    
    Args:
        s: String to sanitize
        
    Returns:
        str: Sanitized string safe for Mermaid diagrams
    """
    # Escape newlines
    s = s.replace('\n', '\\n')
    # Escape quotes
    s = s.replace('"', '\\"')
    # Remove control characters
    s = re.sub(r'\\x[0-9a-fA-F]{2}', '', s)
    return s


def safe_operation(default: T = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for safe operations that catch exceptions.
    
    Args:
        default: Value to return on exception
        
    Returns:
        Callable: Decorated function that catches exceptions
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                return default
        return wrapper
    return decorator


def format_exception(exc: Exception) -> str:
    """
    Format exception as string with traceback.
    
    Args:
        exc: Exception object to format
        
    Returns:
        str: Formatted exception string
    """
    import traceback
    return ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def is_async_function(func: Any) -> bool:
    """
    Check if a function is an asynchronous coroutine function.
    
    Args:
        func: Function to check
        
    Returns:
        bool: True if function is async, False otherwise
    """
    return inspect.iscoroutinefunction(func)


def is_class_method(func: Any) -> bool:
    """
    Check if a function is a class method.
    
    Args:
        func: Function to check
        
    Returns:
        bool: True if function is a class method, False otherwise
    """
    if not inspect.isfunction(func):
        return False
    # Check if function has 'self' or 'cls' as first parameter
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    return len(params) > 0 and (params[0] == 'self' or params[0] == 'cls')


@lru_cache(maxsize=128)
def cache_result(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to cache function results using LRU caching.
    
    Args:
        func: Function to cache results for
        
    Returns:
        Callable: Decorated function with cached results
    """
    return cast(Callable[..., T], lru_cache(maxsize=128)(func))
```