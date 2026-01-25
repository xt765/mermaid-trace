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
        Initialize the handler.

        Args:
            filename (str): The path to the output .mmd file.
            title (str): The title of the Mermaid diagram (written in the header).
            mode (str): File open mode. 'w' (overwrite) or 'a' (append).
            encoding (str): File encoding. Defaults to 'utf-8'.
            delay (bool): If True, file opening is deferred until the first call to emit.
                          Useful to avoid creating empty files if no logs occur.
        """
        # Ensure directory exists to prevent FileNotFoundError on open
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)

        # Header Strategy:
        # We need to write the "sequenceDiagram" preamble ONLY if:
        # 1. We are overwriting the file (mode='w').
        # 2. We are appending (mode='a'), but the file doesn't exist or is empty.
        # This prevents invalid Mermaid files (e.g., multiple "sequenceDiagram" lines).
        should_write_header = False
        if mode == "w":
            should_write_header = True
        elif mode == "a":
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                should_write_header = True

        # Initialize standard FileHandler (opens the file unless delay=True)
        super().__init__(filename, mode, encoding, delay)
        self.title = title

        # Write header immediately if needed.
        if should_write_header:
            self._write_header()

    def _write_header(self) -> None:
        """
        Writes the initial Mermaid syntax lines.

        This setup is required for Mermaid JS or Live Editor to render the diagram.
        It defines the diagram type (sequenceDiagram), title, and enables autonumbering.
        """
        # We use the stream directly if available, or open momentarily if delayed
        if self.stream:
            self.stream.write("sequenceDiagram\n")
            self.stream.write(f"    title {self.title}\n")
            self.stream.write("    autonumber\n")
            # Flush ensures the header is written to disk immediately,
            # so it appears even if the program crashes right after.
            self.flush()
        else:
            # Handling 'delay=True' case:
            # If the file isn't open yet, we temporarily open it just to write the header.
            # This ensures the file is valid even if the application crashes before the first log.
            with open(self.baseFilename, self.mode, encoding=self.encoding) as f:
                f.write("sequenceDiagram\n")
                f.write(f"    title {self.title}\n")
                f.write("    autonumber\n")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record.

        Optimization:
        - Checks for `flow_event` attribute first. This allows this handler
          to be attached to the root logger without processing irrelevant system logs.
          It acts as a high-performance filter before formatting.
        - Delegates the actual writing to `super().emit()`, which handles
          thread locking and stream flushing safely.
        """
        # Only process records that contain our structured FlowEvent data
        if hasattr(record, "flow_event"):
            super().emit(record)
