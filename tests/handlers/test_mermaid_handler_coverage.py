from mermaid_trace.handlers.mermaid_handler import MermaidFileHandler
from unittest.mock import MagicMock


def test_mermaid_handler_header_exception(tmp_path):
    log_file = tmp_path / "test.mmd"
    handler = MermaidFileHandler(str(log_file))

    # Mock formatter to raise exception in get_header
    mock_formatter = MagicMock()
    mock_formatter.get_header.side_effect = Exception("Header error")
    handler.setFormatter(mock_formatter)

    # Should not raise exception, just fallback
    handler._write_header()


def test_mermaid_handler_flush_exception(tmp_path):
    log_file = tmp_path / "test.mmd"
    handler = MermaidFileHandler(str(log_file))

    # Mock formatter to raise exception in flush
    mock_formatter = MagicMock()
    mock_formatter.flush.side_effect = Exception("Flush error")
    handler.setFormatter(mock_formatter)

    # Should not raise exception
    handler.flush()
