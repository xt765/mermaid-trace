import pytest
from unittest.mock import patch, MagicMock
from mermaid_trace.cli import serve, main, _create_handler
import sys
from pathlib import Path
import io
from typing import Any


def test_cli_serve_not_found(capsys: Any) -> None:
    with pytest.raises(SystemExit):
        serve("non_existent_file.mmd")
    captured = capsys.readouterr()
    assert "not found" in captured.out


@patch("mermaid_trace.cli.webbrowser.open")
@patch("mermaid_trace.cli.socketserver.ThreadingTCPServer")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.read_text", return_value="sequenceDiagram")
@patch("pathlib.Path.stat")
def test_cli_serve_basic(
    mock_stat: Any,
    mock_read: Any,
    mock_exists: Any,
    mock_server: Any,
    mock_browser: Any,
) -> None:
    mock_stat.return_value.st_mtime = 12345

    server_instance = MagicMock()
    mock_server.return_value.__enter__.return_value = server_instance
    server_instance.serve_forever.return_value = None

    serve("test.mmd", port=9000)

    mock_browser.assert_called_with("http://localhost:9000")
    server_instance.serve_forever.assert_called_once()


@patch("mermaid_trace.cli.HAS_WATCHDOG", True)
@patch("mermaid_trace.cli.FileSystemEventHandler", create=True)
@patch("mermaid_trace.cli.Observer", create=True)
@patch("mermaid_trace.cli.webbrowser.open")
@patch("mermaid_trace.cli.socketserver.ThreadingTCPServer")
@patch("pathlib.Path.exists", return_value=True)
def test_cli_watchdog_integration(
    mock_exists: Any,
    mock_server: Any,
    mock_browser: Any,
    mock_observer: Any,
    mock_handler: Any,
) -> None:
    mock_server.return_value.__enter__.return_value = MagicMock()

    observer_instance = MagicMock()
    mock_observer.return_value = observer_instance

    serve("test.mmd")

    mock_observer.assert_called_once()
    observer_instance.start.assert_called_once()


def test_cli_main() -> None:
    with patch.object(
        sys, "argv", ["mermaid-trace", "serve", "flow.mmd", "--port", "8080"]
    ):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_with("flow.mmd", 8080)


def test_handler_logic() -> None:
    path = MagicMock(spec=Path)
    path.read_text.return_value = "graph TD; A-->B;"
    path.stat.return_value.st_mtime = 1000

    HandlerClass = _create_handler("test.mmd", path)

    # Test GET /
    # Patch the __init__ to avoid calling super().__init__ which requires real sockets
    with patch("http.server.SimpleHTTPRequestHandler.__init__", return_value=None):
        handler = HandlerClass(MagicMock(), MagicMock(), MagicMock())

    handler.path = "/"
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_GET()

    output = handler.wfile.getvalue().decode("utf-8")
    assert "graph TD; A-->B;" in output
    assert "MermaidTrace Flow Preview: test.mmd" in output

    # Test GET /_status
    handler.wfile = io.BytesIO()
    handler.path = "/_status"
    handler.do_GET()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "1000" in output

    # Test Error handling
    path.read_text.side_effect = Exception("Read Error")
    handler.wfile = io.BytesIO()
    handler.path = "/"
    handler.do_GET()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "Read Error" in output
