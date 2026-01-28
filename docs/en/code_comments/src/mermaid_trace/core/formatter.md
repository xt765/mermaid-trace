# File: src/mermaid_trace/core/formatter.py

## Overview
The `formatter.py` module implements the `MermaidFormatter` class, which is responsible for converting `FlowEvent` objects into Mermaid sequence diagram syntax. It handles the complete lifecycle of diagram generation, from initializing the diagram header to finalizing the diagram footer, including participant declarations and message arrows.

## Core Functionality Analysis

### 1. `MermaidFormatter` Class
This is the central component for converting events to Mermaid syntax:
- **State Management**: Maintains internal state including participants, active diagram sections, and error tracking.
- **Diagram Structure**: Organizes the diagram into logical sections with proper Mermaid syntax.
- **Participant Registration**: Automatically registers participants as they appear in events, ensuring all are properly declared at the beginning of the diagram.

### 2. Event Processing (`add_event`)
The `add_event` method is the main entry point for processing `FlowEvent` objects:
- **Call Events**: For non-return events, it creates a message arrow from source to target with the action and parameters.
- **Return Events**: For return events, it creates a message arrow from target back to source, including return values or error information.
- **Error Handling**: Special formatting for error events, including stack trace display in notes.

### 3. Diagram Generation (`format`)
The `format` method assembles the complete Mermaid diagram:
- **Header Generation**: Adds the `sequenceDiagram` declaration and participant list.
- **Event Rendering**: Processes all accumulated events into Mermaid syntax.
- **Footer Addition**: Closes the diagram properly.
- **Error Section**: Appends error information as notes if any errors occurred.

### 4. Participant Management
- **Automatic Detection**: Extracts participants from `source` and `target` fields of events.
- **Deduplication**: Ensures each participant is only declared once in the diagram.
- **Order Preservation**: Maintains the order in which participants first appear, ensuring diagram consistency.

### 5. Error Handling
- **Stack Trace Formatting**: Converts stack traces into readable note format in Mermaid diagrams.
- **Error Isolation**: Ensures errors in one event don't affect the entire diagram generation process.

## Source Code with English Comments

```python
"""
Mermaid diagram formatter module

This module converts FlowEvent objects into Mermaid sequence diagram syntax.
It handles participant registration, message formatting, and error display
for generating complete, syntactically correct Mermaid diagrams.
"""

from typing import Dict, List, Optional, Set, Tuple

from .events import FlowEvent


class MermaidFormatter:
    """
    Formats FlowEvent objects into Mermaid sequence diagram syntax.
    
    This class manages the complete lifecycle of diagram generation,
    including participant registration, event processing, and final
    diagram assembly with proper Mermaid syntax.
    """

    def __init__(self) -> None:
        """
        Initialize Mermaid formatter with empty state.
        """
        self._events: List[FlowEvent] = []
        self._participants: List[str] = []
        self._participant_set: Set[str] = set()
        self._errors: List[Tuple[str, str]] = []  # (participant, error_message)

    def add_event(self, event: FlowEvent) -> None:
        """
        Add a FlowEvent to be formatted into the diagram.
        
        Args:
            event: The FlowEvent to add to the diagram
        """
        # Register participants
        self._register_participant(event.source)
        self._register_participant(event.target)

        # Store event
        self._events.append(event)

        # Track errors for notes section
        if event.is_error and event.error_message:
            self._errors.append((event.source, event.error_message))

    def _register_participant(self, participant: str) -> None:
        """
        Register a participant if not already registered.
        
        Args:
            participant: The participant name to register
        """
        if participant not in self._participant_set:
            self._participant_set.add(participant)
            self._participants.append(participant)

    def _format_event(self, event: FlowEvent) -> str:
        """
        Format a single FlowEvent into Mermaid syntax.
        
        Args:
            event: The FlowEvent to format
            
        Returns:
            str: Mermaid syntax for the event
        """
        if event.is_return:
            # Return event (dotted arrow back)
            if event.is_error:
                # Error return (x arrow)
                arrow = f"{event.source}--x{event.target}: {event.action}"
            else:
                # Normal return (dotted arrow)
                arrow = f"{event.source}--> {event.target}: {event.action}"

            # Add return value or error message
            if event.result:
                arrow += f"\\n  return: {event.result}"
            elif event.error_message:
                arrow += f"\\n  error: {event.error_message}"
        else:
            # Regular call event (solid arrow)
            arrow = f"{event.source}->> {event.target}: {event.action}"
            if event.params:
                arrow += f"\\n  params: {event.params}"

        return arrow

    def _format_stack_trace(self, event: FlowEvent) -> Optional[str]:
        """
        Format stack trace as a Mermaid note.
        
        Args:
            event: The FlowEvent containing the stack trace
            
        Returns:
            Optional[str]: Mermaid note syntax for the stack trace
        """
        if not event.is_error or not event.stack_trace:
            return None

        # Escape newlines and quotes for Mermaid syntax
        stack_trace = event.stack_trace.replace('\\n', '\\n  ')
        stack_trace = stack_trace.replace('"', '\\"')

        return f"note over {event.source}: Error Stack Trace\\n  {stack_trace}"

    def format(self) -> str:
        """
        Generate complete Mermaid sequence diagram syntax.
        
        Returns:
            str: Complete Mermaid diagram syntax
        """
        lines = ["sequenceDiagram"]

        # Add participants
        for participant in self._participants:
            lines.append(f"participant {participant}")

        lines.append("")  # Empty line for readability

        # Add events
        for event in self._events:
            lines.append(self._format_event(event))
            # Add stack trace note if error
            stack_trace_note = self._format_stack_trace(event)
            if stack_trace_note:
                lines.append(stack_trace_note)
            lines.append("")  # Empty line between events

        # Add error notes section
        if self._errors:
            lines.append("%% Error Notes")
            for participant, error_msg in self._errors:
                error_msg = error_msg.replace('\\n', '\\n  ')
                error_msg = error_msg.replace('"', '\\"')
                lines.append(f"note over {participant}: Error\\n  {error_msg}")
            lines.append("")

        return "\n".join(lines)

    def reset(self) -> None:
        """
        Reset formatter state to prepare for a new diagram.
        """
        self._events.clear()
        self._participants.clear()
        self._participant_set.clear()
        self._errors.clear()

    def get_participants(self) -> List[str]:
        """
        Get list of participants registered in the current diagram.
        
        Returns:
            List[str]: List of participant names
        """
        return self._participants.copy()

    def get_event_count(self) -> int:
        """
        Get number of events processed.
        
        Returns:
            int: Number of events
        """
        return len(self._events)
```