"""
Event Formatting Module

This module provides formatters to convert Event objects into various output formats.
Currently, it supports Mermaid sequence diagram syntax formatting, but can be extended
with additional formatters for other diagram types or logging formats.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Set, Any, List, Tuple
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

    @abstractmethod
    def get_header(self, title: str) -> str:
        """
        Get the file header for the diagram format.

        Args:
            title: The title of the diagram

        Returns:
            str: Header string
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Map raw participant names to sanitized Mermaid IDs
        self._participant_map: Dict[str, str] = {}
        # Set of already used Mermaid IDs to prevent collisions
        self._used_ids: Set[str] = set()

        # State for intelligent collapsing
        # We track a window of events to detect patterns (length 1 or 2)
        self._event_buffer: List[FlowEvent] = []
        self._pattern_count: int = 0
        self._current_pattern: List[Tuple[str, str, str, bool]] = []

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a logging record containing an event.

        If the record contains a FlowEvent, it will be buffered for pattern-based collapsing.
        To get immediate output for tests, you can call flush() after format().
        """
        event: Optional[Event] = getattr(record, "flow_event", None)

        if not event or not isinstance(event, FlowEvent):
            return super().format(record)

        # Create a key for this event type
        event_key = (event.source, event.target, event.action, event.is_return)

        # Case 1: Already in a pattern
        if self._current_pattern:
            pattern_len = len(self._current_pattern)
            match_idx = len(self._event_buffer) % pattern_len

            if event_key == self._current_pattern[match_idx]:
                # It matches!
                self._event_buffer.append(event)
                if match_idx == pattern_len - 1:
                    self._pattern_count += 1
                return ""
            else:
                # Pattern broken! Flush and continue to find new pattern
                output = self.flush()
                prefix = output + "\n" if output else ""

                self._event_buffer = [event]
                return prefix.strip()

        # Case 2: Not in a pattern yet, but have one event buffered
        if self._event_buffer:
            first = self._event_buffer[0]
            first_key = (first.source, first.target, first.action, first.is_return)

            if event_key == first_key:
                # Pattern length 1 detected (A, A)
                self._current_pattern = [first_key]
                self._event_buffer.append(event)
                self._pattern_count = 2
                return ""
            elif (
                event.is_return
                and event.source == first.target
                and event.target == first.source
                and event.action == first.action
            ):
                # Pattern length 2 detected (Call, Return)
                self._current_pattern = [first_key, event_key]
                self._event_buffer.append(event)
                self._pattern_count = 1
                return ""
            else:
                # No pattern, flush first event and keep current as new potential start
                output = self.format_event(first, 1)
                self._event_buffer = [event]
                return output.strip()

        # Case 3: Completely idle
        # To avoid breaking existing tests that expect immediate output for single events,
        # we check if we can immediately format it. But for true collapsing, we need buffering.
        # Strategy: we buffer it, but if it's the ONLY event, flush() must be called.
        # To maintain compatibility with tests, we'll keep buffering but update tests
        # or change logic to only buffer if we suspect a pattern.
        # Actually, the most robust way is to update the tests/handlers to call flush.
        self._event_buffer = [event]
        return ""

    def flush(self) -> str:
        """
        Flushes the current collapsed pattern and returns its Mermaid representation.
        """
        if not self._event_buffer:
            return ""

        output_lines = []

        if self._current_pattern:
            pattern_len = len(self._current_pattern)
            # Only output one instance of the pattern, but with the total count
            for i in range(pattern_len):
                event = self._event_buffer[i]
                line = self.format_event(event, self._pattern_count)
                output_lines.append(line)
        else:
            # Just some buffered events that didn't form a pattern
            for event in self._event_buffer:
                output_lines.append(self.format_event(event, 1))

        # Reset state
        self._event_buffer = []
        self._current_pattern = []
        self._pattern_count = 0

        return "\n".join(output_lines)

    def get_header(self, title: str = "Log Flow") -> str:
        """
        Returns the Mermaid sequence diagram header.
        """
        return f"sequenceDiagram\n    title {title}\n    autonumber\n\n"

    def format_event(self, event: Event, count: int = 1) -> str:
        """
        Converts an Event into a Mermaid syntax string.

        Args:
            event: The Event object to format
            count: Number of times this event was repeated (for collapsing)

        Returns:
            str: Mermaid syntax string representation of the event
        """
        if not isinstance(event, FlowEvent):
            # Fallback format for non-FlowEvent types
            return f"{event.source}->>{event.target}: {event.message}"

        # Sanitize participant names to avoid syntax errors in Mermaid
        src = self._sanitize(event.source)
        tgt = self._sanitize(event.target)

        # Determine arrow type
        arrow = "-->>" if event.is_return else "->>"

        # Construct message text
        msg = ""
        if event.is_error:
            arrow = "--x"
            msg = f"Error: {event.error_message}"
        elif event.is_return:
            msg = f"Return: {event.result}" if event.result else "Return"
        else:
            msg = f"{event.message}({event.params})" if event.params else event.message

        # Append count if collapsed
        if count > 1:
            msg += f" (x{count})"

        # Escape message for Mermaid safety
        msg = self._escape_message(msg)

        # Return the complete Mermaid syntax line
        line = f"{src}{arrow}{tgt}: {msg}"

        # Add Notes for Errors (Stack Trace)
        if event.is_error and event.stack_trace:
            short_stack = self._escape_message(event.stack_trace[:300] + "...")
            note = f"note right of {tgt}: {short_stack}"
            return f"{line}\n{note}"

        # Handle manually marked collapsed events (if any)
        if event.collapsed and count == 1:
            note = f"note right of {src}: ( Sampled / Collapsed Interaction )"
            return f"{line}\n{note}"

        return line

    def _sanitize(self, name: str) -> str:
        """
        Sanitizes participant names to be valid Mermaid identifiers.
        Handles naming collisions by ensuring unique IDs.

        Args:
            name: Original participant name

        Returns:
            str: Sanitized participant name (unique)
        """
        if name in self._participant_map:
            return self._participant_map[name]

        # Replace any non-alphanumeric character (except underscore) with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure it doesn't start with a digit (Mermaid doesn't like that sometimes)
        if clean_name and clean_name[0].isdigit():
            clean_name = "_" + clean_name

        if not clean_name:
            clean_name = "Unknown"

        # Check for collisions
        if clean_name in self._used_ids:
            original_clean = clean_name
            counter = 1
            while clean_name in self._used_ids:
                clean_name = f"{original_clean}_{counter}"
                counter += 1

        self._participant_map[name] = clean_name
        self._used_ids.add(clean_name)
        return clean_name

    def _escape_message(self, msg: str) -> str:
        """
        Escapes special characters in the message text for safe Mermaid rendering.

        Args:
            msg: Original message text

        Returns:
            str: Escaped message text
        """
        if not msg:
            return ""

        # 1. Replace newlines with <br/>
        msg = msg.replace("\n", "<br/>")

        # 2. Escape parentheses and special characters that break Mermaid syntax
        # Mermaid messages are usually after a colon ": message"
        # Characters like [ ] ( ) { } ; # can be problematic if not handled
        
        # We wrap the message in quotes if it contains problematic characters
        # But Mermaid sequence diagrams actually support most characters if they are NOT used as keywords
        # The most common issue is characters that interfere with the arrow or participant parsing
        
        # Replace problematic characters with safer alternatives or escape them
        # Note: Mermaid doesn't have a universal escape character like backslash for all cases,
        # but for sequence diagrams, using Unicode alternatives or just stripping them is often safer.
        
        msg = msg.replace("(", "（").replace(")", "）")
        msg = msg.replace("[", "［").replace("]", "］")
        msg = msg.replace(";", "；")
        msg = msg.replace("#", "＃")

        return msg
