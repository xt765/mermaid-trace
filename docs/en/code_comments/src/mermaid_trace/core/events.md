# File: src/mermaid_trace/core/events.py

## Overview
The `events.py` module defines the core data structure `FlowEvent` for MermaidTrace. This class is responsible for encapsulating all information needed to generate Mermaid sequence diagram nodes and edges, including participants, actions, parameters, return values, and error information.

## Core Functionality Analysis

### 1. `FlowEvent` Class
This is the fundamental data structure that represents a single interaction in the Mermaid diagram:
- **Participant Information**: `source` (caller) and `target` (callee) identify who is interacting with whom.
- **Action Details**: `action` describes what operation is being performed, displayed on the arrow in the diagram.
- **Message Content**: `message` provides additional context or description for the interaction.
- **Parameter Capturing**: `params` stores formatted function arguments, making it clear what data is being passed.
- **Return Value Tracking**: `result` captures the function's return value, displayed when the call completes.
- **Error Handling**: `is_error`, `error_message`, and `stack_trace` handle exception scenarios, displaying error information in the diagram.
- **Tracing Context**: `trace_id` links related events together, ensuring they appear in the same diagram.
- **Event Type Flags**: `is_return` distinguishes return events from call events, enabling two-way arrows in diagrams.

### 2. Event Serialization
The `FlowEvent` class includes methods for serialization and deserialization:
- **`to_dict()`**: Converts the event object to a dictionary, suitable for logging or transmission.
- **`from_dict()`**: Reconstructs a `FlowEvent` object from a dictionary, enabling event reconstruction from logs.

### 3. Event Integrity
- **Required Fields**: Ensures all essential fields (`source`, `target`, `action`, `trace_id`) are present.
- **Type Safety**: Uses type hints and validation to ensure data consistency.
- **Flexible Construction**: Supports both direct instantiation and dictionary-based creation.

## Source Code with English Comments

```python
"""
Event definition module

This module defines the core event structure used by MermaidTrace to represent
interactions between system components. Each FlowEvent corresponds to a single
arrow in the Mermaid sequence diagram.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class FlowEvent:
    """
    Represents a single interaction (call or return) in the Mermaid diagram.
    
    Attributes:
        source: The participant initiating the interaction (caller)
        target: The participant receiving the interaction (callee)
        action: The operation being performed (displayed on the arrow)
        message: Additional context or description for the interaction
        params: Formatted function arguments
        result: Function return value
        is_return: Whether this event represents a return (True) or call (False)
        is_error: Whether this event represents an error
        error_message: Error message if is_error is True
        stack_trace: Full stack trace if is_error is True
        trace_id: Unique identifier linking related events
    """

    source: str
    target: str
    action: str
    message: str
    params: str = ""
    result: str = ""
    is_return: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert FlowEvent to dictionary for logging or serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the event
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FlowEvent:
        """
        Create FlowEvent from dictionary (for deserialization from logs).
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            FlowEvent: Reconstructed event object
        """
        return cls(**data)
```