# Enhanced Web Server Module (server.py)

`server.py` is the advanced preview server for MermaidTrace. Built with FastAPI and Server-Sent Events (SSE), it provides a high-performance, low-latency live preview experience, ideal for frequent updates and managing multiple trace files.

## Core Features

- **Real-time Updates (SSE)**: Uses Server-Sent Events instead of traditional polling. Updates are pushed from the server to the browser instantly when file changes are detected.
- **File List Management**: Automatically scans for all `.mmd` files in the specified directory and provides a sidebar for quick switching.
- **Interactive UI**:
    - **Pan & Zoom**: Integrates the `svg-pan-zoom` library, allowing users to navigate large and complex diagrams with ease.
    - **Responsive Layout**: Built with Tailwind CSS, featuring a collapsible sidebar and adaptive containers.
    - **Export Functionality**: Supports exporting the currently displayed diagram as an SVG file.
- **Filesystem Monitoring**: Deep integration with `watchdog` to listen for file modification and creation events.

## Key Design Patterns

### 1. Connection Management (`ConnectionManager`)

To support multiple simultaneous browser previews, the module implements a simple Pub/Sub pattern.

```python
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        # Create an async queue for each new connection
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.active_connections.add(queue)
        return queue

    async def broadcast(self, data: dict[str, Any]) -> None:
        # Push messages to all active subscribers
        for queue in self.active_connections:
            await queue.put(data)
```

### 2. SSE Endpoint (`/events`)

The endpoint uses an async generator to stream JSON-encoded events to the client.

```python
@app.get("/events")
async def sse_endpoint(request: Request) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await manager.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            manager.unsubscribe(queue)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 3. Client-side Rendering

Instead of reloading the entire page, the frontend uses `mermaid.render` to asynchronously update the diagram content while maintaining the current zoom/pan state.

```javascript
async function renderDiagram(content) {
    const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), content);
    graphDiv.innerHTML = svg;
    setupPanZoom(); // Re-initialize the zoom plugin
}
```

## Source Analysis

### Dependency Checks
The module checks for `fastapi` and `uvicorn`. If missing, it provides helpful installation instructions and falls back to the basic preview mode.

### Server Startup (`run_server`)
1. **Path Resolution**: Converts the target directory into an absolute path.
2. **Monitoring**: Starts a `watchdog` thread to listen for file events.
3. **Web Service**: Runs the FastAPI application using `uvicorn`.

## Usage Scenarios

- **Master Mode**: Triggered by running `mermaid-trace serve . --master`.
- **Multiple File Preview**: Perfect for projects with multiple trace files that need quick switching.
- **Large Diagrams**: Essential for navigating complex diagrams that exceed standard screen sizes.
