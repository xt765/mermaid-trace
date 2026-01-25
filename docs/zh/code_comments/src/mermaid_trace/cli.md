# 文件: src/mermaid_trace/cli.py

## 概览
本文件实现了命令行接口（CLI）工具，主要用于提供 `mermaid-trace serve` 命令。该命令启动一个本地 HTTP 服务器，用于在浏览器中实时预览生成的 `.mmd` 文件的图表。

## 核心功能分析

### serve 函数
这是 CLI 的主入口点。它做了两件事：
1.  **文件监控**：尝试使用 `watchdog` 库监控文件变化。如果可用，它会在控制台打印即时反馈。
2.  **HTTP 服务器**：启动一个 `ThreadingTCPServer`。这是一个多线程的 TCP 服务器，意味着它可以在处理浏览器轮询请求的同时，保持对其他请求的响应能力。

### HTML 模板与实时刷新
`HTML_TEMPLATE` 是一个自包含的 HTML 页面。它包含：
-   Mermaid.js 库（从 CDN 加载）。
-   一个简单的 JavaScript 轮询机制 (`setInterval`)。前端每秒请求 `/ _status` 端点来检查文件修改时间 (mtime)。
-   如果 mtime 发生变化，页面会自动刷新 (`location.reload()`)，从而重新渲染图表。

## 源代码与中文注释

```python
import argparse
import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path
from typing import Type, Any

try:
    # Watchdog 是一个可选依赖项，允许高效的文件监控。
    # 如果已安装，我们使用它来即时检测文件更改。
    from watchdog.observers import Observer  
    from watchdog.events import FileSystemEventHandler  
    HAS_WATCHDOG = True
except ImportError:
    # 当 watchdog 未安装时的回退（例如，最小安装）。
    HAS_WATCHDOG = False

# 预览页面的 HTML 模板
# 此模板提供了一个自包含的环境来渲染 Mermaid 图表。
# 它包括：
# 1. 来自 CDN 的 Mermaid.js 库。
# 2. 用于基本样式和布局的 CSS。
# 3. 当源文件更改时用于自动刷新的 JavaScript 逻辑。
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MermaidTrace Flow Preview</title>
    <!-- 从 CDN 加载 Mermaid.js -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        /* 为了可读性和布局的基本样式 */
        body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        #diagram {{ overflow-x: auto; }} /* 允许宽图表水平滚动 */
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
        <!-- Mermaid 图表内容将被注入此处 -->
        <div class="mermaid" id="diagram">
            {content}
        </div>
    </div>
    <!-- 手动重新加载页面/图表的按钮 -->
    <button class="refresh-btn" onclick="location.reload()">Refresh Diagram</button>
    <div class="status" id="status">Monitoring for changes...</div>

    <script>
        // 使用默认设置初始化 Mermaid
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        
        // 实时重载逻辑
        // 我们跟踪服务器发送的文件的修改时间 (mtime)。
        const currentMtime = "{mtime}";
        
        function checkUpdate() {{
            // 轮询 /_status 端点以检查磁盘上的文件是否已更改
            fetch('/_status')
                .then(response => response.text())
                .then(mtime => {{
                    // 如果服务器报告了不同的 mtime，重新加载页面
                    if (mtime && mtime !== currentMtime) {{
                        console.log("File changed, reloading...");
                        location.reload();
                    }}
                }})
                .catch(err => console.error("Error checking status:", err));
        }}
        
        // 每 1 秒轮询一次
        // 这是本地开发工具中 WebSocket 的简单替代方案
        setInterval(checkUpdate, 1000);
    </script>
</body>
</html>
"""

def _create_handler(filename: str, path: Path) -> Type[http.server.SimpleHTTPRequestHandler]:
    """
    创建自定义请求处理程序类的工厂函数。
    
    这使用闭包将 `filename` 和 `path` 注入到处理程序的作用域中，
    允许 `do_GET` 方法访问它们而无需全局变量。
    
    参数:
        filename (str): 文件的显示名称。
        path (Path): 磁盘上文件的 Path 对象。
        
    返回:
        Type[SimpleHTTPRequestHandler]: 自定义处理程序类。
    """
    class Handler(http.server.SimpleHTTPRequestHandler):
        """
        自定义请求处理程序，用于动态提供生成的 HTML。
        它拦截 GET 请求以提供构建的 HTML 而不是静态文件。
        """
        def log_message(self, format: str, *args: Any) -> None:
            # 抑制默认日志记录以保持控制台清洁
            # 我们只想看到应用程序日志，而不是每个 HTTP 请求
            pass

        def do_GET(self) -> None:
            """
            处理 GET 请求。
            为根路径 ('/') 提供 HTML 包装器。
            """
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                try:
                    # 读取 mermaid 文件的当前内容
                    content = path.read_text(encoding="utf-8")
                    mtime = str(path.stat().st_mtime)
                except Exception as e:
                    # 如果读取失败（例如，文件被锁定）的回退
                    # 直接在图表区域显示错误
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                    mtime = "0"
                
                # 将内容注入 HTML 模板
                html = HTML_TEMPLATE.format(filename=filename, content=content, mtime=mtime)
                self.wfile.write(html.encode("utf-8"))
            
            elif self.path == "/_status":
                # 客户端轮询的 API 端点。
                # 返回文件的当前修改时间。
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                try:
                    mtime = str(path.stat().st_mtime)
                except OSError:
                    mtime = "0"
                self.wfile.write(mtime.encode("utf-8"))
                
            else:
                # 如果需要，提供其他静态文件，或返回 404
                super().do_GET()
    return Handler

def serve(filename: str, port: int = 8000) -> None:
    """
    启动本地 HTTP 服务器以预览 Mermaid 图表。
    
    此函数阻塞主线程并运行 TCP 服务器。
    它会自动打开默认 Web 浏览器到预览 URL。
    
    特性:
    - 提供包裹在 HTML 查看器中的 .mmd 文件。
    - 使用 Watchdog（如果可用）或客户端轮询进行实时重载。
    - 在 Ctrl+C 时优雅地处理关闭。
    
    参数:
        filename (str): 要提供的 .mmd 文件的路径。
        port (int): 服务器绑定的端口。默认为 8000。
    """
    path = Path(filename)
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # 如果可用，设置 Watchdog
    # Watchdog 允许我们在文件更改时打印控制台消息。
    # 实际的浏览器重载由客户端轮询 /_status 端点触发，
    # 但 Watchdog 在终端中提供即时反馈。
    observer = None
    if HAS_WATCHDOG:
        class FileChangeHandler(FileSystemEventHandler):
            def on_modified(self, event: Any) -> None:
                # 过滤我们要监视的特定文件
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
    
    # 自动打开浏览器到服务器 URL
    webbrowser.open(f"http://localhost:{port}")
    
    # 启动 TCP 服务器
    # ThreadingTCPServer 用于并发处理多个请求（如果需要），
    # 确保浏览器轮询不会阻塞初始加载。
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
    CLI 应用程序的入口点。
    解析参数并将分发到相应的命令处理程序。
    """
    parser = argparse.ArgumentParser(description="MermaidTrace CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 'serve' 命令定义
    serve_parser = subparsers.add_parser("serve", help="Serve a Mermaid file in the browser")
    serve_parser.add_argument("file", help="Path to the .mmd file")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve(args.file, args.port)

if __name__ == "__main__":
    main()
```
