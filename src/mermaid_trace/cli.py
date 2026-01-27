"""
Command Line Interface (CLI) Module for MermaidTrace.

This module serves as the entry point for the MermaidTrace command-line tools.
It provides functionality to:
1.  **Serve** Mermaid diagram files (.mmd) via a local HTTP server.
2.  **Preview** diagrams in a web browser with live-reload capabilities.
3.  **Monitor** file changes using polling or filesystem events (via `watchdog`).

Key Components:
-   `serve`: The primary command function that sets up the HTTP server and file watcher.
-   `_create_handler`: A factory function that generates a custom request handler with access to the target file.
-   `HTML_TEMPLATE`: A self-contained HTML page that renders Mermaid diagrams using the Mermaid.js CDN.

Usage:
    Run this module directly or via the `mermaid-trace` command (if installed).
    Example: `python -m mermaid_trace.cli serve diagram.mmd --port 8080`
"""

import argparse
import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path
from typing import Type, Any

# Attempt to import `watchdog` for efficient file system monitoring.
# `watchdog` is an external library that allows the program to react to file events (like modifications) immediately.
# We handle the ImportError gracefully to allow the CLI to function (via polling) even if `watchdog` is not installed.
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    # If watchdog is missing, we fall back to a simpler polling mechanism in the browser
    HAS_WATCHDOG = False

# HTML Template for the diagram preview page.
# This string contains the full HTML structure served to the browser.
#
# It includes:
# 1.  **Mermaid.js CDN**: Loads the library required to render the diagrams client-side.
# 2.  **CSS Styling**: Basic styles for layout, readability, and the "Refresh" button.
# 3.  **JavaScript Logic**:
#     -   Initializes Mermaid.js.
#     -   Implements a polling mechanism (`checkUpdate`) that hits the `/_status` endpoint.
#     -   Reloads the page automatically if the server reports a newer file modification time.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Flow Preview</title>
    <!-- Load Mermaid.js from CDN (Content Delivery Network) -->
    <!-- This library parses the text-based diagram definition and renders it as an SVG -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        /* Basic styling for readability and layout */
        body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
        
        /* Container for the diagram to give it a "card" look */
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        
        h1 {{ color: #333; }}
        
        /* Allow horizontal scrolling for wide diagrams that might overflow the screen */
        #diagram {{ overflow-x: auto; }}
        
        /* Floating refresh button for manual reloads */
        .refresh-btn {{ 
            position: fixed; bottom: 20px; right: 20px; 
            padding: 10px 20px; background: #007bff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
        }}
        .refresh-btn:hover {{ background: #0056b3; }}
        
        /* Status indicator to show the user that the live-reload is active */
        .status {{
            position: fixed; bottom: 20px; left: 20px;
            font-size: 12px; color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MermaidTrace Flow Preview: {filename}</h1>
        <!-- The Mermaid diagram content will be injected here by the Python server -->
        <!-- The 'mermaid' class triggers the Mermaid.js library to process this div -->
        <div class="mermaid" id="diagram">
            {content}
        </div>
    </div>
    
    <!-- Button to manually reload the page/diagram if auto-reload fails or is slow -->
    <button class="refresh-btn" onclick="location.reload()">Refresh Diagram</button>
    <div class="status" id="status">Monitoring for changes...</div>

    <script>
        // Initialize Mermaid with default settings.
        // 'startOnLoad: true' tells Mermaid to find all .mermaid classes and render them immediately.
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        
        // --- Live Reload Logic ---
        
        // We track the file's modification time (mtime) sent by the server during the initial page load.
        // This value is injected into the template by Python.
        const currentMtime = "{mtime}";
        
        /**
         * Checks the server for updates to the source file.
         * It fetches the '/_status' endpoint which returns the current file mtime.
         */
        function checkUpdate() {{
            fetch('/_status')
                .then(response => response.text())
                .then(mtime => {{
                    // If the server reports a different mtime than what we loaded with,
                    // it means the file has changed on disk. We reload the page to see the new diagram.
                    if (mtime && mtime !== currentMtime) {{
                        console.log("File changed, reloading...");
                        location.reload();
                    }}
                }})
                .catch(err => console.error("Error checking status:", err));
        }}
        
        // Poll every 1 second (1000 milliseconds).
        // This is a simple, robust alternative to WebSockets for local development tools.
        // It creates minimal load for a local server.
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

    We use a factory function (a function that returns a class) because `socketserver`
    expects a class type, not an instance. This allows us to "close over" the `filename`
    and `path` variables, making them available to the handler class without using globals.

    Args:
        filename (str): The display name of the file being served (used in the HTML title).
        path (Path): The `pathlib.Path` object pointing to the actual file on disk.

    Returns:
        Type[SimpleHTTPRequestHandler]: A custom class inheriting from `SimpleHTTPRequestHandler`.
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        """
        Custom HTTP Request Handler for serving Mermaid diagram previews.

        This handler overrides standard methods to provide two specific endpoints:
        1.  `/` (Root): Serves the HTML wrapper with the embedded diagram content.
        2.  `/_status`: Returns the file's current modification time (used for live reload).
        """

        def log_message(self, format: str, *args: Any) -> None:
            """
            Override `log_message` to suppress default HTTP request logging.

            By default, `SimpleHTTPRequestHandler` logs every request to stderr.
            We override this to keep the console output clean, showing only important application logs.
            """
            pass

        def do_GET(self) -> None:
            """
            Handle HTTP GET requests.

            Routes:
            -   **/**: Reads the target file, injects it into `HTML_TEMPLATE`, and serves the HTML.
            -   **/_status**: Checks the file's modification time and returns it as plain text.
            -   **Others**: Falls back to the default file serving behavior (though typically not used here).
            """
            if self.path == "/":
                # --- Root Endpoint: Serve the HTML Page ---
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                try:
                    # Read the current content of the Mermaid file from disk.
                    # We read it every time the page is requested to ensure we get the latest version.
                    content = path.read_text(encoding="utf-8")
                    # Get the modification time to embed in the page for the JS poller.
                    mtime = str(path.stat().st_mtime)
                except Exception as e:
                    # Error Handling:
                    # If reading fails (e.g., file locked, permissions, deleted),
                    # we render a special Mermaid diagram showing the error message.
                    # This provides immediate visual feedback in the browser.
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                    mtime = "0"

                # Inject variables into the HTML template
                html = HTML_TEMPLATE.format(
                    filename=filename, content=content, mtime=mtime
                )
                self.wfile.write(html.encode("utf-8"))

            elif self.path == "/_status":
                # --- Status Endpoint: Live Reload Polling ---
                # The client-side JavaScript calls this endpoint periodically.
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                try:
                    # Return the current modification time as the response body.
                    mtime = str(path.stat().st_mtime)
                except OSError:
                    # If the file cannot be accessed (e.g., deleted), return "0".
                    mtime = "0"
                self.wfile.write(mtime.encode("utf-8"))

            else:
                # --- Fallback: Default Behavior ---
                # Useful if the HTML template referenced other static assets (images, css files),
                # though currently everything is embedded.
                super().do_GET()

    return Handler


def serve(filename: str, port: int = 8000) -> None:
    """
    Starts the local HTTP server and file watcher to preview a Mermaid diagram.

    This is the core logic for the `serve` command. It sets up the environment,
    opens the browser, and enters a blocking loop to serve requests.

    Workflow:
    1.  Validates the input file.
    2.  Sets up a `watchdog` observer (if installed) for console logging of changes.
    3.  Creates the custom HTTP handler using `_create_handler`.
    4.  Opens the user's default web browser to the server URL.
    5.  Starts a threaded TCP server to handle HTTP requests.

    Args:
        filename (str): The path to the .mmd file to serve.
        port (int): The port number to bind the server to (default: 8000).
    """
    # Create a Path object for robust file path handling
    path = Path(filename)

    # 1. Validation
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # 2. Watchdog Setup (Optional)
    # If `watchdog` is installed, we use it to print immediate feedback to the console when the file changes.
    # Note: The browser reload is driven by the JS polling the `/_status` endpoint, not by this observer.
    # This observer is primarily for developer feedback in the terminal.
    observer = None
    if HAS_WATCHDOG:

        class FileChangeHandler(FileSystemEventHandler):
            """Internal handler class for Watchdog events."""

            def on_modified(self, event: Any) -> None:
                """Triggered when a file is modified in the watched directory."""
                # We only care about modifications to the specific file we are serving.
                if not event.is_directory and os.path.abspath(event.src_path) == str(
                    path.resolve()
                ):
                    print(f"[Watchdog] File changed: {filename}")

        print("Initializing file watcher...")
        observer = Observer()
        # Watch the directory containing the file, but filter events in the handler
        observer.schedule(FileChangeHandler(), path=str(path.parent), recursive=False)
        observer.start()
    else:
        print(
            "Watchdog not installed. Falling back to polling mode (client-side only)."
        )

    # 3. Create Server Handler
    HandlerClass = _create_handler(filename, path)

    # 4. User Feedback
    print(f"Serving {filename} at http://localhost:{port}")
    print("Press Ctrl+C to stop.")

    # 5. Open Browser
    # We open the browser *before* the server loop blocks, but the request might fail if the server
    # isn't ready instantly. However, `socketserver` setup is usually fast enough.
    webbrowser.open(f"http://localhost:{port}")

    # 6. Start Server
    # We use `ThreadingTCPServer` so that multiple requests (e.g., polling + main page load)
    # can be handled concurrently. This prevents the polling loop from blocking the page load.
    with socketserver.ThreadingTCPServer(("", port), HandlerClass) as httpd:
        try:
            # Block and handle requests indefinitely
            httpd.serve_forever()
        except KeyboardInterrupt:
            # 7. Graceful Shutdown
            # Catch Ctrl+C to clean up resources properly
            print("\nStopping server...")
            if observer:
                observer.stop()
                observer.join()
            httpd.server_close()


def main() -> None:
    """
    Main entry point for the CLI application.

    Responsibilities:
    1.  **Argument Parsing**: Uses `argparse` to define commands and options.
    2.  **Command Dispatch**: Calls the appropriate function based on the user's command.
    """
    # Initialize the argument parser with a description of the tool
    parser = argparse.ArgumentParser(
        description="MermaidTrace CLI - Preview Mermaid diagrams in browser"
    )

    # Create sub-parsers to handle different commands (currently only 'serve')
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- 'serve' command ---
    # Defines the 'serve' command which takes a file path and an optional port
    serve_parser = subparsers.add_parser(
        "serve", help="Serve a Mermaid file in the browser with live reload"
    )
    serve_parser.add_argument("file", help="Path to the .mmd file to serve")
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )

    # Parse the arguments provided by the user
    args = parser.parse_args()

    # Dispatch logic
    if args.command == "serve":
        # Invoke the serve function with parsed arguments
        serve(args.file, args.port)


if __name__ == "__main__":
    # Standard boilerplate to run the main function when the script is executed directly
    main()
