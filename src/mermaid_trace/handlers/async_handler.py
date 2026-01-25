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
    """
    
    def __init__(self, handlers: List[logging.Handler], queue_size: int = -1):
        """
        Initialize the async handler.
        
        Args:
            handlers: A list of handlers that should receive the logs from the queue.
                      (e.g., [MermaidFileHandler(...)])
            queue_size: The maximum size of the queue. -1 means infinite.
        """
        self._log_queue = queue.Queue(queue_size)
        super().__init__(self._log_queue)
        
        self._listener = logging.handlers.QueueListener(
            self._log_queue, 
            *handlers, 
            respect_handler_level=True
        )
        self._listener.start()
        
        # Ensure the listener is stopped and queue is flushed upon exit
        atexit.register(self.stop)

    def stop(self) -> None:
        """
        Stops the listener and flushes the queue.
        
        This is registered with `atexit` to ensure that all pending logs 
        are written to disk before the application terminates.
        """
        if self._listener:
            self._listener.stop()
            self._listener = None
