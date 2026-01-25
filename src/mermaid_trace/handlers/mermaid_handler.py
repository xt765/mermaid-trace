import logging
from typing import Optional
from ..core.events import FlowEvent

class MermaidFileHandler(logging.Handler):
    """
    A custom logging handler that writes `FlowEvent` objects directly to a Mermaid (.mmd) file.
    
    This handler listens for logs containing a `flow_event` in their `extra` dictionary
    and appends them to the file in Mermaid Sequence Diagram syntax.
    """
    def __init__(self, filename: str, title: str = "Log Flow", mode: str = 'w'):
        """
        Initialize the handler.
        
        Args:
            filename (str): The path to the output .mmd file.
            title (str): The title of the Mermaid diagram.
            mode (str): File open mode. 'w' (overwrite) or 'a' (append). 
                        Defaults to 'w' which initializes a new diagram.
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.title = title
        
        # Initialize file with the Mermaid diagram header if in write mode
        if mode == 'w':
            self._write_header()

    def _write_header(self) -> None:
        """
        Writes the initial Mermaid syntax lines (diagram type, title, configuration).
        """
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write("sequenceDiagram\n")
            f.write(f"    title {self.title}\n")
            f.write("    autonumber\n")  # Automatically number the steps

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record.
        
        This method checks if the log record contains a 'flow_event' attribute.
        If present, it converts the event to a Mermaid string and appends it to the file.
        
        Args:
            record (logging.LogRecord): The log record to process.
        """
        # Check if this record has a flow event attached.
        # The `trace` decorator attaches 'flow_event' to the 'extra' dict, 
        # which the logging system merges into the LogRecord object.
        event: Optional[FlowEvent] = getattr(record, 'flow_event', None)
        
        if event:
            try:
                # Convert the event to a diagram line
                line = event.to_mermaid_line()
                
                # Append to the file immediately (simple implementation)
                # Note: In high-throughput systems, you might want to buffer this.
                with open(self.filename, 'a', encoding='utf-8') as f:
                    f.write(f"    {line}\n")
            except Exception:
                # If writing fails, fall back to standard error handling
                self.handleError(record)
