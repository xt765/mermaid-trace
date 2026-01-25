from dataclasses import dataclass, field
import time
from typing import Optional

@dataclass
class FlowEvent:
    """
    Represents a single interaction or step in the execution flow.
    Used to generate sequence diagrams.
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
        Converts this event into a Mermaid sequence diagram line.
        """
        # Sanitize names to be valid Mermaid participants
        src = self._sanitize(self.source)
        tgt = self._sanitize(self.target)
        
        arrow = "-->>" if self.is_return else "->>"
        
        # Add color/style for errors
        if self.is_error:
            arrow = "--x" # Different arrow for error? Or just use text
            msg = f"Error: {self.error_message}"
        elif self.is_return:
            msg = f"Return: {self.result}" if self.result else "Return"
        else:
            msg = f"{self.message}({self.params})" if self.params else self.message
            
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """Replaces invalid characters for Mermaid participant names."""
        return name.replace(" ", "_").replace(".", "_").replace("-", "_")
