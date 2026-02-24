"""
MermaidTrace 增强型 Web 服务器。

本模块提供了一个基于 FastAPI 和 Server-Sent Events (SSE) 的健壮实时预览服务器。
它负责监控 .mmd 文件，并将更新即时推送到浏览器端进行渲染。
"""

import asyncio
import os
import json
from pathlib import Path
from typing import AsyncGenerator, Set, Any

# 尝试导入服务器相关依赖 (FastAPI, Uvicorn)
# 使用 try-except 块是为了让 mermaid-trace 在未安装 [server] 额外依赖的情况下也能被导入（虽然不能运行 server 功能）
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse
    import uvicorn

    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

    # 模拟依赖项，允许在未安装依赖时也能导入模块
    # 这是一种优雅降级策略，避免因缺少可选依赖导致整个库不可用
    class MockException(Exception):
        pass

    class Mock:
        pass

    class MockApp:
        def get(self, *args, **kwargs):
            return lambda f: f

    # 创建伪造的 FastAPI 类和对象，防止 NameError
    def FastAPI(**kw: Any) -> MockApp:  # type: ignore
        return MockApp()
    Request = Mock  # type: ignore
    HTTPException = MockException  # type: ignore
    HTMLResponse = Mock  # type: ignore
    StreamingResponse = Mock  # type: ignore

# 尝试导入文件监控依赖 (Watchdog)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# 初始化 FastAPI 应用
app = FastAPI(title="MermaidTrace Preview Server")


# 用于管理 SSE (Server-Sent Events) 连接的全局状态类
class ConnectionManager:
    """
    连接管理器：处理客户端的订阅与消息广播。
    使用异步队列 (asyncio.Queue) 为每个连接的客户端存储待发送的消息。
    """
    def __init__(self) -> None:
        # 存储所有活跃连接的队列集合
        self.active_connections: Set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """
        客户端订阅：创建一个新的消息队列并加入活跃列表。
        
        Returns:
            asyncio.Queue: 用于接收消息的队列
        """
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.active_connections.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """
        取消订阅：从活跃列表中移除指定的队列。
        通常在客户端断开连接时调用。
        """
        self.active_connections.remove(queue)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """
        广播消息：向所有活跃的客户端队列推送消息。
        
        Args:
            data: 要发送的数据字典
        """
        for queue in self.active_connections:
            await queue.put(data)


# 全局连接管理器实例
manager = ConnectionManager()

# 增强型 UI 的 HTML 模板
# 包含：
# 1. Mermaid.js: 用于渲染图表
# 2. svg-pan-zoom: 用于图表的缩放和平移交互
# 3. Tailwind CSS: 用于美化界面
# 4. 自定义 JavaScript: 处理 SSE 事件、文件加载和渲染逻辑
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Master Preview</title>
    <!-- 引入必要的外部库 -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; }
        .mermaid { background: white; }
        /* 图表容器样式：设置背景网格和布局 */
        #diagram-container { 
            height: calc(100vh - 10rem); 
            overflow: hidden; 
            position: relative;
            background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex;
            flex-direction: column;
        }
        /* SVG 包装器：处理鼠标交互 */
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
        
        /* 确保 mermaid 生成的 SVG 不受最大宽度限制，以便自由缩放 */
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
    <!-- 顶部导航栏 -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center space-x-3">
            <div class="bg-blue-600 text-white p-2 rounded-lg">
                <!-- Logo 图标 -->
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
            </div>
            <h1 class="text-xl font-bold text-gray-800">MermaidTrace <span class="text-blue-600">Master</span></h1>
        </div>
        <!-- 工具栏按钮 -->
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
        <!-- 侧边栏：文件列表 -->
        <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto hidden md:block">
            <div class="p-4 border-b border-gray-100">
                <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Trace Files</h2>
            </div>
            <nav id="file-list" class="p-2 space-y-1">
                <!-- 文件列表项将通过 JS 动态注入 -->
            </nav>
        </aside>

        <!-- 主内容区域：图表展示 -->
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

        // 初始化 Mermaid 库
        function initMermaid() {
            if (typeof mermaid === 'undefined') {
                console.log("Waiting for mermaid...");
                setTimeout(initMermaid, 100);
                return;
            }
            
            mermaid.initialize({ 
                startOnLoad: false, 
                theme: 'default',
                securityLevel: 'loose', // 允许宽松的安全级别以支持 HTML 标签
                useMaxWidth: false,
                sequence: { 
                    showSequenceNumbers: true,
                    useMaxWidth: false,
                    bottomMarginAdjustment: 1
                }
            });
            
            // 初始化文件列表
            updateFileList();
        }

        // 加载指定文件内容
        async function loadFile(filename) {
            if (!filename) return;
            currentFile = filename;
            
            // 更新侧边栏选中状态
            document.querySelectorAll('.sidebar-item').forEach(el => {
                if (el.dataset.filename === filename) el.classList.add('active');
                else el.classList.remove('active');
            });

            try {
                // 调用后端 API 获取文件内容
                const response = await fetch(`/api/file?name=${encodeURIComponent(filename)}`);
                const data = await response.json();
                
                document.getElementById('current-filename').textContent = filename;
                renderDiagram(data.content);
                updateTimestamp();
            } catch (err) {
                console.error("Failed to load file:", err);
            }
        }

        // 渲染 Mermaid 图表
        async function renderDiagram(content) {
            const graphDiv = document.getElementById('mermaid-graph');
            graphDiv.removeAttribute('data-processed');
            // 渲染新图表前清理旧内容
            graphDiv.innerHTML = content;
            
            try {
                // 使用 mermaid API 生成 SVG
                const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), content);
                graphDiv.innerHTML = svg;
                // 设置平移和缩放功能
                setupPanZoom();
            } catch (err) {
                console.error("Mermaid render error:", err);
            }
        }

        // 配置 SVG 的平移和缩放交互
        function setupPanZoom() {
            if (panZoomInstance) {
                panZoomInstance.destroy();
                panZoomInstance = null;
            }
            const svg = document.querySelector('#mermaid-graph svg');
            if (svg) {
                // 确保 SVG 占满容器
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.maxWidth = 'none';
                svg.style.maxHeight = 'none';
                
                // 清除可能与 'fit' 冲突的显式宽高属性
                svg.removeAttribute('width');
                svg.removeAttribute('height');
                
                // 初始化 svg-pan-zoom
                panZoomInstance = svgPanZoom(svg, {
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: true,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 20,
                    zoomScaleSensitivity: 0.2
                });

                // 窗口大小改变时自动适应
                window.addEventListener('resize', () => {
                    if (panZoomInstance) {
                        panZoomInstance.resize();
                        panZoomInstance.fit();
                        panZoomInstance.center();
                    }
                });
            }
        }

        // 重置缩放视图
        function resetZoom() {
            if (panZoomInstance) {
                panZoomInstance.fit();
                panZoomInstance.center();
            }
        }

        // 更新最后更新时间戳
        function updateTimestamp() {
            const now = new Date();
            document.getElementById('last-updated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }

        // 更新文件列表
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

            // 如果没有选中文件且有文件可用，默认加载第一个
            if (!currentFile && files.length > 0) {
                loadFile(files[0]);
            }
        }

        // 建立 SSE 连接以接收实时更新
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
        
        // 开始初始化流程
        initMermaid();

        // 下载当前图表为 SVG 文件
        function downloadSVG() {
            const svg = document.querySelector('#diagram-container svg');
            if (!svg) return;
            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svg);
            // 添加命名空间以确保 SVG 格式正确
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

# 全局变量：要监控的目录或文件路径
# 默认为当前目录
watch_dir: Path = Path(".")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    """
    主页路由。
    
    Returns:
        str: 渲染后的 HTML 页面内容。
    """
    # 如果 watch_dir 是一个文件，我们可能需要立即渲染它或重定向
    # 但目前 watch_dir 在 run_server 中被解析，前端逻辑会处理文件加载
    return HTML_TEMPLATE


@app.get("/api/files")
async def list_files() -> list[str]:
    """
    获取文件列表 API。
    
    Returns:
        list[str]: 可用的 .mmd 文件名列表。
    """
    # 如果监控的是单个文件，只返回该文件
    if os.path.isfile(str(watch_dir)):
        return [os.path.basename(str(watch_dir))]

    # 如果监控的是目录，返回目录下所有 .mmd 文件
    if os.path.isdir(str(watch_dir)):
        files = sorted([f.name for f in Path(watch_dir).glob("*.mmd")])
        return files

    return []


@app.get("/api/file")
async def get_file_content(name: str) -> dict[str, str]:
    """
    获取特定文件内容 API。
    
    Args:
        name: 请求的文件名
        
    Returns:
        dict: 包含文件内容的字典 {"content": "..."}
        
    Raises:
        HTTPException: 如果文件名非法或文件不存在
    """
    # 安全检查：防止目录遍历攻击 (Directory Traversal)
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=403, detail="Invalid filename")

    if os.path.isfile(str(watch_dir)):
        # 单文件模式：忽略 name 参数或确保它匹配目标文件
        target_file = Path(str(watch_dir))
        if target_file.name != name:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        # 目录模式：拼接路径
        target_file = Path(watch_dir) / name

    if not target_file.exists() or not str(target_file).endswith(".mmd"):
        raise HTTPException(status_code=404, detail="File not found")

    return {"content": target_file.read_text(encoding="utf-8")}


@app.get("/events")
async def sse_endpoint(request: Request) -> StreamingResponse:
    """
    Server-Sent Events (SSE) 端点。
    用于向前端实时推送文件更新通知。
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        # 订阅更新
        queue = await manager.subscribe()
        try:
            while True:
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    break
                # 等待队列中的新消息
                data = await queue.get()
                # 发送 SSE 格式的数据
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            # 清理：取消订阅
            manager.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def run_server(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    启动 FastAPI 服务器以预览 Mermaid 图表。

    Args:
        target: 要监控的文件或目录路径。
        port: 服务器绑定的端口号。
        open_browser: 是否自动在默认浏览器中打开预览页面。
    """
    global watch_dir
    target_path = Path(target).resolve()

    if not target_path.exists():
        print(f"Error: Target '{target}' not found.")
        return

    # 设置全局监控路径
    # 这里的逻辑稍显复杂：
    # 如果 target 是文件，watch_dir 就设为该文件路径，API 会相应处理单文件模式
    # 如果 target 是目录，watch_dir 就设为该目录路径
    watch_dir = target_path

    # 检查服务器依赖是否安装
    if not HAS_SERVER_DEPS:
        print("Error: FastAPI and Uvicorn are required for the preview server.")
        print("Please install them with: pip install mermaid-trace[server]")
        print("Or manually: pip install fastapi uvicorn")
        return

    # 启动 Watchdog 文件监控
    if HAS_WATCHDOG:
        # 确定监控范围 (Scope)
        if target_path.is_file():
            # Watchdog 只能监控目录，所以如果是单文件，我们需要监控其父目录
            watch_scope = str(target_path.parent)
            is_single_file = True
        else:
            watch_scope = str(target_path)
            is_single_file = False

        class Handler(FileSystemEventHandler):
            """文件系统事件处理器"""
            def on_modified(self, event: Any) -> None:
                if event.is_directory:
                    return

                filename = os.path.basename(event.src_path)

                # 过滤逻辑：只关心目标文件的变化
                if is_single_file:
                    # 确保变化的绝对路径与目标路径一致
                    if os.path.abspath(event.src_path) != str(target_path):
                        return
                elif not filename.endswith(".mmd"):
                    # 目录模式下，只关心 .mmd 后缀的文件
                    return

                # 广播文件更新事件
                asyncio.run(manager.broadcast({"type": "update", "filename": filename}))

            def on_created(self, event: Any) -> None:
                # 处理新文件创建事件
                if not event.is_directory and event.src_path.endswith(".mmd"):
                    if not is_single_file:  # 仅在监控目录时刷新列表
                        asyncio.run(manager.broadcast({"type": "refresh_list"}))

        # 配置并启动观察者
        observer = Observer()
        observer.schedule(Handler(), watch_scope, recursive=False)
        observer.start()
        print(f"[*] Watching: {target_path}")

    # 自动打开浏览器
    if open_browser:
        import webbrowser

        print(f"[*] Opening browser at http://localhost:{port}")
        webbrowser.open(f"http://localhost:{port}")

    print(f"[*] Starting Server at http://localhost:{port}")
    # 启动 Uvicorn 服务器
    # host="0.0.0.0" 允许外部访问
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
