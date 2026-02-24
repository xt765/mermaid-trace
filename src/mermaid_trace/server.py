"""
MermaidTrace Enhanced Web Server.

This module provides a robust, real-time preview server based on FastAPI and Server-Sent Events (SSE).
It monitors .mmd files for changes and instantly pushes updates to the browser for rendering.
"""

import asyncio
import os
import json
from pathlib import Path
from typing import AsyncGenerator, Set, Any

# Attempt to import server-related dependencies (FastAPI, Uvicorn).
# The try-except block ensures mermaid-trace can still be imported even if the
# [server] extra dependencies are not installed (though server features won't work).
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse
    import uvicorn

    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

    # Mock dependencies to allow module import without installation.
    # This is a graceful degradation strategy to prevent the entire library
    # from crashing due to missing optional dependencies.
    class MockException(Exception):
        pass

    class Mock:
        pass

    class MockApp:
        def get(self, *args: Any, **kwargs: Any) -> Any:
            return lambda f: f

    # Create fake FastAPI class and objects to prevent NameError
    def FastAPI(**kw: Any) -> MockApp:  # type: ignore
        return MockApp()

    Request = Mock  # type: ignore
    HTTPException = MockException  # type: ignore
    HTMLResponse = Mock  # type: ignore
    StreamingResponse = Mock  # type: ignore

# Attempt to import file monitoring dependencies (Watchdog).
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# Initialize the FastAPI application
app = FastAPI(title="MermaidTrace Preview Server")


# Global state class for managing SSE (Server-Sent Events) connections
class ConnectionManager:
    """
    Connection Manager: Handles client subscriptions and message broadcasting.

    Uses asyncio.Queue to store pending messages for each connected client,
    enabling asynchronous communication.
    """

    def __init__(self) -> None:
        # Set of queues for all active connections
        self.active_connections: Set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """
        Client Subscription: Creates a new message queue and adds it to the active list.

        Returns:
            asyncio.Queue: The queue used for receiving messages for this client.
        """
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.active_connections.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """
        Unsubscribe: Removes the specified queue from the active list.
        Typically called when a client disconnects.
        """
        self.active_connections.remove(queue)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """
        Broadcast Message: Pushes a message to all active client queues.

        Args:
            data: The dictionary containing data to send.
        """
        for queue in self.active_connections:
            await queue.put(data)


# Global instance of the connection manager
manager = ConnectionManager()

# Enhanced UI HTML Template
# Contains:
# 1. Mermaid.js: For diagram rendering
# 2. svg-pan-zoom: For pan and zoom interactions
# 3. Tailwind CSS: For UI styling
# 4. Custom JavaScript: Handles SSE events, file loading, and rendering logic
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Master Preview</title>
    <!-- External Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; }
        .mermaid { background: white; }
        /* Diagram Container: Grid background and layout */
        #diagram-container { 
            height: calc(100vh - 10rem); 
            overflow: hidden; 
            position: relative;
            background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex;
            flex-direction: column;
        }
        /* SVG Wrapper: Handles mouse interactions */
        #svg-wrapper { 
            flex: 1;
            width: 100%; 
            height: 100%; 
            cursor: grab; 
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #svg-wrapper:active { cursor: grabbing; }
        .sidebar-item:hover { background-color: #e2e8f0; }
        .sidebar-item.active { background-color: #3b82f6; color: white; }
        
        /* Ensure mermaid generated SVG is not constrained, allowing free zoom */
        #mermaid-graph {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #mermaid-graph svg {
            max-width: none !important;
            max-height: none !important;
        }
    </style>
</head>
<body class="flex flex-col h-screen">
    <!-- Top Navigation Bar -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center space-x-3">
            <div class="bg-blue-600 text-white p-2 rounded-lg">
                <!-- Logo Icon -->
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
            </div>
            <h1 class="text-xl font-bold text-gray-800">MermaidTrace <span class="text-blue-600">Master</span></h1>
        </div>
        <!-- Toolbar Buttons -->
        <div class="flex items-center space-x-4">
            <span id="status-badge" class="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Live Connected</span>
            <button onclick="resetZoom()" class="text-gray-600 hover:text-blue-600 transition" title="Reset Zoom">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
            </button>
            <button onclick="downloadSVG()" class="text-gray-600 hover:text-blue-600 transition" title="Download SVG">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            </button>
        </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
        <!-- Sidebar: File List -->
        <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto hidden md:block">
            <div class="p-4 border-b border-gray-100">
                <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Trace Files</h2>
            </div>
            <nav id="file-list" class="p-2 space-y-1">
                <!-- File list items will be injected via JS -->
            </nav>
        </aside>

        <!-- Main Content Area: Diagram Display -->
        <main class="flex-1 flex flex-col p-6 overflow-hidden">
            <div class="mb-4 flex justify-between items-end">
                <div>
                    <h2 id="current-filename" class="text-2xl font-bold text-gray-900">Select a file</h2>
                    <p id="last-updated" class="text-sm text-gray-500 mt-1">Ready to visualize</p>
                </div>
            </div>

            <div id="diagram-container" class="flex-1 bg-white rounded-xl shadow-inner border border-gray-200 overflow-hidden">
                <div id="svg-wrapper">
                    <div class="mermaid" id="mermaid-graph">
                        sequenceDiagram
                        Note over Server, Client: Waiting for trace data...
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let panZoomInstance = null;
        let currentFile = null;

        // Initialize Mermaid Library
        function initMermaid() {
            if (typeof mermaid === 'undefined') {
                console.log("Waiting for mermaid...");
                setTimeout(initMermaid, 100);
                return;
            }
            
            mermaid.initialize({ 
                startOnLoad: false, 
                theme: 'default',
                securityLevel: 'loose', // Allow HTML tags
                useMaxWidth: false,
                sequence: { 
                    showSequenceNumbers: true,
                    useMaxWidth: false,
                    bottomMarginAdjustment: 1
                }
            });
            
            // Initialize file list
            updateFileList();
        }

        // Load content of a specific file
        async function loadFile(filename) {
            if (!filename) return;
            currentFile = filename;
            
            // Update sidebar active state
            document.querySelectorAll('.sidebar-item').forEach(el => {
                if (el.dataset.filename === filename) el.classList.add('active');
                else el.classList.remove('active');
            });

            try {
                // Fetch file content from backend API
                const response = await fetch(`/api/file?name=${encodeURIComponent(filename)}`);
                const data = await response.json();
                
                document.getElementById('current-filename').textContent = filename;
                renderDiagram(data.content);
                updateTimestamp();
            } catch (err) {
                console.error("Failed to load file:", err);
            }
        }

        // Render Mermaid Diagram
        async function renderDiagram(content) {
            const graphDiv = document.getElementById('mermaid-graph');
            graphDiv.removeAttribute('data-processed');
            // Clear old content before rendering new
            graphDiv.innerHTML = content;
            
            try {
                // Generate SVG using mermaid API
                const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), content);
                graphDiv.innerHTML = svg;
                // Setup Pan and Zoom
                setupPanZoom();
            } catch (err) {
                console.error("Mermaid render error:", err);
            }
        }

        // Configure SVG Pan and Zoom interactions
        function setupPanZoom() {
            if (panZoomInstance) {
                panZoomInstance.destroy();
                panZoomInstance = null;
            }
            const svg = document.querySelector('#mermaid-graph svg');
            if (svg) {
                // Ensure SVG fills the container
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.maxWidth = 'none';
                svg.style.maxHeight = 'none';
                
                // Remove explicit width/height that might conflict with 'fit'
                svg.removeAttribute('width');
                svg.removeAttribute('height');
                
                // Initialize svg-pan-zoom
                panZoomInstance = svgPanZoom(svg, {
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: true,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 20,
                    zoomScaleSensitivity: 0.2
                });

                // Auto-fit on window resize
                window.addEventListener('resize', () => {
                    if (panZoomInstance) {
                        panZoomInstance.resize();
                        panZoomInstance.fit();
                        panZoomInstance.center();
                    }
                });
            }
        }

        // Reset Zoom View
        function resetZoom() {
            if (panZoomInstance) {
                panZoomInstance.fit();
                panZoomInstance.center();
            }
        }

        // Update Last Updated Timestamp
        function updateTimestamp() {
            const now = new Date();
            document.getElementById('last-updated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }

        // Update File List
        async function updateFileList() {
            const response = await fetch('/api/files');
            const files = await response.json();
            const list = document.getElementById('file-list');
            list.innerHTML = '';
            
            files.forEach(f => {
                const item = document.createElement('a');
                item.href = "#";
                item.className = `sidebar-item block px-3 py-2 text-sm font-medium rounded-md transition ${f === currentFile ? 'active' : 'text-gray-700'}`;
                item.dataset.filename = f;
                item.textContent = f;
                item.onclick = (e) => {
                    e.preventDefault();
                    loadFile(f);
                };
                list.appendChild(item);
            });

            // Default to first file if none selected
            if (!currentFile && files.length > 0) {
                loadFile(files[0]);
            }
        }

        // Establish SSE Connection for Real-time Updates
        const eventSource = new EventSource("/events");
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "update" && data.filename === currentFile) {
                console.log("File update received:", data.filename);
                loadFile(data.filename);
            } else if (data.type === "refresh_list") {
                updateFileList();
            }
        };

        eventSource.onerror = () => {
            document.getElementById('status-badge').className = "px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800";
            document.getElementById('status-badge').textContent = "Connection Lost";
        };
        
        // Start Initialization
        initMermaid();

        // Download Current Diagram as SVG
        function downloadSVG() {
            const svg = document.querySelector('#diagram-container svg');
            if (!svg) return;
            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svg);
            // Add namespaces to ensure valid SVG
            if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }
            if(!source.match(/^<svg[^>]+xmlns\\:xlink="http\\:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)){
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }
            source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
            const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
            const link = document.createElement("a");
            link.href = url;
            link.download = `${currentFile || 'diagram'}.svg`;
            link.click();
        }
    </script>
</body>
</html>
"""

# Global variable: Directory or file path to monitor
# Defaults to current directory
watch_dir: Path = Path(".")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    """
    Home page route.

    Returns:
        str: Rendered HTML page content.
    """
    # Note: If watch_dir is a file, the frontend logic handles the display.
    # The actual path resolution happens in run_server.
    return HTML_TEMPLATE


@app.get("/api/files")
async def list_files() -> list[str]:
    """
    API to retrieve the list of available files.

    Returns:
        list[str]: List of .mmd filenames.
    """
    # Single file mode: return only that file
    if os.path.isfile(str(watch_dir)):
        return [os.path.basename(str(watch_dir))]

    # Directory mode: return all .mmd files in the directory
    if os.path.isdir(str(watch_dir)):
        files = sorted([f.name for f in Path(watch_dir).glob("*.mmd")])
        return files

    return []


@app.get("/api/file")
async def get_file_content(name: str) -> dict[str, str]:
    """
    API to retrieve the content of a specific file.

    Args:
        name: The requested filename.

    Returns:
        dict: A dictionary containing the file content {"content": "..."}

    Raises:
        HTTPException: If the filename is invalid or file not found.
    """
    # Security check: Prevent Directory Traversal attacks
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=403, detail="Invalid filename")

    if os.path.isfile(str(watch_dir)):
        # Single file mode: ensure request matches the target file
        target_file = Path(str(watch_dir))
        if target_file.name != name:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        # Directory mode: construct full path
        target_file = Path(watch_dir) / name

    if not target_file.exists() or not str(target_file).endswith(".mmd"):
        raise HTTPException(status_code=404, detail="File not found")

    return {"content": target_file.read_text(encoding="utf-8")}


@app.get("/events")
async def sse_endpoint(request: Request) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint.
    Used to push real-time file update notifications to the frontend.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        # Subscribe to updates
        queue = await manager.subscribe()
        try:
            while True:
                # Check for client disconnection
                if await request.is_disconnected():
                    break
                # Wait for new messages in the queue
                data = await queue.get()
                # Yield data in SSE format
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            # Cleanup: Unsubscribe on exit
            manager.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def run_server(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    Start the FastAPI server to preview Mermaid diagrams.

    Args:
        target: Path to the file or directory to monitor.
        port: Port number to bind the server to.
        open_browser: Whether to automatically open the default web browser.
    """
    global watch_dir
    target_path = Path(target).resolve()

    if not target_path.exists():
        print(f"Error: Target '{target}' not found.")
        return

    # Set global monitor path
    # Logic:
    # If target is a file, watch_dir is that file (API handles single-file mode).
    # If target is a directory, watch_dir is that directory.
    watch_dir = target_path

    # Check if server dependencies are installed
    if not HAS_SERVER_DEPS:
        print("Error: FastAPI and Uvicorn are required for the preview server.")
        print("Please install them with: pip install mermaid-trace[server]")
        print("Or manually: pip install fastapi uvicorn")
        return

    # Start Watchdog file monitoring
    if HAS_WATCHDOG:
        # Determine Watch Scope
        if target_path.is_file():
            # Watchdog monitors directories, so for a single file, watch its parent
            watch_scope = str(target_path.parent)
            is_single_file = True
        else:
            watch_scope = str(target_path)
            is_single_file = False

        class Handler(FileSystemEventHandler):
            """File System Event Handler"""

            def on_modified(self, event: Any) -> None:
                if event.is_directory:
                    return

                filename = os.path.basename(event.src_path)

                # Filter logic: Only care about target file(s)
                if is_single_file:
                    # Ensure the modified absolute path matches target
                    if os.path.abspath(event.src_path) != str(target_path):
                        return
                elif not filename.endswith(".mmd"):
                    # Directory mode: only care about .mmd files
                    return

                # Broadcast file update event
                # Note: This runs in a separate thread managed by Watchdog.
                # 'asyncio.run' creates a NEW event loop for this call.
                # Ideally, we should thread-safe communicate with the main loop,
                # but for simple broadcasting to independent queues, this may work
                # if the queues are not loop-bound or if we accept the risk.
                # A more robust solution would use `call_soon_threadsafe`.
                try:
                    asyncio.run(
                        manager.broadcast({"type": "update", "filename": filename})
                    )
                except Exception as e:
                    print(f"Error broadcasting update: {e}")

            def on_created(self, event: Any) -> None:
                # Handle new file creation
                if not event.is_directory and event.src_path.endswith(".mmd"):
                    if not is_single_file:  # Refresh list only in directory mode
                        try:
                            asyncio.run(manager.broadcast({"type": "refresh_list"}))
                        except Exception as e:
                            print(f"Error broadcasting refresh: {e}")

        # Configure and start observer
        observer = Observer()
        observer.schedule(Handler(), watch_scope, recursive=False)
        observer.start()
        print(f"[*] Watching: {target_path}")

    # Auto-open browser
    if open_browser:
        import webbrowser

        print(f"[*] Opening browser at http://localhost:{port}")
        webbrowser.open(f"http://localhost:{port}")

    print(f"[*] Starting Server at http://localhost:{port}")
    # Start Uvicorn Server
    # host="0.0.0.0" allows external access
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
