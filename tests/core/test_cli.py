import pytest
from unittest.mock import patch
from mermaid_trace.cli import serve, main, get_package_version
import sys


def test_cli_serve_success() -> None:
    """Test that serve calls run_server correctly."""
    with patch("mermaid_trace.server.run_server") as mock_run_server:
        serve("test.mmd", 9000)
        mock_run_server.assert_called_once_with("test.mmd", 9000, True)


def test_cli_serve_import_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that serve handles import errors gracefully."""
    with patch.dict("sys.modules", {"mermaid_trace.server": None}):
        with pytest.raises(SystemExit) as excinfo:
            serve("test.mmd")

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Could not import server module." in captured.out


def test_cli_main_serve() -> None:
    """Test that main parses arguments and calls serve."""
    with patch.object(
        sys, "argv", ["mermaid-trace", "serve", "flow.mmd", "--port", "8080"]
    ):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8080, open_browser=True)


def test_cli_main_serve_default_port() -> None:
    """Test that main uses default port 8000."""
    with patch.object(sys, "argv", ["mermaid-trace", "serve", "flow.mmd"]):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8000, open_browser=True)


def test_cli_main_no_browser_flag() -> None:
    """Test that --no-browser flag prevents browser from opening."""
    with patch.object(
        sys, "argv", ["mermaid-trace", "serve", "flow.mmd", "--no-browser"]
    ):
        with patch("mermaid_trace.cli.serve") as mock_serve:
            main()
            mock_serve.assert_called_once_with("flow.mmd", 8000, open_browser=False)


def test_cli_main_version_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that version command displays version information."""
    with patch.object(sys, "argv", ["mermaid-trace", "version"]):
        with patch(
            "mermaid_trace.cli.get_package_version", return_value="0.7.1"
        ) as mock_version:
            main()
            mock_version.assert_called_once()
            captured = capsys.readouterr()
            assert "MermaidTrace version: 0.7.1" in captured.out


def test_get_package_version_installed() -> None:
    """Test get_package_version when package is installed."""
    with patch("mermaid_trace.cli.get_version", return_value="1.2.3"):
        assert get_package_version() == "1.2.3"


def test_get_package_version_not_installed() -> None:
    """Test get_package_version when package is not installed."""
    from importlib.metadata import PackageNotFoundError

    with patch(
        "mermaid_trace.cli.get_version",
        side_effect=PackageNotFoundError("mermaid-trace"),
    ):
        assert get_package_version() == "0.0.0 (development)"
