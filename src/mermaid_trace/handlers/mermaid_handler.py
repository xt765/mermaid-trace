"""
Mermaid File Handler Module

This module provides a custom logging handler that writes FlowEvent objects to
Mermaid (.mmd) files. It handles the Mermaid syntax formatting, file headers, and
ensures thread-safe file writing.
"""

import logging
import logging.handlers
import os
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class MermaidHandlerMixin:
    """
    Mixin to provide Mermaid-specific logic to logging handlers.
    """

    title: str
    terminator: str
    # These are provided by logging.Handler or its subclasses
    formatter: Optional[logging.Formatter]
    stream: Any

    def _write_header(self) -> None:
        """
        Writes the initial Mermaid syntax lines to the file.
        """
        # Default header if no formatter is available
        header = f"sequenceDiagram\n    title {self.title}\n    autonumber\n\n"

        if self.formatter and hasattr(self.formatter, "get_header"):
            try:
                # Use formatter's header if it provides one
                header = getattr(self.formatter, "get_header")(self.title)
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
        Handles rotation if the parent class supports it.
        """
        # Only process records that contain our structured FlowEvent data
        if not hasattr(record, "flow_event"):
            return

        try:
            # 1. Handle Rotation (for RotatingFileHandler and TimedRotatingFileHandler)
            if hasattr(self, "shouldRollover") and getattr(self, "shouldRollover")(
                record
            ):
                getattr(self, "doRollover")()

            # 2. Ensure stream is open (handles delay=True)
            if self.stream is None:
                if hasattr(self, "_open"):
                    self.stream = getattr(self, "_open")()

            # 3. Check if we need to write the header.
            # If the file is empty (position 0), it's either a new file,
            # an empty existing file, or a freshly rotated file.
            if self.stream and hasattr(self.stream, "tell") and self.stream.tell() == 0:
                self._write_header()

            # 4. Format the record.
            # Our custom MermaidFormatter might return an empty string
            # if it's currently collapsing/buffering repetitive calls.
            if hasattr(self, "format"):
                msg = getattr(self, "format")(record)
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
                    # Note: We do NOT call self.flush() here to allow
                    # the formatter's collapsing buffer to work correctly.
        except Exception:
            if hasattr(self, "handleError"):
                getattr(self, "handleError")(record)

    def flush(self) -> None:
        """
        Flushes both the underlying file stream and any buffered events in the formatter.
        """
        if self.formatter and hasattr(self.formatter, "flush"):
            try:
                msg = getattr(self.formatter, "flush")()
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
            except Exception:
                pass

        # Use hasattr to check if super() has flush, to avoid Mypy errors with mixins
        super_flush = getattr(super(), "flush", None)
        if callable(super_flush):
            super_flush()

    def close(self) -> None:
        """
        Ensures all buffered events are written before closing the file.
        """
        self.flush()
        super_close = getattr(super(), "close", None)
        if callable(super_close):
            super_close()


class MermaidFileHandler(MermaidHandlerMixin, logging.FileHandler):
    """
    A custom logging handler that writes `FlowEvent` objects to a Mermaid (.mmd) file.
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ):
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(filename, mode, encoding, delay)
        self.title = title
        self.terminator = "\n"


class RotatingMermaidFileHandler(
    MermaidHandlerMixin, logging.handlers.RotatingFileHandler
):
    """
    Rotating version of the MermaidFileHandler.
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: str = "utf-8",
        delay: bool = False,
    ):  # noqa: PLR0913
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.title = title
        self.terminator = "\n"


class TimedRotatingMermaidFileHandler(
    MermaidHandlerMixin, logging.handlers.TimedRotatingFileHandler
):
    """
    Timed rotating version of the MermaidFileHandler.
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        when: str = "h",
        interval: int = 1,
        backupCount: int = 0,
        encoding: str = "utf-8",
        delay: bool = False,
        utc: bool = False,
        atTime: Any = None,
    ):  # noqa: PLR0913
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime
        )
        self.title = title
        self.terminator = "\n"
