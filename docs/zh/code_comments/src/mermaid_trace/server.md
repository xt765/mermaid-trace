# 增强型 Web 服务器模块 (server.py)

`server.py` 是 MermaidTrace 提供的高级预览服务器模块。它基于 FastAPI 和 Server-Sent Events (SSE) 技术，实现了高性能、低延迟的实时预览功能，特别适用于需要频繁更新图表或管理多个跟踪文件的场景。

## 核心功能

- **实时更新 (SSE)**: 使用服务器发送事件（Server-Sent Events）代替传统的轮询机制。一旦服务器检测到文件变化，会立即向浏览器推送更新通知，实现真正的“零延迟”刷新。
- **文件列表管理**: 自动扫描指定目录下的所有 `.mmd` 文件，并在侧边栏提供快速切换功能。
- **交互式 UI**:
    - **缩放与平移**: 集成 `svg-pan-zoom` 库，支持通过鼠标滚轮或拖拽来查看大型复杂的时序图。
    - **响应式布局**: 基于 Tailwind CSS 构建，支持侧边栏折叠和自适应容器。
    - **导出功能**: 支持将当前显示的图表直接导出为 SVG 文件。
- **文件系统监控**: 深度集成 `watchdog`，能够监听文件的修改和新建事件，自动同步文件列表。

## 关键技术设计

### 1. 连接管理器 (`ConnectionManager`)

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

### 服务器启动 (`run_server`)
1. **路径解析**: 将传入的目录路径转换为绝对路径。
2. **启动监控**: 开启 `watchdog` 线程监听文件事件。
3. **启动 Web 服务**: 使用 `uvicorn` 运行 FastAPI 应用。

## 使用场景

- **Master 模式**: 当你运行 `mermaid-trace serve . --master` 时，会启动此增强型服务器。
- **多文件预览**: 适合在一个项目中同时跟踪多个模块，并希望在浏览器中快速切换查看。
- **超大图表**: 对于普通的静态 HTML 难以查看的大型图表，此模块提供的缩放功能非常实用。
