from mermaid_trace.cli import _create_handler
from unittest.mock import MagicMock, patch
from pathlib import Path


def test_cli_handler_log_message():
    # Test that log_message does nothing (suppressed)
    path_mock = MagicMock(spec=Path)
    HandlerClass = _create_handler("test.mmd", path_mock)

    # Instantiate handler without calling super().__init__ which triggers too much logic
    handler = HandlerClass.__new__(HandlerClass)
    # Manually set attributes needed for log_message if any (none needed for this override)

    # Capture stdout/stderr to ensure nothing is printed
    with patch("sys.stderr") as stderr:
        handler.log_message("test format", "arg")
        stderr.write.assert_not_called()


def test_cli_handler_do_get_status_error():
    path_mock = MagicMock(spec=Path)
    path_mock.stat.side_effect = OSError("File not found")

    HandlerClass = _create_handler("test.mmd", path_mock)

    # Instantiate bare handler
    handler = HandlerClass.__new__(HandlerClass)
    handler.path = "/_status"
    handler.wfile = MagicMock()

    # We need to mock send_response, send_header, end_headers since they are called
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_GET()

    # Should write "0" to wfile
    handler.wfile.write.assert_called_with(b"0")


def test_cli_handler_do_get_root_read_error():
    path_mock = MagicMock(spec=Path)
    path_mock.read_text.side_effect = Exception("Read error")

    HandlerClass = _create_handler("test.mmd", path_mock)

    handler = HandlerClass.__new__(HandlerClass)
    handler.path = "/"
    handler.wfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_GET()

    # Should contain error message in the output
    # call_args[0][0] is the bytes written
    call_args = handler.wfile.write.call_args[0][0].decode("utf-8")
    assert "Failed to read file: Read error" in call_args
    assert 'const currentMtime = "0";' in call_args


def test_cli_handler_do_get_fallback():
    path_mock = MagicMock(spec=Path)
    HandlerClass = _create_handler("test.mmd", path_mock)

    handler = HandlerClass.__new__(HandlerClass)
    handler.path = "/other"

    # Mock super().do_GET. Since we can't easily mock super(), we patch the base class method
    with patch("http.server.SimpleHTTPRequestHandler.do_GET") as mock_super_get:
        handler.do_GET()
        mock_super_get.assert_called_once()
