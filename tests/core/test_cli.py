import pytest
from unittest.mock import patch
from mermaid_trace.cli import serve, main
import sys


def test_cli_serve_success() -> None:
    """Test that serve calls run_server when dependencies are present."""
    with patch("mermaid_trace.server.HAS_SERVER_DEPS", True):
        with patch("mermaid_trace.server.run_server") as mock_run_server:
            serve("test.mmd", 9000)
            mock_run_server.assert_called_once_with("test.mmd", 9000)


def test_cli_serve_missing_deps(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that serve exits and prints error when dependencies are missing."""
    with patch("mermaid_trace.server.HAS_SERVER_DEPS", False):
        with pytest.raises(SystemExit) as excinfo:
            serve("test.mmd")
        
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Error: The preview server requires additional dependencies." in captured.out


def test_cli_main_serve() -> None:
    """Test that main parses arguments and calls serve."""
    with patch.object(sys, "argv", ["mermaid-trace", "serve", "flow.mmd", "--port", "8080"]):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8080)


def test_cli_main_serve_default_port() -> None:
    """Test that main uses default port 8000."""
    with patch.object(sys, "argv", ["mermaid-trace", "serve", "flow.mmd"]):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8000)


def test_cli_main_master_flag_ignored() -> None:
    """Test that the deprecated --master flag is ignored but accepted."""
    with patch.object(sys, "argv", ["mermaid-trace", "serve", "flow.mmd", "--master"]):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8000)
