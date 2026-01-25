"""
MermaidTrace: Visualize your Python code execution flow as Mermaid Sequence Diagrams.

This package provides tools to automatically trace function calls and generate
Mermaid-compatible sequence diagrams (.mmd files). It is designed to help
developers understand the flow of their applications, debug complex interactions,
and document system behavior.

Key Components:
- `trace`: A decorator to instrument functions for tracing.
- `LogContext`: Manages execution context (like thread-local storage) to track
  caller/callee relationships across async tasks and threads.
- `configure_flow`: Sets up the logging handler to write diagrams to a file.
"""

from .core.decorators import trace_interaction, trace
from .handlers.mermaid_handler import MermaidFileHandler
from .core.events import FlowEvent
from .core.context import LogContext
# We don't import integrations by default to avoid hard dependencies
# Integrations (like FastAPI) must be imported explicitly by the user if needed.

from importlib.metadata import PackageNotFoundError, version

import logging

def configure_flow(output_file: str = "flow.mmd") -> logging.Logger:
    """
    Configures the flow logger to output to a Mermaid file.
    
    This function sets up the logging infrastructure required to capture
    trace events and write them to the specified output file. It should
    be called once at the start of your application.
    
    Args:
        output_file (str): The absolute or relative path to the output .mmd file.
                           Defaults to "flow.mmd" in the current directory.
    
    Returns:
        logging.Logger: The configured logger instance used for flow tracing.
    """
    # Get the specific logger used by the tracing decorators
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicate logs if configured multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create and attach the custom handler that writes Mermaid syntax
    handler = MermaidFileHandler(output_file)
    logger.addHandler(handler)
    
    return logger

try:
    # Attempt to retrieve the installed package version
    __version__ = version("mermaid-trace")
except PackageNotFoundError:
    # Fallback version if the package is not installed (e.g., local development)
    __version__ = "0.0.0"


# Export public API for easy access
__all__ = ["trace_interaction", "trace", "configure_flow", "MermaidFileHandler", "LogContext", "FlowEvent"]
