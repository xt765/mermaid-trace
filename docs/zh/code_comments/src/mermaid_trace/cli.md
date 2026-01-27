# CLI 命令行工具模块 (cli.py)

`cli.py` 是 MermaidTrace 命令行工具的入口点。它提供了一个本地 HTTP 服务器，用于在浏览器中实时预览生成的 Mermaid 序列图（.mmd 文件），并支持自动刷新。

## 核心功能

- **本地预览服务器**: 启动一个微型 HTTP 服务器，将 Mermaid 文件渲染为网页。
- **实时预览与自动刷新**: 使用浏览器端轮询（Polling）机制，当检测到文件变动时自动刷新页面。
- **文件监控**: 集成 `watchdog` 库（可选）进行高效的文件系统监控。
- **内嵌渲染引擎**: 使用 Mermaid.js CDN 在客户端渲染图表，无需安装复杂的图形库。

## 关键设计

### 1. HTML 模板与 Mermaid.js 集成

模块内置了一个 `HTML_TEMPLATE` 字符串，它包含了：
- **Mermaid.js 加载**: 从 CDN 引入库文件。
- **自动刷新逻辑**: JavaScript `setInterval` 每秒调用 `/_status` 接口，比对文件修改时间（mtime）。
- **错误容错机制**: 如果文件读取失败（例如文件被占用、权限不足或被删除），后端会注入 `mtime = "0"` 并生成一个包含错误提示的 Mermaid 图表。这确保了前端页面不会崩溃，且用户能立即看到错误原因。

### 2. 自定义请求处理器工厂 (`_create_handler`)

为了向 `socketserver` 传递动态参数（如文件名和路径），使用了工厂模式。

```python
def _create_handler(filename: str, path: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                # 渲染 HTML 模板并注入内容
                ...
            elif self.path == "/_status":
                # 返回文件的最新修改时间 (mtime)
                ...
    return Handler
```

### 3. 混合监控模式

- **Watchdog (服务端)**: 如果安装了 `watchdog`，会在控制台实时打印文件变动日志。
- **Polling (客户端)**: 浏览器通过 Ajax 轮询 `/_status` 接口，这是实现自动刷新的核心机制，即使没有 `watchdog` 也能工作。

## 源码分析与注释

```python
# 尝试导入 watchdog 以实现高效监控
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

def serve(filename: str, port: int = 8000) -> None:
    """
    启动本地服务器。
    1. 验证文件路径。
    2. 设置 Watchdog 监控（可选）。
    3. 创建 HTTP 处理程序。
    4. 自动打开浏览器。
    5. 进入服务循环。
    """
    path = Path(filename)
    if not path.exists():
        print(f"错误: 找不到文件 '{filename}'")
        sys.exit(1)

    # 启动 Watchdog (仅用于终端提示)
    if HAS_WATCHDOG:
        observer = Observer()
        observer.schedule(FileChangeHandler(), path=str(path.parent), recursive=False)
        observer.start()

    # 创建处理器并启动线程化服务器
    # ThreadingTCPServer 允许同时处理多个请求（如轮询和页面加载）
    HandlerClass = _create_handler(filename, path)
    with socketserver.ThreadingTCPServer(("", port), HandlerClass) as httpd:
        webbrowser.open(f"http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            # 捕获 Ctrl+C 实现优雅退出
            if observer:
                observer.stop()
            httpd.server_close()

def main() -> None:
    """
    CLI 命令行解析。
    使用 argparse 定义 'serve' 命令及其参数。
    """
    parser = argparse.ArgumentParser(description="MermaidTrace CLI - 在浏览器中预览 Mermaid 图表")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 定义 serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动实时预览服务器")
    serve_parser.add_argument("file", help="要预览的 .mmd 文件路径")
    serve_parser.add_argument("--port", type=int, default=8000, help="服务器端口")

    args = parser.parse_args()
    if args.command == "serve":
        serve(args.file, args.port)
```

## 使用示例

在终端运行：
```bash
# 启动预览
mermaid-trace serve trace.mmd --port 8080
```
或直接使用 Python 模块运行：
```bash
python -m mermaid_trace.cli serve trace.mmd
```
