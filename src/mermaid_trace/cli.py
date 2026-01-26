"""
Command Line Interface Module

This module provides command-line functionality for MermaidTrace, primarily for
previewing generated Mermaid diagrams in a web browser with live reload capabilities.
"""

import argparse
import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path
from typing import Type, Any

try:
    # Watchdog is an optional dependency for efficient file monitoring
    # If installed, it enables instant file change detection
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    # Fallback when watchdog is not installed (minimal install case)
    HAS_WATCHDOG = False

# HTML Template for the diagram preview page
# Provides a self-contained environment to render Mermaid diagrams with:
# 1. Mermaid.js library from CDN for diagram rendering
# 2. Basic CSS styling for readability and layout
# 3. JavaScript for auto-refreshing when the source file changes
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Flow Preview</title>
    <!-- Load Mermaid.js from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        /* Basic styling for readability and layout */
        body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        #diagram {{ overflow-x: auto; }} /* Allow horizontal scrolling for wide diagrams */
        .refresh-btn {{ 
            position: fixed; bottom: 20px; right: 20px; 
            padding: 10px 20px; background: #007bff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
        }}
        .refresh-btn:hover {{ background: #0056b3; }}
        .status {{
            position: fixed; bottom: 20px; left: 20px;
            font-size: 12px; color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MermaidTrace Flow Preview: {filename}</h1>
        <!-- The Mermaid diagram content will be injected here -->
        <div class="mermaid" id="diagram">
            {content}
        </div>
    </div>
    <!-- Button to manually reload the page/diagram -->
    <button class="refresh-btn" onclick="location.reload()">Refresh Diagram</button>
    <div class="status" id="status">Monitoring for changes...</div>

    <script>
        // Initialize Mermaid with default settings
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        
        // Live Reload Logic
        // We track the file's modification time (mtime) sent by the server.
        const currentMtime = "{mtime}";
        
        function checkUpdate() {{
            // Poll the /_status endpoint to check if the file has changed on disk
            fetch('/_status')
                .then(response => response.text())
                .then(mtime => {{
                    // If the server reports a different mtime, reload the page
                    if (mtime && mtime !== currentMtime) {{
                        console.log("File changed, reloading...");
                        location.reload();
                    }}
                }})
                .catch(err => console.error("Error checking status:", err));
        }}
        
        // Poll every 1 second
        // This is a simple alternative to WebSockets for local dev tools
        setInterval(checkUpdate, 1000);
    </script>
</body>
</html>
"""


def _create_handler(
    filename: str, path: Path
) -> Type[http.server.SimpleHTTPRequestHandler]:
    """
    Factory function to create a custom HTTP request handler class.

    This uses a closure to inject `filename` and `path` into the handler's scope,
    allowing the `do_GET` method to access them without global variables.

    Args:
        filename (str): Display name of the file being served
        path (Path): Path object pointing to the file on disk

    Returns:
        Type[SimpleHTTPRequestHandler]: A custom request handler class
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        """
        Custom HTTP Request Handler for serving Mermaid diagram previews.

        This handler intercepts GET requests to:
        - Serve the HTML wrapper with embedded diagram content at the root path ('/')
        - Provide file modification time for live reload at '/_status'
        - Fall back to default behavior for other paths
        """

        def log_message(self, format: str, *args: Any) -> None:
            """
            Suppress default request logging to keep the console clean.

            Only application logs are shown, not every HTTP request.
            """
            pass

        def do_GET(self) -> None:
            """
            Handle GET requests for different paths.

            Routes:
            - '/'          : Serves HTML wrapper with embedded Mermaid content
            - '/_status'   : Returns current file modification time for live reload
            - other paths  : Falls back to default SimpleHTTPRequestHandler behavior
            """
            if self.path == "/":
                # Serve the main HTML page with embedded diagram
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                try:
                    # Read current content of the Mermaid file
                    content = path.read_text(encoding="utf-8")
                    mtime = str(path.stat().st_mtime)
                except Exception as e:
                    # Fallback if reading fails (e.g., file locked, permission error)
                    # Display error directly in the diagram area
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                    mtime = "0"

                # Inject content into the HTML template
                html = HTML_TEMPLATE.format(
                    filename=filename, content=content, mtime=mtime
                )
                self.wfile.write(html.encode("utf-8"))

            elif self.path == "/_status":
                # API endpoint for client-side polling
                # Returns current file modification time as plain text
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                try:
                    mtime = str(path.stat().st_mtime)
                except OSError:
                    # Fallback if file can't be accessed
                    mtime = "0"
                self.wfile.write(mtime.encode("utf-8"))

            else:
                # Serve other static files if needed, or return 404
                super().do_GET()

    return Handler


def serve(filename: str, port: int = 8000) -> None:
    """
    Starts a local HTTP server to preview Mermaid diagrams in a web browser.

    This function blocks the main thread while running a TCP server. It automatically
    opens the default web browser to the preview URL and supports live reload when
    the source .mmd file changes.

    Features:
    - Serves .mmd files wrapped in an HTML viewer with Mermaid.js
    - Live reload functionality using Watchdog (if available) or client-side polling
    - Graceful shutdown handling on Ctrl+C
    - Automatic browser opening

    Args:
        filename (str): Path to the .mmd file to serve
        port (int, optional): Port to bind the server to. Defaults to 8000.
    """
    # Resolve the file path
    path = Path(filename)
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # Setup Watchdog file watcher if available
    # Watchdog provides immediate file change notifications in the terminal
    # The actual browser reload is handled by client-side polling
    observer = None
    if HAS_WATCHDOG:

        class FileChangeHandler(FileSystemEventHandler):
            """Watchdog event handler for detecting changes to the served file"""

            def on_modified(self, event: Any) -> None:
                """Called when a file is modified"""
                # Filter only for modifications to our specific file
                if not event.is_directory and os.path.abspath(event.src_path) == str(
                    path.resolve()
                ):
                    print(f"[Watchdog] File changed: {filename}")

        print("Initializing file watcher...")
        observer = Observer()
        observer.schedule(FileChangeHandler(), path=str(path.parent), recursive=False)
        observer.start()
    else:
        print(
            "Watchdog not installed. Falling back to polling mode (client-side only)."
        )

    # Create the custom HTTP handler
    HandlerClass = _create_handler(filename, path)

    # Print server information
    print(f"Serving {filename} at http://localhost:{port}")
    print("Press Ctrl+C to stop.")

    # Automatically open the default web browser to the preview URL
    webbrowser.open(f"http://localhost:{port}")

    # Start the TCP server
    # Using ThreadingTCPServer to handle multiple requests concurrently
    # This ensures browser polling doesn't block the initial page load
    with socketserver.ThreadingTCPServer(("", port), HandlerClass) as httpd:
        try:
            # Serve forever until interrupted
            httpd.serve_forever()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nStopping server...")
            # Stop the watchdog observer if it was started
            if observer:
                observer.stop()
                observer.join()
            # Close the server
            httpd.server_close()


def main() -> None:
    """
    Entry point for the CLI application.

    Parses command-line arguments and dispatches to the appropriate command handler.
    Currently supports only the 'serve' command for previewing Mermaid diagrams.
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="MermaidTrace CLI - Preview Mermaid diagrams in browser"
    )

    # Add subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # Define 'serve' command for previewing diagrams
    serve_parser = subparsers.add_parser(
        "serve", help="Serve a Mermaid file in the browser with live reload"
    )
    serve_parser.add_argument("file", help="Path to the .mmd file to serve")
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )

    # Parse arguments and execute command
    args = parser.parse_args()

    if args.command == "serve":
        # Execute the serve command
        serve(args.file, args.port)


if __name__ == "__main__":
    # Run the main function when script is executed directly
    main()
