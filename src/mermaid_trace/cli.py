import argparse
import http.server
import socketserver
import webbrowser
import sys
from pathlib import Path

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Flow Preview</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        #diagram {{ overflow-x: auto; }}
        .refresh-btn {{ 
            position: fixed; bottom: 20px; right: 20px; 
            padding: 10px 20px; background: #007bff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
        }}
        .refresh-btn:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MermaidTrace Flow Preview: {filename}</h1>
        <div class="mermaid" id="diagram">
            {content}
        </div>
    </div>
    <button class="refresh-btn" onclick="location.reload()">Refresh Diagram</button>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>
"""

def serve(filename: str, port: int = 8000):
    path = Path(filename)
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception as e:
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                
                html = HTML_TEMPLATE.format(filename=filename, content=content)
                self.wfile.write(html.encode("utf-8"))
            else:
                # Serve static files if needed, or 404
                super().do_GET()

    print(f"Serving {filename} at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{port}")
    
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="MermaidTrace CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 'serve' command
    serve_parser = subparsers.add_parser("serve", help="Serve a Mermaid file in the browser")
    serve_parser.add_argument("file", help="Path to the .mmd file")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve(args.file, args.port)

if __name__ == "__main__":
    main()
