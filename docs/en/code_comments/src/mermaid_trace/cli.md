# CLI Command Line Interface Module (cli.py)

`cli.py` is the entry point for the MermaidTrace command-line tools. It provides a local HTTP server to preview generated Mermaid sequence diagrams (.mmd files) in the browser with live-reload support.

## Core Features

- **Local Preview Server**: Launches a lightweight HTTP server to render Mermaid files as web pages.
- **Master Enhanced Mode**: Integrates FastAPI and SSE (Server-Sent Events) for an advanced preview interface with file browsing, pan/zoom, and instant updates.
- **Live Preview & Auto-Reload**: Uses browser-side polling (Basic mode) or SSE (Master mode) to refresh the page automatically when file changes are detected.
- **File Monitoring**: Integrates the `watchdog` library (optional) for efficient filesystem event monitoring.
- **Embedded Rendering Engine**: Uses the Mermaid.js CDN to render diagrams on the client side, eliminating the need for complex local graphics libraries.

## Key Technical Design

### 1. HTML Template & Mermaid.js Integration

The module contains an `HTML_TEMPLATE` string that includes:
- **Mermaid.js Loading**: Imports the library from a CDN.
- **Auto-Reload Logic**: JavaScript `setInterval` calls the `/_status` endpoint every second to compare the file's modification time (mtime).
- **Error Tolerance**: If file reading fails (e.g., file busy, permission denied, or deleted), the backend injects `mtime = "0"` and generates a Mermaid diagram containing the error message. This ensures the frontend remains stable and provides immediate feedback.

### 2. Custom Request Handler Factory (`_create_handler`)

A factory pattern is used to pass dynamic parameters (like filename and path) to the `socketserver`.

```python
def _create_handler(filename: str, path: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                # Render HTML template and inject content
                ...
            elif self.path == "/_status":
                # Return the file's latest modification time (mtime)
                ...
    return Handler
```

### 3. Hybrid Monitoring Mode

- **Watchdog (Server-side)**: If `watchdog` is installed, file change logs are printed to the console in real-time.
- **Polling (Client-side)**: The browser polls the `/_status` endpoint via Ajax. This is the core mechanism for auto-reload, working even without `watchdog`.

## Source Analysis

```python
import argparse
import http.server
import socketserver
from pathlib import Path

# Try to import watchdog for efficient monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

def serve(filename: str, port: int = 8000, master: bool = False) -> None:
    """
    Starts the local server.
    1. If master mode is enabled, calls server.run_server.
    2. Validates the file path.
    3. Sets up Watchdog monitoring (optional).
    4. Creates the HTTP handler.
    5. Automatically opens the browser.
    6. Enters the service loop.
    """
    if master:
        # Try to start the enhanced server
        try:
            from .server import run_server, HAS_SERVER_DEPS
            if HAS_SERVER_DEPS:
                run_server(target_dir, port)
                return
        except ImportError:
            pass

    path = Path(filename)
    # ... basic server setup ...

def main() -> None:
    """
    CLI Command Parsing.
    Uses argparse to define the 'serve' command and its arguments.
    """
    parser = argparse.ArgumentParser(description="MermaidTrace CLI - Preview Mermaid diagrams in browser")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Define the serve command
    serve_parser = subparsers.add_parser("serve", help="Start the live preview server")
    serve_parser.add_argument("file", help="Path to the .mmd file to preview")
    serve_parser.add_argument("--port", type=int, default=8000, help="Server port")
    serve_parser.add_argument("--master", action="store_true", help="Use enhanced preview (requires FastAPI)")

    args = parser.parse_args()
    if args.command == "serve":
        serve(args.file, args.port, args.master)
```

## Usage Examples

Run in the terminal:
```bash
# Basic preview
mermaid-trace serve trace.mmd --port 8080

# Master preview (directory browsing, pan/zoom)
mermaid-trace serve . --master
```
