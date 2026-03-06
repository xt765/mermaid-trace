# CLI Command Line Interface Module (cli.py)

`cli.py` is the entry point for the MermaidTrace command-line tools. In version v0.7.1, it has been completely refactored to act as a lightweight dispatcher, delegating all Web server logic to the more robust `server.py` module.

## Installation

Starting from v0.7.1, FastAPI and Uvicorn are now required dependencies. Install to use all features:

```bash
pip install mermaid-trace
```

After installation, all features are available, including:
- Code tracing and .mmd file generation
- Web preview server (fully offline capable)
- Live reload and interactive controls

## Core Features

- **Unified Entry Point**: Provides `mermaid-trace serve` command for diagram preview and `mermaid-trace version` for version information.
- **Argument Parsing**: Uses `argparse` to handle command-line arguments, supporting file path, port specification, and browser control.
- **Offline Support**: Web preview server uses local static resources, no network connection required.

## Available Commands

### `mermaid-trace serve`

Start a local HTTP server to preview Mermaid diagram files with live reload.

**Features:**
- Real-time Updates - Diagrams reload automatically when files change
- Multi-file Support - Browse all .mmd files in a directory
- Interactive Controls - Zoom, pan, and export diagrams as SVG
- Hot Reload - Server-Sent Events (SSE) for instant updates

**File Modes:**
- Single File: Provide a .mmd file path to preview that file
- Directory: Provide a directory path to browse all .mmd files

**Options:**
- `path`: Path to a .mmd file or directory containing .mmd files (required)
- `-p, --port`: Port number for the server (default: 8000)
- `--no-browser`: Do not automatically open the browser
- `--master`: Deprecated: Master mode is now the default

**Examples:**
```bash
mermaid-trace serve flow.mmd              # Preview a single diagram file
mermaid-trace serve ./diagrams            # Preview all .mmd files in directory
mermaid-trace serve flow.mmd --port 3000  # Use custom port
mermaid-trace serve flow.mmd --no-browser # Don't auto-open browser
```

### `mermaid-trace version`

Display the installed version of MermaidTrace.

**Example:**
```bash
mermaid-trace version
# Output: MermaidTrace version: 0.7.1
```

## Key Technical Design

### 1. Lazy Import

To keep the CLI tool's startup lightweight, the `server` module (containing heavy FastAPI dependencies) is only imported when the user actually executes the `serve` command.

```python
def serve(...):
    try:
        from .server import run_server
        ...
```

### 2. Error Handling

If the server module fails to import (e.g., corrupted installation), the CLI provides clear guidance:

```text
Error: Could not import server module.
Please ensure mermaid-trace is installed correctly:
    pip install mermaid-trace
```

### 3. Offline Support

Starting from v0.7.1, the web preview server uses local static resources instead of external CDN dependencies. This ensures the preview works offline without network connectivity.

## Source Analysis

```python
"""
Command Line Interface (CLI) Module - MermaidTrace.

This module provides the command-line interface for MermaidTrace,
enabling users to preview Mermaid diagram files through a local web server.
"""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version as get_version


def get_package_version() -> str:
    """
    Get the installed package version.

    Returns:
        str: Version string, e.g., "0.7.0"
    """
    try:
        return get_version("mermaid-trace")
    except PackageNotFoundError:
        return "0.0.0 (development)"


def serve(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    Start a local HTTP server to preview Mermaid diagrams.

    This function delegates the actual server logic to `mermaid_trace.server.run_server`.
    It handles dependency checking and provides installation instructions if
    required packages (fastapi, uvicorn) are missing.

    Args:
        target: Path to the .mmd file or directory to serve.
        port: The port number to bind the server to (default: 8000).
        open_browser: Whether to automatically open the browser (default: True).
    """
    try:
        from .server import run_server, HAS_SERVER_DEPS

        if HAS_SERVER_DEPS:
            run_server(target, port, open_browser)
        else:
            print("Error: The preview server requires additional dependencies.")
            print("\nPlease install them with one of the following commands:")
            print("    uv add mermaid-trace[server]")
            print("    # or")
            print("    uv add fastapi uvicorn watchdog")
            sys.exit(1)

    except ImportError:
        print("Error: Could not import server module.")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the CLI application.

    Parses command-line arguments and invokes the appropriate function
    based on the provided subcommand.
    """
    parser = argparse.ArgumentParser(
        prog="mermaid-trace",
        description=(
            "MermaidTrace - Visualize Python execution flow as Mermaid sequence diagrams.\n\n"
            "This tool helps you understand complex code execution by automatically\n"
            "tracing function calls and generating interactive sequence diagrams.\n\n"
            "Use 'mermaid-trace <command> --help' for detailed command information."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  mermaid-trace serve flow.mmd              # Preview a single diagram file\n"
            "  mermaid-trace serve ./diagrams            # Preview all .mmd files in directory\n"
            "  mermaid-trace serve flow.mmd --port 3000  # Use custom port\n"
            "  mermaid-trace serve flow.mmd --no-browser # Don't auto-open browser\n"
            "  mermaid-trace version                     # Show version information\n\n"
            "Documentation: https://github.com/xt765/mermaid-trace\n"
            "Bug Reports: https://github.com/xt765/mermaid-trace/issues"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="available commands",
        metavar="<command>",
    )

    # Version command
    subparsers.add_parser(
        "version",
        help="Display version information",
        description="Show the installed version of MermaidTrace.",
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start live preview server for Mermaid diagrams",
        description=(
            "Start a local HTTP server to preview Mermaid diagram files with live reload.\n\n"
            "Features:\n"
            "  • Real-time Updates - Diagrams reload automatically when files change\n"
            "  • Multi-file Support - Browse all .mmd files in a directory\n"
            "  • Interactive Controls - Zoom, pan, and export diagrams as SVG\n"
            "  • Hot Reload - Server-Sent Events (SSE) for instant updates\n\n"
            "File Modes:\n"
            "  - Single File: Provide a .mmd file path to preview that file\n"
            "  - Directory: Provide a directory path to browse all .mmd files"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    serve_parser.add_argument(
        "path",
        help="Path to a .mmd file or directory containing .mmd files",
    )

    serve_parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port number for the server (default: 8000)",
    )

    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser",
    )

    serve_parser.add_argument(
        "--master",
        action="store_true",
        help="Deprecated: Master mode is now the default.",
    )

    args = parser.parse_args()

    if args.command == "serve":
        serve(args.path, args.port, open_browser=not args.no_browser)
    elif args.command == "version":
        print(f"MermaidTrace version: {get_package_version()}")


if __name__ == "__main__":
    main()
```
