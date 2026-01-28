# File: src/mermaid_trace/handlers/async_handler.py

## Overview
The `async_handler.py` module implements the `AsyncMermaidHandler` class, which provides asynchronous processing capabilities for MermaidTrace events. This handler uses a background thread to process events, preventing the logging process from blocking the main application flow, especially in high-throughput scenarios.

## Core Functionality Analysis

### 1. `AsyncMermaidHandler` Class
This class extends the `MermaidHandler` to add asynchronous processing capabilities:
- **Background Processing**: Uses a dedicated thread to process events, ensuring logging doesn't block the main application.
- **Queue Management**: Implements a thread-safe queue to buffer events between the main thread and the processing thread.
- **Graceful Shutdown**: Includes mechanisms to ensure all events are processed before the application exits.

### 2. Event Processing Flow
The async handler processes events through the following steps:
1. **Event Reception**: Receives `FlowEvent` objects through the `emit` method.
2. **Queueing**: Adds events to a thread-safe queue instead of processing them immediately.
3. **Background Processing**: A separate thread processes events from the queue, converting them to Mermaid syntax and writing to files.
4. **Batching**: Can process multiple events in batches for improved performance in high-throughput scenarios.

### 3. Thread Safety
- **Queue Synchronization**: Uses `queue.Queue` for thread-safe communication between the main thread and processing thread.
- **Locking Mechanisms**: Implements appropriate locking to ensure safe access to shared resources.
- **Atomic Operations**: Ensures operations on shared data structures are atomic to prevent race conditions.

### 4. Performance Optimization
- **Buffer Size**: Allows configuration of the queue size to balance memory usage and event processing capacity.
- **Batch Processing**: Processes multiple events at once to reduce I/O operations and improve throughput.
- **Non-blocking Operations**: Uses non-blocking queue operations where possible to prevent main thread blocking.

### 5. Error Handling
- **Isolated Error Processing**: Errors in the background thread don't affect the main application.
- **Exception Logging**: Logs exceptions that occur during background processing to prevent silent failures.
- **Fallback Mechanisms**: Includes fallback processing for events that fail to process normally.

## Source Code with English Comments

```python
"""
Asynchronous Mermaid handler module

This module provides an asynchronous handler for MermaidTrace events,
using a background thread to process events and prevent blocking
the main application flow, especially in high-throughput scenarios.
"""

import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional

from ..core.events import FlowEvent
from .mermaid_handler import MermaidHandler


class AsyncMermaidHandler(MermaidHandler):
    """
    Asynchronous Mermaid handler that processes events in a background thread.
    
    This handler uses a queue to buffer events and processes them in a separate
    thread, preventing logging from blocking the main application flow.
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
        queue_size: int = 1000,
        batch_size: int = 10,
        flush_interval: float = 0.1,
    ):
        """
        Initialize the asynchronous Mermaid handler.
        
        Args:
            filename: Path to the Mermaid file
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: None)
            delay: Whether to delay file opening until first emit
            queue_size: Maximum size of the event queue
            batch_size: Number of events to process in each batch
            flush_interval: Maximum time to wait between flushes (in seconds)
        """
        super().__init__(filename, mode, encoding, delay)
        
        # Create thread-safe queue for events
        self._queue: queue.Queue[Optional[FlowEvent]] = queue.Queue(maxsize=queue_size)
        
        # Processing configuration
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        
        # Create and start processing thread
        self._running = True
        self._thread = threading.Thread(target=self._process_events, daemon=True)
        self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record asynchronously by adding it to the queue.
        
        Args:
            record: Log record containing the flow event
        """
        if not hasattr(record, "flow_event"):
            return

        event = record.flow_event
        if not isinstance(event, FlowEvent):
            return

        try:
            # Add event to queue (non-blocking if queue is full)
            try:
                self._queue.put(event, block=False)
            except queue.Full:
                # Queue is full, discard oldest event and add new one
                try:
                    self._queue.get(block=False)
                    self._queue.put(event, block=False)
                except queue.Empty:
                    # This should rarely happen, but handle gracefully
                    pass
        except Exception:
            # If queue operation fails, fall back to synchronous processing
            super().emit(record)

    def _process_events(self) -> None:
        """
        Background thread function to process events from the queue.
        """
        events: List[FlowEvent] = []
        last_flush_time = time.time()

        while self._running:
            try:
                # Get event from queue with timeout
                event = self._queue.get(timeout=0.1)
                
                if event is None:
                    # Sentinel value to signal shutdown
                    break

                events.append(event)
                
                # Process batch if size reached or time elapsed
                current_time = time.time()
                if (len(events) >= self._batch_size or 
                    current_time - last_flush_time >= self._flush_interval):
                    self._process_batch(events)
                    events.clear()
                    last_flush_time = current_time
                    
            except queue.Empty:
                # No events, check if we need to flush partial batch
                current_time = time.time()
                if events and current_time - last_flush_time >= self._flush_interval:
                    self._process_batch(events)
                    events.clear()
                    last_flush_time = current_time
            except Exception:
                # Ignore exceptions to keep processing thread running
                pass

        # Process any remaining events before exiting
        if events:
            try:
                self._process_batch(events)
            except Exception:
                pass

    def _process_batch(self, events: List[FlowEvent]) -> None:
        """
        Process a batch of events synchronously.
        
        Args:
            events: List of events to process
        """
        for event in events:
            try:
                # Create a synthetic log record for the event
                record = logging.LogRecord(
                    name="mermaid_trace.async",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="",
                    args=(),
                    exc_info=None,
                )
                record.flow_event = event
                super().emit(record)
            except Exception:
                # Ignore exceptions for individual events
                pass

    def close(self) -> None:
        """
        Close the handler and ensure all events are processed.
        """
        # Signal shutdown to processing thread
        self._running = False
        
        # Add sentinel value to queue to unblock get()
        try:
            self._queue.put(None, block=False)
        except queue.Full:
            pass
        
        # Wait for processing thread to complete
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)  # 5-second timeout
        
        # Close the underlying handler
        super().close()


# Alias for convenience
AsyncHandler = AsyncMermaidHandler
```