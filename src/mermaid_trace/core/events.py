"""
Event Definition Module

This module defines the event structure for the tracing system. It provides an
abstract Event base class and a concrete FlowEvent implementation that represents
individual interactions in the execution flow.
"""

from abc import ABC, abstractmethod
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

    @abstractmethod
    def get_source(self) -> str:
        """
        Get the source of the event.

        Returns:
            str: Name of the participant that generated the event
        """
        pass

    @abstractmethod
    def get_target(self) -> str:
        """
        Get the target of the event.

        Returns:
            str: Name of the participant that received the event
        """
        pass

    @abstractmethod
    def get_action(self) -> str:
        """
        Get the action name of the event.

        Returns:
            str: Short name describing the action performed
        """
        pass

    @abstractmethod
    def get_message(self) -> str:
        """
        Get the message text of the event.

        Returns:
            str: Detailed message describing the event
        """
        pass

    @abstractmethod
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the event.

        Returns:
            float: Unix timestamp (seconds) when the event occurred
        """
        pass

    @abstractmethod
    def get_trace_id(self) -> str:
        """
        Get the trace ID of the event.

        Returns:
            str: Unique identifier for the trace session
        """
        pass


@dataclass
class FlowEvent(Event):
    """
    Represents a single interaction or step in the execution flow.

    This data structure acts as the intermediate representation (IR) between
    runtime code execution and the final diagram output. Each instance
    corresponds directly to one arrow or note in the sequence diagram.

    The fields map to diagram syntax components as follows:
    `source` -> `target`: `message`

    Attributes:
        source (str):
            The name of the participant initiating the action (the "Caller").
            In sequence diagrams: The participant on the LEFT side of the arrow.

        target (str):
            The name of the participant receiving the action (the "Callee").
            In sequence diagrams: The participant on the RIGHT side of the arrow.

        action (str):
            A short, human-readable name for the operation (e.g., function name).
            Used for grouping or filtering logs, but often redundant with message.

        message (str):
            The actual text label displayed on the diagram arrow.
            Example: "getUser(id=1)" or "Return: User(name='Alice')".

        timestamp (float):
            Unix timestamp (seconds) of when the event occurred.
            Used for ordering events if logs are processed asynchronously.
            Defaults to current time when event is created.

        trace_id (str):
            Unique identifier for the trace session.
            Allows filtering multiple concurrent traces from a single log file
            to generate separate diagrams for separate requests.

        is_return (bool):
            Flag indicating if this is a response arrow.
            If True, the arrow is drawn as a dotted line in sequence diagrams.
            If False, it is a solid line representing a call.
            Defaults to False.

        is_error (bool):
            Flag indicating if an exception occurred.
            If True, the arrow might be styled differently to show failure.
            Defaults to False.

        error_message (Optional[str]):
            Detailed error text if `is_error` is True.
            Can be added as a note or included in the arrow label.
            Defaults to None.

        params (Optional[str]):
            Stringified representation of function arguments.
            Captured only for request events (call start).
            Defaults to None.

        result (Optional[str]):
            Stringified representation of the return value.
            Captured only for return events (call end).
            Defaults to None.
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
    params: Optional[str] = None  # Stringified function arguments
    result: Optional[str] = None  # Stringified return value

    def get_source(self) -> str:
        """Get the source of the event."""
        return self.source

    def get_target(self) -> str:
        """Get the target of the event."""
        return self.target

    def get_action(self) -> str:
        """Get the action name of the event."""
        return self.action

    def get_message(self) -> str:
        """Get the message text of the event."""
        return self.message

    def get_timestamp(self) -> float:
        """Get the timestamp of the event."""
        return self.timestamp

    def get_trace_id(self) -> str:
        """Get the trace ID of the event."""
        return self.trace_id
