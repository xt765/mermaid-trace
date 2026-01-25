import argparse
import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path
from typing import Type, Any

try:
    from watchdog.observers import Observer  
    from watchdog.events import FileSystemEventHandler  
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# HTML Template for the preview page
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
        const currentMtime = "{mtime}";
        
        function checkUpdate() {{
            fetch('/_status')
                .then(response => response.text())
                .then(mtime => {{
                    if (mtime && mtime !== currentMtime) {{
                        console.log("File changed, reloading...");
                        location.reload();
                    }}
                }})
                .catch(err => console.error("Error checking status:", err));
        }}
        
        // Poll every 1 second
        setInterval(checkUpdate, 1000);
    </script>
</body>
</html>
"""

def _create_handler(filename: str, path: Path) -> Type[http.server.SimpleHTTPRequestHandler]:
    """Helper to create the request handler class with closure over filename/path."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        """
        Custom Request Handler to serve the generated HTML dynamically.
        """
        def log_message(self, format: str, *args: Any) -> None:
            # Suppress default logging to keep console clean
            pass

        def do_GET(self) -> None:
            """
            Handle GET requests.
            Serves the HTML wrapper for the root path ('/').
            """
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                try:
                    # Read the current content of the mermaid file
                    content = path.read_text(encoding="utf-8")
                    mtime = str(path.stat().st_mtime)
                except Exception as e:
                    # Fallback if reading fails (e.g., file locked)
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                    mtime = "0"
                
                # Inject content into the HTML template
                html = HTML_TEMPLATE.format(filename=filename, content=content, mtime=mtime)
                self.wfile.write(html.encode("utf-8"))
            
            elif self.path == "/_status":
                # API endpoint for client to check file status
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                try:
                    mtime = str(path.stat().st_mtime)
                except OSError:
                    mtime = "0"
                self.wfile.write(mtime.encode("utf-8"))
                
            else:
                # Serve static files if needed, or return 404
                super().do_GET()
    return Handler

def serve(filename: str, port: int = 8000) -> None:
    """
    Starts a local HTTP server to preview the Mermaid diagram.
    """
    path = Path(filename)
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # Setup Watchdog if available
    observer = None
    if HAS_WATCHDOG:
        class FileChangeHandler(FileSystemEventHandler):
            def on_modified(self, event: Any) -> None:
                if not event.is_directory and os.path.abspath(event.src_path) == str(path.resolve()):
                    print(f"[Watchdog] File changed: {filename}")

        print("Initializing file watcher...")
        observer = Observer()
        observer.schedule(FileChangeHandler(), path=str(path.parent), recursive=False)
        observer.start()
    else:
        print("Watchdog not installed. Falling back to polling mode (client-side only).")

    HandlerClass = _create_handler(filename, path)

    print(f"Serving {filename} at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    
    # Open browser automatically to the server URL
    webbrowser.open(f"http://localhost:{port}")
    
    # Start the TCP server
    with socketserver.ThreadingTCPServer(("", port), HandlerClass) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            if observer:
                observer.stop()
                observer.join()
            httpd.server_close()

def main() -> None:
    """
    Entry point for the CLI application.
    """
    parser = argparse.ArgumentParser(description="MermaidTrace CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 'serve' command definition
    serve_parser = subparsers.add_parser("serve", help="Serve a Mermaid file in the browser")
    serve_parser.add_argument("file", help="Path to the .mmd file")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve(args.file, args.port)

if __name__ == "__main__":
    main()
