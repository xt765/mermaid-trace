"""
Event Formatting Module

This module provides formatters to convert Event objects into various output formats.
Currently, it supports Mermaid sequence diagram syntax formatting, but can be extended
with additional formatters for other diagram types or logging formats.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional
from .events import Event, FlowEvent


class BaseFormatter(ABC, logging.Formatter):
    """
    Abstract base class for all event formatters.

    This provides a common interface for different formatters, allowing
    for extensibility and supporting multiple output formats.

    Subclasses must implement the format_event method to convert Event objects
    into the desired output string format.
    """

    @abstractmethod
    def format_event(self, event: Event) -> str:
        """
        Format an Event into the desired output string.

        Args:
            event: The Event object to format

        Returns:
            str: Formatted string representation of the event
        """
        pass

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a logging record containing an event.

        This method overrides the standard logging.Formatter.format method to
        extract and format Event objects from log records.

        Args:
            record: The logging record to format. Must contain a 'flow_event' attribute
                   if it represents a tracing event.

        Returns:
            str: Formatted string representation of the record
        """
        # Retrieve the Event object from the log record
        event: Optional[Event] = getattr(record, "flow_event", None)

        if not event:
            # Fallback for standard logs if they accidentally reach this handler
            return super().format(record)

        # Convert event to the desired format using the subclass's format_event method
        return self.format_event(event)


class MermaidFormatter(BaseFormatter):
    """
    Custom formatter to convert Events into Mermaid sequence diagram syntax.

    This formatter transforms FlowEvent objects into lines of Mermaid syntax that
    can be directly written to a .mmd file. Each event becomes a single line in the
    sequence diagram.
    """

    def format_event(self, event: Event) -> str:
        """
        Converts an Event into a Mermaid syntax string.

        Args:
            event: The Event object to format

        Returns:
            str: Mermaid syntax string representation of the event
        """
        if not isinstance(event, FlowEvent):
            # Fallback format for non-FlowEvent types
            return f"{event.get_source()}->>{event.get_target()}: {event.get_message()}"

        # Sanitize participant names to avoid syntax errors in Mermaid
        src = self._sanitize(event.source)
        tgt = self._sanitize(event.target)

        # Determine arrow type based on event properties
        # ->> : Solid line with arrowhead (synchronous call)
        # -->> : Dotted line with arrowhead (return)
        # --x : Dotted line with cross (error)
        arrow = "-->>" if event.is_return else "->>"

        # Construct message text based on event type
        msg = ""
        if event.is_error:
            arrow = "--x"
            msg = f"Error: {event.error_message}"
        elif event.is_return:
            # For return events, show return value or just "Return"
            msg = f"Return: {event.result}" if event.result else "Return"
        else:
            # For call events, show Action(Params) or just Action
            msg = f"{event.message}({event.params})" if event.params else event.message

        # Escape message for Mermaid safety (e.g., replacing newlines)
        msg = self._escape_message(msg)

        # Return the complete Mermaid syntax line
        # Format: Source->>Target: Message
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """
        Sanitizes participant names to be valid Mermaid identifiers.

        Mermaid doesn't like spaces or special characters in participant aliases
        unless they are quoted (which we are not doing here for simplicity),
        so we replace them with underscores.

        Args:
            name: Original participant name

        Returns:
            str: Sanitized participant name
        """
        # Replace any non-alphanumeric character (except underscore) with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure it doesn't start with a digit (Mermaid doesn't like that sometimes)
        if clean_name and clean_name[0].isdigit():
            clean_name = "_" + clean_name
        return clean_name

    def _escape_message(self, msg: str) -> str:
        """
        Escapes special characters in the message text for safe Mermaid rendering.

        Args:
            msg: Original message text

        Returns:
            str: Escaped message text
        """
        # Replace newlines with <br/> for proper display in Mermaid diagrams
        msg = msg.replace("\n", "<br/>")
        # Additional escaping could be added here if needed for other characters
        return msg
