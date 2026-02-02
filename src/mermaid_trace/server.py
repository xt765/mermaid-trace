"""
Enhanced Web Server for MermaidTrace.

This module provides a robust, real-time preview server using FastAPI and Server-Sent Events (SSE).
It monitors .mmd files and pushes updates to the browser instantly.
"""

import asyncio
import os
import json
from pathlib import Path
from typing import AsyncGenerator, Set, Any

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse
    import uvicorn

    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

app = FastAPI(title="MermaidTrace Preview Server")


# Global state to manage connected clients for SSE
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.active_connections.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.active_connections.remove(queue)

    async def broadcast(self, data: dict[str, Any]) -> None:
        for queue in self.active_connections:
            await queue.put(data)


manager = ConnectionManager()

# HTML Template with enhanced UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Master Preview</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; }
        .mermaid { background: white; }
        #diagram-container { 
            height: calc(100vh - 10rem); 
            overflow: hidden; 
            position: relative;
            background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex;
            flex-direction: column;
        }
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
        /* Ensure mermaid SVG doesn't have max-width constraints */
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
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center space-x-3">
            <div class="bg-blue-600 text-white p-2 rounded-lg">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
            </div>
            <h1 class="text-xl font-bold text-gray-800">MermaidTrace <span class="text-blue-600">Master</span></h1>
        </div>
        <div class="flex items-center space-x-4">
            <span id="status-badge" class="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Live Connected</span>
            <button onclick="resetZoom()" class="text-gray-600 hover:text-blue-600 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
            </button>
            <button onclick="downloadSVG()" class="text-gray-600 hover:text-blue-600 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            </button>
        </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
        <!-- Sidebar -->
        <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto hidden md:block">
            <div class="p-4 border-b border-gray-100">
                <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Trace Files</h2>
            </div>
            <nav id="file-list" class="p-2 space-y-1">
                <!-- File items will be injected here -->
            </nav>
        </aside>

        <!-- Main Content -->
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

        function initMermaid() {
            if (typeof mermaid === 'undefined') {
                console.log("Waiting for mermaid...");
                setTimeout(initMermaid, 100);
                return;
            }
            
            mermaid.initialize({ 
                startOnLoad: false, 
                theme: 'default',
                securityLevel: 'loose',
                useMaxWidth: false,
                sequence: { 
                    showSequenceNumbers: true,
                    useMaxWidth: false,
                    bottomMarginAdjustment: 1
                }
            });
            
            // Initialize
            updateFileList();
        }

        async function loadFile(filename) {
            if (!filename) return;
            currentFile = filename;
            
            // Update active state in sidebar
            document.querySelectorAll('.sidebar-item').forEach(el => {
                if (el.dataset.filename === filename) el.classList.add('active');
                else el.classList.remove('active');
            });

            try {
                const response = await fetch(`/api/file?name=${encodeURIComponent(filename)}`);
                const data = await response.json();
                
                document.getElementById('current-filename').textContent = filename;
                renderDiagram(data.content);
                updateTimestamp();
            } catch (err) {
                console.error("Failed to load file:", err);
            }
        }

        async function renderDiagram(content) {
            const graphDiv = document.getElementById('mermaid-graph');
            graphDiv.removeAttribute('data-processed');
            // Clean up previous SVG before rendering new one
            graphDiv.innerHTML = content;
            
            try {
                const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), content);
                graphDiv.innerHTML = svg;
                setupPanZoom();
            } catch (err) {
                console.error("Mermaid render error:", err);
            }
        }

        function setupPanZoom() {
            if (panZoomInstance) {
                panZoomInstance.destroy();
                panZoomInstance = null;
            }
            const svg = document.querySelector('#mermaid-graph svg');
            if (svg) {
                // Ensure SVG takes up all available space for the pan-zoom container
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.maxWidth = 'none';
                svg.style.maxHeight = 'none';
                
                // Clear explicit width/height attributes that might conflict with 'fit'
                svg.removeAttribute('width');
                svg.removeAttribute('height');
                
                panZoomInstance = svgPanZoom(svg, {
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: true,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 20,
                    zoomScaleSensitivity: 0.2
                });

                // Auto fit on window resize
                window.addEventListener('resize', () => {
                    if (panZoomInstance) {
                        panZoomInstance.resize();
                        panZoomInstance.fit();
                        panZoomInstance.center();
                    }
                });
            }
        }

        function resetZoom() {
            if (panZoomInstance) {
                panZoomInstance.fit();
                panZoomInstance.center();
            }
        }

        function updateTimestamp() {
            const now = new Date();
            document.getElementById('last-updated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }

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

            if (!currentFile && files.length > 0) {
                loadFile(files[0]);
            }
        }

        // SSE Connection for real-time updates
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

        function downloadSVG() {
            const svg = document.querySelector('#diagram-container svg');
            if (!svg) return;
            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svg);
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

# Global directory to watch
watch_dir: Path = Path(".")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    return HTML_TEMPLATE


@app.get("/api/files")
async def list_files() -> list[str]:
    files = sorted([f.name for f in watch_dir.glob("*.mmd")])
    return files


@app.get("/api/file")
async def get_file_content(name: str) -> dict[str, str]:
    file_path = watch_dir / name
    if not file_path.exists() or not str(file_path).endswith(".mmd"):
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": file_path.read_text(encoding="utf-8")}


@app.get("/events")
async def sse_endpoint(request: Request) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await manager.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {json.dumps(data)}\\n\\n"
        finally:
            manager.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def run_server(directory: str, port: int = 8000) -> None:
    global watch_dir
    watch_dir = Path(directory).resolve()

    if not HAS_SERVER_DEPS:
        print("Error: FastAPI, Uvicorn are required for the enhanced server.")
        print("Install them with: pip install fastapi uvicorn")
        return

    # Start Watchdog
    if HAS_WATCHDOG:

        class Handler(FileSystemEventHandler):
            def on_modified(self, event: Any) -> None:
                if not event.is_directory and event.src_path.endswith(".mmd"):
                    filename = os.path.basename(event.src_path)
                    asyncio.run(
                        manager.broadcast({"type": "update", "filename": filename})
                    )

            def on_created(self, event: Any) -> None:
                if not event.is_directory and event.src_path.endswith(".mmd"):
                    asyncio.run(manager.broadcast({"type": "refresh_list"}))

        observer = Observer()
        observer.schedule(Handler(), str(watch_dir), recursive=False)
        observer.start()
        print(f"[*] Watching directory: {watch_dir}")

    print(f"[*] Starting Master Preview Server at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
