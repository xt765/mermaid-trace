# File: src/mermaid_trace/__init__.py

## Overview
The `__init__.py` file at the root of the `mermaid_trace` package serves as the main entry point for the library. It exposes the public API, including core decorators, configuration functions, and integration points, making them available for import by users.

## Core Functionality Analysis

### 1. Public API Exports
This file defines the public API of MermaidTrace, exposing:
- **Decorators**: `@trace` and `@trace_interaction` for function tracing.
- **Class Decorators**: `@trace_class` for automatic instrumentation of entire classes.
- **Configuration**: `configure_flow` function for setting up logging and diagram generation.
- **Utilities**: Helper functions and classes for advanced usage.
- **Integrations**: Framework integrations like FastAPI middleware.

### 2. Package Structure
The `__init__.py` file organizes the package structure by:
- **Simplifying Imports**: Allowing users to import core functionality directly from `mermaid_trace` instead of from specific submodules.
- **Providing Consistent Interface**: Creating a stable public API that hides internal implementation details.
- **Version Information**: Exposing the package version for compatibility checking.

### 3. Configuration Functions
The `configure_flow` function is the primary way users set up MermaidTrace:
- **File Configuration**: Specifies the output file for Mermaid diagrams.
- **Logging Setup**: Configures the logging system to capture trace events.
- **Async Configuration**: Enables or disables asynchronous processing.
- **Overrides**: Allows overriding default configuration values.

### 4. Instrumentation Functions
- **`trace`/`trace_interaction`**: Decorators for tracing individual functions.
- **`trace_class`**: Decorator for automatically tracing all methods in a class.
- **`patch_object`**: Function for patching third-party objects for tracing.

### 5. Integration Points
- **FastAPI Middleware**: Exposes the FastAPI integration for web applications.
- **CLI Tools**: Exposes command-line interface tools for diagram viewing and management.

## Source Code with English Comments

```python
"""
MermaidTrace: The Python Logger That Draws Diagrams

MermaidTrace is a specialized logging tool that automatically generates
Mermaid JS sequence diagrams from your code execution. It's perfect for
visualizing complex business logic, microservice interactions, or
asynchronous flows.
"""

from .core import (
    Config,
    ConfigOverrides,
    FlowEvent,
    LogContext,
    MermaidFormatter,
    config,
    get_flow_logger,
    trace_interaction,
)

from .core.decorators import trace_class, patch_object
from .handlers import AsyncMermaidHandler, MermaidHandler, RotatingMermaidFileHandler
from .integrations import MermaidTraceMiddleware, add_mermaid_trace_middleware


# Version information
__version__ = "0.1.0"
__author__ = "MermaidTrace Team"
__license__ = "MIT"


# Public API exports
__all__ = [
    # Core functionality
    "trace",
    "trace_interaction",
    "trace_class",
    "patch_object",
    "configure_flow",
    
    # Core classes
    "Config",
    "ConfigOverrides",
    "FlowEvent",
    "LogContext",
    "MermaidFormatter",
    "config",
    "get_flow_logger",
    
    # Handlers
    "MermaidHandler",
    "AsyncMermaidHandler",
    "RotatingMermaidFileHandler",
    
    # Integrations
    "MermaidTraceMiddleware",
    "add_mermaid_trace_middleware",
    
    # Version
    "__version__",
]


# Alias for convenience
trace = trace_interaction


def configure_flow(
    filename: str,
    overwrite: bool = True,
    level: int = None,
    queue_size: int = 1000,
    async_mode: bool = True,
    config_overrides: ConfigOverrides = None,
) -> None:
    """
    Configure MermaidTrace logging and output.
    
    Args:
        filename: Path to the output Mermaid file
        overwrite: Whether to overwrite the file on each run
        level: Logging level (default: logging.INFO)
        queue_size: Size of the async event queue
        async_mode: Whether to use asynchronous processing
        config_overrides: Dictionary of configuration overrides
    """
    import logging
    
    # Set up logging level
    if level is None:
        level = logging.INFO
    
    # Update configuration
    if config_overrides:
        config.update(**config_overrides)
    
    # Create logger
    logger = get_flow_logger()
    logger.setLevel(level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create and add handler
    if async_mode:
        handler = AsyncMermaidHandler(
            filename=filename,
            overwrite=overwrite,
            queue_size=queue_size,
        )
    else:
        handler = MermaidHandler(
            filename=filename,
            overwrite=overwrite,
        )
    
    logger.addHandler(handler)


# Import CLI module if available
try:
    from .cli import cli
    __all__.append("cli")
except ImportError:
    pass
```