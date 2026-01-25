"""
MermaidTrace: Visualize your Python code execution flow as Mermaid Sequence Diagrams.
"""

from .core.decorators import trace_interaction, trace
from .handlers.mermaid_handler import MermaidFileHandler
from .core.events import FlowEvent
from .core.context import LogContext
# We don't import integrations by default to avoid hard dependencies

from importlib.metadata import PackageNotFoundError, version

import logging

def configure_flow(output_file: str = "flow.mmd") -> logging.Logger:
    """
    Configures the flow logger to output to a Mermaid file.
    
    Args:
        output_file: Path to the output .mmd file.
    """
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = MermaidFileHandler(output_file)
    logger.addHandler(handler)
    return logger

try:
    __version__ = version("mermaid-trace")
except PackageNotFoundError:
    __version__ = "0.0.0"


__all__ = ["trace_interaction", "trace", "configure_flow", "MermaidFileHandler", "LogContext"]
