"""
Asynchronous Mermaid Handler Module
===================================

This module implements a non-blocking logging handler that leverages a background thread
and a queue mechanism to handle log records. This design pattern is crucial for
high-performance applications where I/O latency (like writing to disk) in the main
execution thread is unacceptable.

Key Components:
1.  **AsyncMermaidHandler**: The frontend handler that quickly pushes logs to a queue.
2.  **Queue**: A thread-safe FIFO buffer (producer-consumer pattern).
3.  **QueueListener**: A background worker that pulls logs from the queue and
    writes them to the actual destination (e.g., a file).

By decoupling log generation from log persistence, we ensure that the application's
core logic remains responsive even during bursts of logging activity.
"""

import logging
import logging.handlers
import queue
import atexit
from typing import List, Optional, cast


class AsyncMermaidHandler(logging.handlers.QueueHandler):
    """
    A high-performance, non-blocking logging handler using the Producer-Consumer pattern.

    This handler acts as the "Producer". It intercepts log records and immediately
    pushes them into a thread-safe queue. A separate "Consumer" thread (managed by
    QueueListener) asynchronously picks up these records and dispatches them to the
    actual underlying handlers (like MermaidFileHandler).

    **Architecture & Benefits:**
    - **Non-Blocking I/O**: The main application thread never waits for disk writes.
      It only waits for the (very fast) queue insertion operation.
    - **Burst Handling**: The queue acts as a buffer, absorbing sudden spikes in
      log volume without slowing down the application.
    - **Thread Safety**: Uses Python's thread-safe `queue.Queue` for synchronization.
    - **Graceful Shutdown**: Integrates with `atexit` to ensure pending logs are
      flushed before the application terminates.

    **Usage:**
    Typically used to wrap a standard file handler:

    ```python
    file_handler = MermaidFileHandler("trace.mmd")
    async_handler = AsyncMermaidHandler(handlers=[file_handler])
    logger.addHandler(async_handler)
    ```
    """

    def __init__(self, handlers: List[logging.Handler], queue_size: int = 1000):
        """
        Initialize the asynchronous handler infrastructure.

        This setup involves three main steps:
        1.  Creating a bounded queue to hold log records.
        2.  Initializing the parent QueueHandler.
        3.  Starting a background QueueListener thread to process the queue.

        Args:
            handlers (List[logging.Handler]): A list of "real" handlers that will
                eventually write the logs (e.g., to a file or stream). The background
                listener will pass records to these handlers.
            queue_size (int): The maximum number of log records the queue can hold.
                Defaults to 1000.
                *Trade-off*: A larger queue consumes more memory but handles larger
                bursts. A smaller queue saves memory but increases the risk of
                dropped logs if the consumer falls behind.
        """
        # 1. Create a bounded queue (Producer-Consumer buffer).
        # We use a bounded queue to prevent uncontrolled memory growth if the
        # consumer (writer) cannot keep up with the producer (application).
        self._log_queue: queue.Queue[logging.LogRecord] = queue.Queue(queue_size)
        self._queue_size = queue_size

        # 2. Initialize the parent QueueHandler.
        # This configures self.queue, which is used by the emit() method.
        super().__init__(self._log_queue)

        # 3. Initialize and start the QueueListener (The Consumer).
        # The QueueListener runs in a separate daemon thread. It continuously:
        #   a. Blocks waiting for a record from the queue.
        #   b. Retrieves the record.
        #   c. Passes it to the provided 'handlers'.
        #
        # respect_handler_level=True ensures that if the underlying handler is set
        # to ERROR but the logger is INFO, the underlying handler won't write INFO logs.
        self._listener: Optional[logging.handlers.QueueListener] = (
            logging.handlers.QueueListener(
                self._log_queue, *handlers, respect_handler_level=True
            )
        )

        # Start the background worker thread.
        self._listener.start()

        # 4. Ensure Graceful Shutdown.
        # Register the stop method to be called automatically when the Python
        # interpreter exits. This is critical for flushing the queue so no logs are lost.
        atexit.register(self.stop)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the queue (Producer action).

        This method overrides the standard logging emit to implement a non-blocking
        strategy with a fallback.

        **Logic Flow:**
        1.  Attempt to put the record into the queue.
        2.  Use a short timeout (0.1s) to avoid blocking the main application
            indefinitely if the queue is full (backpressure).
        3.  If the queue remains full after the timeout, drop the record to preserve
            application stability, but print a warning to stderr.

        Args:
            record (logging.LogRecord): The log event to be processed.
        """
        try:
            # We explicitly cast self.queue because QueueHandler.queue is typed
            # generically in some stubs, but we know it's a queue.Queue.
            queue_instance = cast(queue.Queue[logging.LogRecord], self.queue)

            # Attempt to enqueue the record.
            # block=True, timeout=0.1: We wait briefly for a slot to open up.
            # This balances "trying to save the log" vs "not freezing the app".
            queue_instance.put(record, block=True, timeout=0.1)

        except queue.Full:
            # **Queue Overflow Handling**
            # If we reach here, the consumer (writer) is too slow or the burst
            # is too large. We must drop data to keep the application running.

            # Only warn for important logs to avoid spamming stderr.
            if record.levelno >= logging.WARNING:
                # We use print() instead of logging to avoid infinite recursion
                # (logging about a logging failure).
                print(
                    f"WARNING: AsyncMermaidHandler queue is full (size: {self._queue_size}), "
                    f"dropping log record: {record.msg}"
                )

    def stop(self) -> None:
        """
        Clean up resources and flush pending logs.

        This method is called automatically via atexit or can be called manually.

        **Shutdown Sequence:**
        1.  Check if the listener is active.
        2.  Call `listener.stop()`. This sends a special "sentinel" (None) to the queue.
        3.  The background thread sees the sentinel, stops waiting for new logs,
            processes any remaining items in the queue, and then terminates.
        4.  Explicitly flush all underlying handlers to ensure stateful formatters
            write their final buffered events.
        """
        if self._listener:
            # We keep a reference to handlers to flush them after listener stops
            handlers = self._listener.handlers
            try:
                # Stop the listener. This blocks until the listener thread joins,
                # ensuring all records currently in the queue are processed.
                self._listener.stop()
                self._listener = None

                # Crucial step for stateful formatters:
                # After the listener has finished emitting all records from the queue,
                # we must tell the handlers to flush their internal buffers.
                for handler in handlers:
                    try:
                        handler.flush()
                    except Exception:
                        pass
            except Exception:
                # We catch generic exceptions here because during interpreter shutdown,
                # some modules (like queue) might already be partially unloaded.
                pass
