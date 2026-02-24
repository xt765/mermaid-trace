# CLI Command Line Interface Module (cli.py)

`cli.py` is the entry point for the MermaidTrace command-line tools. In version v0.7.0, it has been completely refactored to act as a lightweight dispatcher, delegating all Web server logic to the more robust `server.py` module.

## Core Features

- **Unified Entry Point**: Provides the `mermaid-trace serve` command, with no need to distinguish between modes.
- **Smart Dependency Check**: Checks for optional dependencies like `fastapi` and `uvicorn` before starting the server, providing friendly installation instructions if missing.
- **Argument Parsing**: Uses `argparse` to handle command-line arguments, supporting file path and port specification.
- **Backward Compatibility**: Retains the `--master` argument (though no longer needed) to maintain compatibility with older scripts.

## Key Technical Design

### 1. Lazy Import

To keep the CLI tool's startup lightweight, the `server` module (containing heavy FastAPI dependencies) is only imported when the user actually executes the `serve` command.

```python
def serve(...):
    try:
        from .server import run_server
        ...
```

### 2. Graceful Degradation & Error Messages

If a user installs only the core library (`pip install mermaid-trace`) without server dependencies, the CLI catches the `ImportError` or checks the `HAS_SERVER_DEPS` flag and prints clear installation instructions:

```text
Error: The preview server requires additional dependencies.
Please install them with:
    pip install mermaid-trace[server]
```

## Source Analysis

```python
"""
Command Line Interface (CLI) Module - MermaidTrace.

This module serves as the entry point for the MermaidTrace command-line tool.
It facilitates the preview of Mermaid diagram files (.mmd) via a local HTTP server,
leveraging the robust FastAPI-based implementation in `server.py`.

Usage:
    Run this module directly or via the `mermaid-trace` command if installed.
    Example: `mermaid-trace serve diagram.mmd --port 8080`
"""

import argparse  # Standard library for parsing command-line arguments
import sys  # Used for system-specific parameters and functions (e.g., exit)


def serve(target: str, port: int = 8000) -> None:
    """
    Starts a local HTTP server to preview Mermaid diagrams.

    This function delegates the actual server logic to `mermaid_trace.server.run_server`.
    It handles dependency checking and provides installation instructions if
    required packages (fastapi, uvicorn) are missing.

    Args:
        target (str): Path to the .mmd file or directory to serve.
        port (int): The port number to bind the server to (default: 8000).
    """
    try:
        # Attempt to import the run function and dependency flag from the server module.
        # Delayed import avoids loading heavy dependencies when server functionality is not needed.
        from .server import run_server, HAS_SERVER_DEPS

        # Check if server dependencies (fastapi, uvicorn, etc.) are installed
        if HAS_SERVER_DEPS:
            # Dependencies are present; launch the server.
            run_server(target, port)
        else:
            # Dependencies are missing; print error and installation instructions.
            # Note: While pip is suggested, modern Python workflows might use tools like uv.
            print("Error: The preview server requires additional dependencies.")
            print("Please install them with:")
            print("    pip install mermaid-trace[server]")
            print("Or manually:")
            print("    pip install fastapi uvicorn")
            sys.exit(1)  # Exit with a non-zero status code indicating error

    except ImportError:
        # Catch cases where importing the server module itself fails (e.g., corrupted files)
        print("Error: Could not import server module.")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the CLI application.

    Responsible for parsing command-line arguments and invoking the appropriate
    function based on the subcommand provided.
    """
    # Create the top-level argument parser
    parser = argparse.ArgumentParser(
        description="MermaidTrace CLI - Preview Mermaid diagrams in the browser"
    )

    # Create sub-parsers to handle different commands (e.g., 'serve')
    # dest="command" stores the chosen subcommand name in args.command
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- 'serve' Command Definition ---
    # Add 'serve' subcommand: starts the live preview server
    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve a Mermaid file or directory in the browser with live reload",
    )

    # Add 'path' positional argument: the file or folder to preview
    serve_parser.add_argument(
        "path", help="Path to the .mmd file or directory to serve"
    )

    # Add '--port' optional argument: server listening port
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )

    # Add '--master' deprecated argument
    # Kept for backward compatibility with older scripts, but ignored in code
    serve_parser.add_argument(
        "--master",
        action="store_true",
        help="Deprecated: Master mode is now the default.",
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Dispatch to the corresponding function based on the subcommand
    if args.command == "serve":
        # If 'serve' command is used, call the serve function
        serve(args.path, args.port)


if __name__ == "__main__":
    # Execute main function when script is run directly
    main()
```
