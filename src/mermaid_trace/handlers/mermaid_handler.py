"""
Mermaid File Handler Module

This module provides a custom logging handler that writes FlowEvent objects to
Mermaid (.mmd) files. It handles the Mermaid syntax formatting, file headers, and
ensures thread-safe file writing.
"""

import logging
import os


class MermaidFileHandler(logging.FileHandler):
    """
    A custom logging handler that writes `FlowEvent` objects to a Mermaid (.mmd) file.

    Strategy & Optimization:
    1. **Inheritance**: Inherits from `logging.FileHandler` to leverage robust,
       thread-safe file writing capabilities (locking, buffering) provided by the stdlib.
    2. **Header Management**: Automatically handles the Mermaid file header
       (`sequenceDiagram`, `title`, `autonumber`) to ensure the output file
       is a valid Mermaid document. It smartly detects if the file is new or
       being appended to.
    3. **Deferred Formatting**: The actual string conversion happens in the `emit`
       method (via the formatter), keeping the handler focused on I/O.
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ):
        """
        Initialize the Mermaid file handler.

        Args:
            filename (str): The path to the output .mmd file.
            title (str, optional): The title of the Mermaid diagram. Defaults to "Log Flow".
            mode (str, optional): File open mode. 'w' (overwrite) or 'a' (append). Defaults to "a".
            encoding (str, optional): File encoding. Defaults to "utf-8".
            delay (bool, optional): If True, file opening is deferred until the first call to emit.
                                   Useful to avoid creating empty files if no logs occur. Defaults to False.
        """
        # Ensure the directory exists to prevent FileNotFoundError when opening the file
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)

        # Determine if we need to write a header
        # Header is written only if:
        # 1. We are overwriting the file (mode='w'), or
        # 2. We are appending (mode='a') but the file doesn't exist or is empty
        should_write_header = False
        if mode == "w":
            should_write_header = True
        elif mode == "a":
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                should_write_header = True

        # Initialize the parent FileHandler (opens the file unless delay=True)
        super().__init__(filename, mode, encoding, delay)
        self.title = title

        # Write the header immediately if needed
        if should_write_header:
            self._write_header()

    def _write_header(self) -> None:
        """
        Writes the initial Mermaid syntax lines to the file.

        This setup is required for Mermaid JS or Live Editor to render the diagram correctly.
        It defines:
        - Diagram type (sequenceDiagram)
        - Title of the diagram
        - Autonumbering of steps

        Thread Safety: Uses the handler's internal lock to prevent concurrent writes
        when delay=True, ensuring the header is written only once.
        """
        # Use the handler's internal lock to ensure thread safety
        assert self.lock is not None, "Handler lock should always be initialized"
        with self.lock:
            # Write to the existing stream if available, otherwise open temporarily
            if self.stream:
                # Stream is already open (delay=False or emit() has been called)
                self.stream.write("sequenceDiagram\n")
                self.stream.write(f"    title {self.title}\n")
                self.stream.write("    autonumber\n")
                # Flush ensures the header is written to disk immediately
                self.flush()
            else:
                # Handle delay=True case: file not yet opened
                # Temporarily open the file just to write the header
                with open(self.baseFilename, self.mode, encoding=self.encoding) as f:
                    f.write("sequenceDiagram\n")
                    f.write(f"    title {self.title}\n")
                    f.write("    autonumber\n")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record and write it to the Mermaid file.

        This method overrides the parent's emit method to filter out non-FlowEvent records.

        Optimization:
        - Checks for `flow_event` attribute first, acting as a high-performance filter
        - Only processes records containing structured FlowEvent data
        - Delegates actual writing to parent's emit() method, which handles locking and flushing

        Args:
            record (logging.LogRecord): The log record to process
        """
        # Only process records that contain our structured FlowEvent data
        # This allows the handler to be attached to the root logger without processing
        # irrelevant system logs
        if hasattr(record, "flow_event"):
            super().emit(record)
