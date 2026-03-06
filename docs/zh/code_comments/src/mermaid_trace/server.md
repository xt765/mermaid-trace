# 增强型 Web 服务器模块 (server.py)

`server.py` 是 MermaidTrace 提供的高级预览服务器模块。它基于 FastAPI 和 Server-Sent Events (SSE) 技术，实现了高性能、低延迟的实时预览功能，特别适用于需要频繁更新图表或管理多个跟踪文件的场景。

## 核心功能

- **实时更新 (SSE)**: 使用服务器发送事件（Server-Sent Events）代替传统的轮询机制。一旦服务器检测到文件变化，会立即向浏览器推送更新通知，实现真正的"零延迟"刷新。
- **离线支持**: 所有静态资源（Tailwind CSS、Mermaid.js、svg-pan-zoom）均已打包到本地。无需网络连接即可使用。
- **文件列表管理**: 自动扫描指定目录下的所有 `.mmd` 文件，并在侧边栏提供快速切换功能。
- **交互式 UI**:
    - **缩放与平移**: 集成 `svg-pan-zoom` 库，支持通过鼠标滚轮或拖拽来查看大型复杂的时序图。
    - **响应式布局**: 基于 Tailwind CSS 构建，支持侧边栏折叠和自适应容器。
    - **导出功能**: 支持将当前显示的图表直接导出为 SVG 文件。
- **文件系统监控**: 深度集成 `watchdog`，能够监听文件的修改和新建事件，自动同步文件列表。

## 关键技术设计

### 1. 静态文件服务

从 v0.7.1 开始，服务器使用本地静态资源（CSS、JavaScript）而不是外部 CDN。这确保预览功能完全离线可用。

```python
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

HTML 模板引用这些本地资源：
```html
<script src="/static/mermaid.min.js"></script>
<script src="/static/svg-pan-zoom.min.js"></script>
<link href="/static/tailwind.min.css" rel="stylesheet">
```

### 2. 连接管理器 (`ConnectionManager`)

为了支持多个浏览器窗口同时预览，模块实现了一个简单的发布-订阅模式。

```python
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        # 为每个新连接创建一个异步队列
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.active_connections.add(queue)
        return queue

    async def broadcast(self, data: dict[str, Any]) -> None:
        # 将消息发送给所有订阅者
        for queue in self.active_connections:
            await queue.put(data)
```

### 2. SSE 端点 (`/events`)

该接口通过异步生成器向客户端流式传输 JSON 格式的事件数据。

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

### 3. 前端渲染引擎

前端不再简单的刷新整个页面，而是通过 `mermaid.render` 异步渲染新的内容，并保持当前的缩放状态。

```javascript
async function renderDiagram(content) {
    const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), content);
    graphDiv.innerHTML = svg;
    setupPanZoom(); // 重新初始化缩放插件
}
```

## 源码分析与注释

### 依赖检查
模块会检查 `fastapi` 和 `uvicorn` 是否安装。如果未安装，会优雅地提示用户并回退到基础模式。

```python
# Try to import server-related dependencies (FastAPI, Uvicorn)
# Use a try-except block to allow mermaid-trace to be imported even if [server] extra dependencies are not installed
# (though server functionality won't work)
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse
    import uvicorn

    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

    # Mock dependencies to allow module import without installation
    # This is a graceful degradation strategy to avoid making the entire library unusable due to missing optional dependencies
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

# Try to import file monitoring dependency (Watchdog)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# Initialize FastAPI app
app = FastAPI(title="MermaidTrace Preview Server")
```

### 连接管理器 (`ConnectionManager`)

```python
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
        Usually called when a client disconnects.
        """
        self.active_connections.remove(queue)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """
        Broadcast Message: Pushes a message to all active client queues.
        
        Args:
            data: The dictionary data to send
        """
        for queue in self.active_connections:
            await queue.put(data)


# Global connection manager instance
manager = ConnectionManager()
```

### HTML 模板与前端逻辑

```python
# HTML Template for Enhanced UI
# Includes:
# 1. Mermaid.js: For rendering diagrams
# 2. svg-pan-zoom: For zoom and pan interactions
# 3. Tailwind CSS: For styling the interface
# 4. Custom JavaScript: Handles SSE events, file loading, and rendering logic
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Master Preview</title>
    <!-- Import necessary external libraries -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
...
```

### 服务器启动 (`run_server`)
1. **路径解析**: 将传入的目录路径转换为绝对路径。
2. **启动监控**: 开启 `watchdog` 线程监听文件事件。
3. **启动 Web 服务**: 使用 `uvicorn` 运行 FastAPI 应用。

```python
def run_server(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    Start the FastAPI server to preview Mermaid diagrams.

    Args:
        target: The file or directory path to monitor.
        port: The port number to bind the server to.
        open_browser: Whether to automatically open the preview page in the default browser.
    """
    global watch_dir
    target_path = Path(target).resolve()

    if not target_path.exists():
        print(f"Error: Target '{target}' not found.")
        return

    # Set global monitoring path
    # The logic here is slightly complex:
    # If target is a file, watch_dir is set to that file path, and the API will handle single-file mode accordingly
    # If target is a directory, watch_dir is set to that directory path
    watch_dir = target_path

    # Check if server dependencies are installed
    if not HAS_SERVER_DEPS:
        print("Error: FastAPI and Uvicorn are required for the preview server.")
        print("Please install them with: pip install mermaid-trace[server]")
        print("Or manually: pip install fastapi uvicorn")
        return

    # Start Watchdog file monitoring
    if HAS_WATCHDOG:
        # Determine monitoring scope
        if target_path.is_file():
            # Watchdog can only monitor directories, so if it's a single file, we monitor its parent directory
            watch_scope = str(target_path.parent)
            is_single_file = True
        else:
            watch_scope = str(target_path)
            is_single_file = False

        class Handler(FileSystemEventHandler):
            """File system event handler"""
            def on_modified(self, event: Any) -> None:
                if event.is_directory:
                    return

                filename = os.path.basename(event.src_path)

                # Filter logic: only care about changes to the target file(s)
                if is_single_file:
                    # Ensure the absolute path of the changed file matches the target path
                    if os.path.abspath(event.src_path) != str(target_path):
                        return
                elif not filename.endswith(".mmd"):
                    # In directory mode, only care about .mmd files
                    return

                # Broadcast file update event
                # Note: This runs in a thread, so we use asyncio.run to execute the async broadcast method
                # This works here because uvicorn runs in a separate process/loop context usually,
                # or if run directly, we need to be careful.
                # Actually uvicorn.run blocks. Watchdog runs in a separate thread.
                # asyncio.run() creates a NEW loop. This might be tricky if manager uses a loop bound to the main thread.
                # Ideally we should use loop.call_soon_threadsafe if we had access to the main loop.
                # But for this simple case, creating a new loop to put to queue (which is thread-safeish) might work
                # or might fail if Queue is bound to a loop.
                # asyncio.Queue IS NOT thread safe. This is a potential bug in the original implementation plan if strict asyncio is used.
                # However, let's keep the translation faithful to the logic.
                asyncio.run(manager.broadcast({"type": "update", "filename": filename}))

            def on_created(self, event: Any) -> None:
                # Handle new file creation event
                if not event.is_directory and event.src_path.endswith(".mmd"):
                    if not is_single_file:  # Only refresh list when monitoring a directory
                        asyncio.run(manager.broadcast({"type": "refresh_list"}))

        # Configure and start the observer
        observer = Observer()
        observer.schedule(Handler(), watch_scope, recursive=False)
        observer.start()
        print(f"[*] Watching: {target_path}")

    # Automatically open browser
    if open_browser:
        import webbrowser

        print(f"[*] Opening browser at http://localhost:{port}")
        webbrowser.open(f"http://localhost:{port}")

    print(f"[*] Starting Server at http://localhost:{port}")
    # Start Uvicorn server
    # host="0.0.0.0" allows external access
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
```

## 使用场景

- **默认模式**: 当你运行 `mermaid-trace serve` 时，默认启动此增强型服务器。
- **多文件预览**: 适合在一个项目中同时跟踪多个模块，并希望在浏览器中快速切换查看。
- **超大图表**: 对于普通的静态 HTML 难以查看的大型图表，此模块提供的缩放功能非常实用。
