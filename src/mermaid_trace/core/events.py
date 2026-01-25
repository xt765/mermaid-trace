from dataclasses import dataclass, field
import time
from typing import Optional

@dataclass
class FlowEvent:
    """
    Represents a single interaction or step in the execution flow.
    
    This data structure captures all necessary metadata to generate one line
    of a Mermaid sequence diagram. It is passed from the tracing decorators
    to the logging handler.
    
    Attributes:
        source (str): The name of the participant initiating the action (caller).
        target (str): The name of the participant receiving the action (callee).
        action (str): A brief description of the action (e.g., function name).
        message (str): The text to display on the diagram arrow.
        timestamp (float): Unix timestamp of when the event occurred.
        is_return (bool): True if this event represents a return from a function call.
        is_error (bool): True if this event represents an exception/error.
        error_message (Optional[str]): The error message if `is_error` is True.
        params (Optional[str]): Stringified function arguments (for request events).
        result (Optional[str]): Stringified return value (for response events).
    """
    source: str
    target: str
    action: str
    message: str
    timestamp: float = field(default_factory=time.time)
    is_return: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    params: Optional[str] = None
    result: Optional[str] = None
    
    def to_mermaid_line(self) -> str:
        """
        Converts this event into a valid Mermaid sequence diagram syntax line.
        
        Returns:
            str: A string like "A->>B: message" or "B-->>A: return".
        """
        # Sanitize names to ensure they are valid Mermaid participant identifiers
        # e.g., "My Class" -> "My_Class"
        src = self._sanitize(self.source)
        tgt = self._sanitize(self.target)
        
        # Determine arrow type
        # ->> : Solid line with arrowhead (synchronous call)
        # -->> : Dotted line with arrowhead (return)
        # --x : Dotted line with cross (error)
        arrow = "-->>" if self.is_return else "->>"
        
        # Format the message based on event type
        if self.is_error:
            arrow = "--x"
            msg = f"Error: {self.error_message}"
        elif self.is_return:
            msg = f"Return: {self.result}" if self.result else "Return"
        else:
            # For requests, include parameters if available
            msg = f"{self.message}({self.params})" if self.params else self.message
            
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """
        Replaces characters in participant names that might break Mermaid syntax.
        
        Args:
            name (str): The raw participant name.
            
        Returns:
            str: The sanitized name safe for Mermaid usage.
        """
        # Replace spaces, dots, and hyphens with underscores
        return name.replace(" ", "_").replace(".", "_").replace("-", "_")
