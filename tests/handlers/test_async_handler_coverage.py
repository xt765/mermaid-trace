import logging
import queue
from mermaid_trace.handlers.async_handler import AsyncMermaidHandler
from unittest.mock import MagicMock, patch


def test_async_handler_emit_queue_full():
    # Test queue full behavior
    mock_handler = MagicMock(spec=logging.Handler)
    mock_handler.level = logging.INFO
    # Create handler with small queue size
    async_handler = AsyncMermaidHandler(handlers=[mock_handler], queue_size=1)

    # Fill the queue
    record1 = logging.LogRecord("name", logging.INFO, "path", 1, "msg1", None, None)
    async_handler.emit(record1)

    # Try to emit another record, which should block then timeout
    record2 = logging.LogRecord("name", logging.WARNING, "path", 1, "msg2", None, None)

    # We mock queue.put to simulate timeout/full
    with patch.object(async_handler.queue, "put", side_effect=queue.Full):
        # Capture print output
        with patch("builtins.print") as mock_print:
            async_handler.emit(record2)
            # Should print warning for WARNING level
            mock_print.assert_called()
            assert "AsyncMermaidHandler queue is full" in mock_print.call_args[0][0]

    # Clean up
    async_handler.stop()


def test_async_handler_stop_exception():
    mock_handler = MagicMock(spec=logging.Handler)
    mock_handler.level = logging.INFO
    async_handler = AsyncMermaidHandler(handlers=[mock_handler])

    # Mock listener.stop to raise exception
    assert async_handler._listener is not None
    with patch.object(
        async_handler._listener, "stop", side_effect=Exception("Stop error")
    ):
        # async_handler.stop() should catch and ignore the exception from listener.stop()
        async_handler.stop()


def test_async_handler_stop_flush_exception():
    mock_handler = MagicMock(spec=logging.Handler)
    mock_handler.level = logging.INFO
    mock_handler.flush.side_effect = Exception("Flush error")
    async_handler = AsyncMermaidHandler(handlers=[mock_handler])

    # Should not raise exception
    async_handler.stop()
