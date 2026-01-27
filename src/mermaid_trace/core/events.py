"""
Event Definition Module

This module defines the event structure for the tracing system. It provides an
abstract Event base class and a concrete FlowEvent implementation that represents
individual interactions in the execution flow.
"""

from abc import ABC
from dataclasses import dataclass, field
import time
from typing import Optional


class Event(ABC):
    """
    Abstract base class for all event types.

    This provides a common interface for different types of events, allowing
    for extensibility and supporting multiple output formats. Concrete event
    classes must implement all abstract methods.
    """

    # Common attributes that should be present in all events
    source: str
    target: str
    action: str
    message: str
    timestamp: float
    trace_id: str


@dataclass
class FlowEvent(Event):
    """
    Represents a single interaction or step in the execution flow.

    (Existing docstring omitted for brevity)
    """

    # Required fields for every event
    source: str  # Participant who initiated the action
    target: str  # Participant who received the action
    action: str  # Short name for the operation
    message: str  # Detailed message for the diagram arrow
    trace_id: str  # Unique identifier for the trace session

    # Optional fields with defaults
    timestamp: float = field(
        default_factory=time.time
    )  # Unix timestamp of event creation
    is_return: bool = False  # Whether this is a response arrow
    is_error: bool = False  # Whether an error occurred
    error_message: Optional[str] = None  # Detailed error message if is_error is True
    stack_trace: Optional[str] = None  # Full stack trace if is_error is True
    params: Optional[str] = None  # Stringified function arguments
    result: Optional[str] = None  # Stringified return value
    collapsed: bool = (
        False  # Whether this interaction should be visually collapsed (loop/folding)
    )
