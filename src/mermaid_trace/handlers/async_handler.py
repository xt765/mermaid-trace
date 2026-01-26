"""
Asynchronous Mermaid Handler Module

This module provides a non-blocking logging handler that uses a background thread
for writing logs. It's designed to improve performance in high-throughput applications
by decoupling the logging I/O from the main execution thread.
"""

import logging
import logging.handlers
import queue
import atexit
from typing import List, Optional


class AsyncMermaidHandler(logging.handlers.QueueHandler):
    """
    A non-blocking logging handler that uses a background thread to write logs.

    This handler pushes log records to a queue, which are then picked up by a
    QueueListener running in a separate thread and dispatched to the actual
    handlers (e.g., MermaidFileHandler).

    This architecture provides several benefits:
    - Main thread doesn't block waiting for disk I/O
    - Logs are processed in the background
    - Better performance in high-throughput applications
    - Smooth handling of burst traffic
    """

    def __init__(self, handlers: List[logging.Handler], queue_size: int = 1000):
        """
        Initialize the async handler.

        Args:
            handlers: A list of handlers that should receive the logs from the queue.
                      These are typically MermaidFileHandler instances.
            queue_size: The maximum size of the queue. Default is 1000.
                       If the queue fills up, new log records may be dropped.
        """
        # Create a bounded queue with the specified size
        self._log_queue: queue.Queue[logging.LogRecord] = queue.Queue(queue_size)
        self._queue_size = queue_size

        # Initialize parent QueueHandler with our queue
        super().__init__(self._log_queue)

        # Initialize QueueListener to process records from the queue
        # It starts an internal thread to monitor the queue
        # respect_handler_level=True ensures the target handlers' log levels are respected
        self._listener: Optional[logging.handlers.QueueListener] = (
            logging.handlers.QueueListener(
                self._log_queue, *handlers, respect_handler_level=True
            )
        )

        # Start the listener thread
        self._listener.start()

        # Register stop method to be called on program exit
        # This ensures all pending logs are written to disk before termination
        atexit.register(self.stop)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the queue with a timeout and drop policy.

        If the queue is full, this method will attempt to put the record with
        a short timeout. If that fails, it will drop the record and print a warning.

        Args:
            record: The log record to emit
        """
        from typing import cast

        try:
            # Try to put the record in the queue with a short timeout (0.1 seconds)
            # This prevents the main thread from blocking indefinitely if the queue is full
            # Use cast to tell Mypy this is a queue.Queue instance
            queue_instance = cast(queue.Queue[logging.LogRecord], self.queue)
            queue_instance.put(record, block=True, timeout=0.1)
        except queue.Full:
            # If queue is full, log a warning and drop the record
            if record.levelno >= logging.WARNING:
                # Avoid infinite recursion by not using self.logger
                print(
                    f"WARNING: AsyncMermaidHandler queue is full (size: {self._queue_size}), dropping log record: {record.msg}"
                )

    def stop(self) -> None:
        """
        Stops the listener and flushes all pending logs from the queue.

        This method is registered with `atexit` to ensure that all pending logs
        are written to disk before the application terminates.
        """
        if self._listener:
            try:
                # Stop the listener - this will process all remaining records in the queue
                self._listener.stop()
                self._listener = None
            except queue.Full:
                # Handle case where queue is full when trying to put sentinel value
                # The listener thread may still be processing, but we can safely exit
                pass
