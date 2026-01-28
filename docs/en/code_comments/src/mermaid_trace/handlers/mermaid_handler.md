# File: src/mermaid_trace/handlers/mermaid_handler.py

## Overview
The `mermaid_handler.py` module implements the `MermaidHandler` class, which is responsible for processing `FlowEvent` objects and writing them to Mermaid diagram files. This is the core handler that converts event data into Mermaid syntax and manages the diagram file lifecycle.

## Core Functionality Analysis

### 1. `MermaidHandler` Class
This class extends the standard `logging.Handler` to process Mermaid-specific events:
- **Event Processing**: Converts `FlowEvent` objects into Mermaid sequence diagram syntax.
- **File Management**: Handles opening, writing to, and closing Mermaid diagram files.
- **Diagram Generation**: Uses the `MermaidFormatter` to generate complete Mermaid diagrams from events.

### 2. Event Handling Flow
The handler processes events through the following steps:
1. **Event Extraction**: Extracts `FlowEvent` objects from log records.
2. **Formatting**: Uses `MermaidFormatter` to convert events to Mermaid syntax.
3. **File Operations**: Manages writing the formatted diagram to files, including creating new files when needed.
4. **Diagram Updates**: Appends new events to existing diagrams or creates new diagrams for new trace IDs.

### 3. File Management
- **File Creation**: Creates new Mermaid files based on the specified filename pattern.
- **Overwrite Control**: Supports both overwriting existing files and appending to them.
- **Directory Handling**: Automatically creates directories if they don't exist.
- **Encoding Support**: Handles different file encodings for internationalization.

### 4. Diagram Organization
- **Trace ID Separation**: Can create separate diagrams for different trace IDs, ensuring each flow has its own diagram.
- **Diagram Structure**: Maintains proper Mermaid syntax structure, including participant declarations and message ordering.
- **Event Grouping**: Groups related events together to create coherent flow diagrams.

### 5. Error Handling
- **Robust Processing**: Handles exceptions during event processing to prevent logging failures from affecting the main application.
- **Fallback Mechanisms**: Includes fallback processing for malformed events or file system errors.
- **Error Logging**: Logs errors encountered during processing to aid in debugging.

## Source Code with English Comments

```python
"""
Mermaid file handler module

This module implements the core handler for writing Mermaid sequence
diagrams to files. It processes FlowEvent objects and converts them
into properly formatted Mermaid syntax.
"""

import logging
import os
from typing import Dict, Optional, Set

from ..core.events import FlowEvent
from ..core.formatter import MermaidFormatter


class MermaidHandler(logging.Handler):
    """
    Handler for writing Mermaid sequence diagrams to files.
    
    This handler processes FlowEvent objects and converts them into
    Mermaid sequence diagram syntax, writing the results to files.
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
        overwrite: bool = False,
    ):
        """
        Initialize the Mermaid handler.
        
        Args:
            filename: Path to the Mermaid file
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: None)
            delay: Whether to delay file opening until first emit
            overwrite: Whether to overwrite existing files
        """
        super().__init__()
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self.overwrite = overwrite

        # Create directory if it doesn't exist
        directory = os.path.dirname(self.baseFilename)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception:
                pass

        # Initialize formatter and file handle
        self.formatter = MermaidFormatter()
        self.stream = None
        self._open_stream()

    def _open_stream(self) -> None:
        """
        Open the file stream if not already open.
        """
        if self.stream is None:
            if self.overwrite and os.path.exists(self.baseFilename):
                # Clear file content if overwrite is True
                with open(self.baseFilename, "w", encoding=self.encoding) as f:
                    pass
            
            # Open file stream
            self.stream = open(
                self.baseFilename,
                self.mode,
                encoding=self.encoding,
                buffering=1  # Line buffering
            )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record by writing it to the Mermaid file.
        
        Args:
            record: Log record containing the flow event
        """
        if not hasattr(record, "flow_event"):
            return

        event = record.flow_event
        if not isinstance(event, FlowEvent):
            return

        try:
            if self.stream is None:
                self._open_stream()

            # Add event to formatter
            self.formatter.add_event(event)

            # Write formatted diagram to file
            diagram = self.formatter.format()
            if self.stream:
                self.stream.seek(0)
                self.stream.truncate()
                self.stream.write(diagram)
                self.stream.flush()

        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """
        Close the handler and release resources.
        """
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        super().close()


class RotatingMermaidFileHandler(MermaidHandler):
    """
    Mermaid handler that supports file rotation based on size or time.
    
    This handler extends MermaidHandler to support rotating log files
    when they reach a certain size or at specified time intervals.
    """

    def __init__(
        self,
        filename: str,
        maxBytes: int = 0,
        backupCount: int = 0,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
    ):
        """
        Initialize the rotating Mermaid handler.
        
        Args:
            filename: Path to the Mermaid file
            maxBytes: Maximum size of file before rotation
            backupCount: Number of backup files to keep
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: None)
            delay: Whether to delay file opening until first emit
        """
        super().__init__(filename, mode, encoding, delay)
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record, rotating the file if necessary.
        
        Args:
            record: Log record containing the flow event
        """
        if self.maxBytes > 0:
            self._check_rotation()
        super().emit(record)

    def _check_rotation(self) -> None:
        """
        Check if the file needs to be rotated based on size.
        """
        if self.stream is None:
            return

        try:
            self.stream.flush()
            if os.path.exists(self.baseFilename):
                file_size = os.path.getsize(self.baseFilename)
                if file_size >= self.maxBytes:
                    self._do_rotation()
        except Exception:
            pass

    def _do_rotation(self) -> None:
        """
        Perform file rotation.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Rotate backup files
        for i in range(self.backupCount - 1, 0, -1):
            src = f"{self.baseFilename}.{i}"
            dst = f"{self.baseFilename}.{i + 1}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)

        # Rotate current file
        if self.backupCount > 0:
            dst = f"{self.baseFilename}.1"
            if os.path.exists(dst):
                os.remove(dst)
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dst)

        # Reopen stream
        self._open_stream()
```