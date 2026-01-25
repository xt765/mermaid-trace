import logging
from typing import Optional
from pathlib import Path
from ..core.events import FlowEvent

class MermaidFileHandler(logging.Handler):
    """
    A logging handler that writes FlowEvents directly to a Mermaid .mmd file.
    """
    def __init__(self, filename: str, title: str = "Log Flow", mode: str = 'w'):
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.title = title
        
        # Initialize file with header
        if mode == 'w':
            self._write_header()

    def _write_header(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write("sequenceDiagram\n")
            f.write(f"    title {self.title}\n")
            f.write("    autonumber\n")

    def emit(self, record: logging.LogRecord):
        # Check if this record has a flow event
        # It might be in record.msg if it's a special log, but we prefer 'extra' or custom attr
        # The decorator will attach 'flow_event' to the extra dict, which logging merges into record
        event: Optional[FlowEvent] = getattr(record, 'flow_event', None)
        
        if event:
            try:
                line = event.to_mermaid_line()
                with open(self.filename, 'a', encoding='utf-8') as f:
                    f.write(f"    {line}\n")
            except Exception:
                self.handleError(record)
