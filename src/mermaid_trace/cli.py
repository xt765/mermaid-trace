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
        str: Version string, e.g., "0.7.1"
    """
    try:
        return get_version("mermaid-trace")
    except PackageNotFoundError:
        return "0.0.0 (development)"


def serve(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    Start a local HTTP server to preview Mermaid diagrams.

    This function delegates the actual server logic to `mermaid_trace.server.run_server`.

    Args:
        target: Path to the .mmd file or directory to serve.
        port: The port number to bind the server to (default: 8000).
        open_browser: Whether to automatically open the browser (default: True).
    """
    try:
        from .server import run_server

        run_server(target, port, open_browser)

    except ImportError:
        print("Error: Could not import server module.")
        print("Please ensure mermaid-trace is installed correctly:")
        print("    pip install mermaid-trace")
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

    args = parser.parse_args()

    if args.command == "serve":
        serve(args.path, args.port, open_browser=not args.no_browser)
    elif args.command == "version":
        print(f"MermaidTrace version: {get_package_version()}")


if __name__ == "__main__":
    main()
