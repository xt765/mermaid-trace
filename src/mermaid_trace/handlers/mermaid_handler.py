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
    4. **Lazy Initialization**: File opening and header writing are deferred until
       the first log is emitted, supporting `delay=True` correctly.
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

        # Initialize the parent FileHandler
        # We rely on super() to handle the 'delay' logic for opening the stream.
        super().__init__(filename, mode, encoding, delay)
        self.title = title
        # Ensure the terminator is always a newline, as Mermaid files are line-based.
        self.terminator = "\n"

    def _write_header(self) -> None:
        """
        Writes the initial Mermaid syntax lines to the file.

        It attempts to use the attached formatter's `get_header` method if available,
        otherwise falls back to a default Mermaid sequence diagram header.
        """
        # Default header if no formatter is available
        header = f"sequenceDiagram\n    title {self.title}\n    autonumber\n\n"

        if self.formatter and hasattr(self.formatter, "get_header"):
            try:
                # Use formatter's header if it provides one
                header = self.formatter.get_header(self.title)
                # Ensure it ends with at least one newline for safety
                if not header.endswith("\n"):
                    header += "\n"
            except Exception:
                # Fallback if formatter fails
                pass

        if self.stream:
            self.stream.write(header)
            # Ensure it's physically on disk before any logs follow
            self.stream.flush()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record and write it to the Mermaid file.

        This method overrides the parent's emit method to:
        1. Filter out non-FlowEvent records
        2. Lazily write the file header if the file is empty/new
        3. Handle intelligent collapsing via the formatter
        4. Delegate writing to the parent class

        Args:
            record (logging.LogRecord): The log record to process
        """
        # Only process records that contain our structured FlowEvent data
        if hasattr(record, "flow_event"):
            # Ensure stream is open
            if self.stream is None:
                self.stream = self._open()

            # Check if we need to write the header.
            # If the file is empty (position 0), it's either a new file (w)
            # or an empty existing file (a). In both cases, we need a header.
            if self.stream.tell() == 0:
                self._write_header()

            # Format the record. Our custom MermaidFormatter might return an empty string
            # if it's currently collapsing/buffering repetitive calls.
            msg = self.format(record)
            if msg:
                # If we have a message (either a single event or a flushed collapsed batch),
                # write it to the stream.
                if self.stream:
                    self.stream.write(msg + self.terminator)
                    # We do NOT call self.flush() here because that would
                    # trigger formatter.flush() and clear our collapsing buffer.
                    # Standard FileHandler.emit does not call flush() either.
                    # The OS and Python's internal buffering handle performance.

    def flush(self) -> None:
        """
        Flushes both the underlying file stream and any buffered events in the formatter.
        """
        # 1. Flush any collapsed batch remaining in the formatter
        if self.formatter and hasattr(self.formatter, "flush"):
            try:
                msg = self.formatter.flush()
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
            except Exception:
                pass

        # 2. Flush the file stream
        super().flush()

    def close(self) -> None:
        """
        Ensures all buffered events are written before closing the file.
        """
        self.flush()
        super().close()
