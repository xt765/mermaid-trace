"""
MermaidTrace: Visualize your Python code execution flow as Mermaid Sequence Diagrams.

This package provides tools to automatically trace function calls and generate
Mermaid-compatible sequence diagrams (.mmd files). It is designed to help
developers understand the flow of their applications, debug complex interactions,
and document system behavior.

Key Components:
- `trace`: A decorator to instrument functions for tracing. It captures arguments,
  return values, and errors, and logs them as interactions.
- `LogContext`: Manages execution context (like thread-local storage) to track
  caller/callee relationships across async tasks and threads.
- `configure_flow`: Sets up the logging handler to write diagrams to a file.
  It handles handler configuration, file modes, and async logging setup.

Usage Example:
    from mermaid_trace import trace, configure_flow

    configure_flow("my_flow.mmd")

    @trace
    def hello():
        print("Hello")

    hello()
"""

from .core.decorators import trace_interaction, trace
from .handlers.mermaid_handler import MermaidFileHandler
from .handlers.async_handler import AsyncMermaidHandler
from .core.events import Event, FlowEvent
from .core.context import LogContext
from .core.formatter import BaseFormatter, MermaidFormatter
# We don't import integrations by default to avoid hard dependencies
# Integrations (like FastAPI) must be imported explicitly by the user if needed.

from importlib.metadata import PackageNotFoundError, version
from typing import List, Optional

import logging


def configure_flow(
    output_file: str = "flow.mmd",
    handlers: Optional[List[logging.Handler]] = None,
    append: bool = False,
    async_mode: bool = False,
) -> logging.Logger:
    """
    Configures the flow logger to output to a Mermaid file.

    This function sets up the logging infrastructure required to capture
    trace events and write them to the specified output file. It should
    be called once at the start of your application to initialize the tracing system.

    Args:
        output_file (str): The absolute or relative path to the output .mmd file.
                           Defaults to "flow.mmd" in the current directory.
                           If the file does not exist, it will be created with the correct header.
        handlers (List[logging.Handler], optional): A list of custom logging handlers.
                                                    If provided, 'output_file' is ignored unless
                                                    you explicitly include a MermaidFileHandler.
                                                    Useful if you want to stream logs to other destinations.
        append (bool): If True, adds the new handler(s) without removing existing ones.
                       Defaults to False (clears existing handlers to prevent duplicate logging).
        async_mode (bool): If True, uses a non-blocking background thread for logging (QueueHandler).
                           Recommended for high-performance production environments to avoid
                           blocking the main execution thread during file I/O.
                           Defaults to False.

    Returns:
        logging.Logger: The configured logger instance used for flow tracing.
    """
    # Get the specific logger used by the tracing decorators
    # This logger is isolated from the root logger to prevent pollution
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicate logs if configured multiple times
    # unless 'append' is requested. This ensures idempotency when calling configure_flow multiple times.
    if not append and logger.hasHandlers():
        logger.handlers.clear()

    # Determine the target handlers
    target_handlers = []

    if handlers:
        # Use user-provided handlers if available
        target_handlers = handlers
    else:
        # Create default Mermaid handler
        # This handler knows how to write the Mermaid header and format events
        handler = MermaidFileHandler(output_file)
        handler.setFormatter(MermaidFormatter())
        target_handlers = [handler]

    if async_mode:
        # Wrap the target handlers in an AsyncMermaidHandler (QueueHandler)
        # The QueueListener will pick up logs from the queue and dispatch to target_handlers
        # This decouples the application execution from the logging I/O
        async_handler = AsyncMermaidHandler(target_handlers)
        logger.addHandler(async_handler)
    else:
        # Attach handlers directly to the logger for synchronous logging
        # Simple and reliable for debugging or low-throughput applications
        for h in target_handlers:
            logger.addHandler(h)

    return logger


try:
    # Attempt to retrieve the installed package version
    __version__ = version("mermaid-trace")
except PackageNotFoundError:
    # Fallback version if the package is not installed (e.g., local development)
    __version__ = "0.0.0"


# Export public API for easy access
__all__ = [
    "trace_interaction",
    "trace",
    "configure_flow",
    "MermaidFileHandler",
    "AsyncMermaidHandler",
    "LogContext",
    "Event",
    "FlowEvent",
    "BaseFormatter",
    "MermaidFormatter",
]
