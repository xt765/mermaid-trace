# src/mermaid_trace/cli.py 代码分析

## 文件概览 (File Overview)
`src/mermaid_trace/cli.py` 实现了命令行工具 (CLI)。它允许用户通过终端命令来启动一个本地 Web 服务器，实时预览生成的 Mermaid 流程图。
主要功能命令是：`python -m mermaid_trace serve flow.mmd`。

## 核心概念 (Key Concepts)

*   **CLI (Command Line Interface)**: 命令行界面，允许用户通过文本命令与程序交互。这里使用了 Python 标准库 `argparse`。
*   **HTTP Server**: 一个简单的 Web 服务器，用于将 `.mmd` 文件内容包装在 HTML 中发送给浏览器。
*   **Mermaid.js**: 一个 JavaScript 库，负责在浏览器端将文本格式的流程图代码渲染成漂亮的 SVG 图形。

## 代码详解 (Code Walkthrough)

```python
import argparse
import http.server
import socketserver
import webbrowser
import sys
from pathlib import Path

# 预览页面的 HTML 模板
# 这个模板从 CDN 加载 Mermaid.js 库来渲染图表。
# 它提供了一个简单的界面，带有一个刷新按钮，以便在文件更改时重新加载图表。
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
        /* 基础样式，提升可读性和布局 */
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
    </style>
</head>
<body>
    <div class="container">
        <h1>MermaidTrace Flow Preview: {filename}</h1>
        <!-- Mermaid 图表内容将被注入到这里 -->
        <div class="mermaid" id="diagram">
            {content}
        </div>
    </div>
    <!-- 手动重新加载页面/图表的按钮 -->
    <button class="refresh-btn" onclick="location.reload()">Refresh Diagram</button>
    <script>
        // 使用默认设置初始化 Mermaid
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>
"""

def serve(filename: str, port: int = 8000) -> None:
    """
    启动本地 HTTP 服务器以预览 Mermaid 图表。
    
    此函数读取指定的 .mmd 文件，将其包装在 HTML 模板中，并进行服务。
    它还会尝试自动打开默认 Web 浏览器。
    
    Args:
        filename (str): 要服务的 .mmd 文件的路径。
        port (int): 服务器绑定的端口号 (默认: 8000)。
    """
    path = Path(filename)
    if not path.exists():
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # 自定义请求处理器
    class Handler(http.server.SimpleHTTPRequestHandler):
        """
        自定义请求处理器，用于动态服务生成的 HTML。
        """
        def do_GET(self) -> None:
            """
            处理 GET 请求。
            为根路径 ('/') 服务 HTML 包装器。
            """
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                try:
                    # 读取 mermaid 文件的当前内容
                    content = path.read_text(encoding="utf-8")
                except Exception as e:
                    # 如果读取失败（例如，文件被锁定），提供回退内容
                    content = f"sequenceDiagram\nNote right of Error: Failed to read file: {e}"
                
                # 将内容注入 HTML 模板
                # 注意：这里用了 .format()，所以模板里的 {content} 会被替换
                html = HTML_TEMPLATE.format(filename=filename, content=content)
                self.wfile.write(html.encode("utf-8"))
            else:
                # 如果需要服务静态文件，或者返回 404
                super().do_GET()

    print(f"Serving {filename} at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    
    # 自动打开浏览器访问服务器 URL
    webbrowser.open(f"http://localhost:{port}")
    
    # 启动 TCP 服务器
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.server_close()

def main() -> None:
    """
    CLI 应用程序的入口点。
    解析命令行参数并分发到相应的函数。
    """
    parser = argparse.ArgumentParser(description="MermaidTrace CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 定义 'serve' 命令
    serve_parser = subparsers.add_parser("serve", help="Serve a Mermaid file in the browser")
    serve_parser.add_argument("file", help="Path to the .mmd file")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve(args.file, args.port)

if __name__ == "__main__":
    main()
```

## 新手指南 (Beginner's Guide)

*   **为什么需要这个服务器？**
    Mermaid 文件 (`.mmd`) 只是纯文本。要看到图形，你需要一个渲染器。虽然 VS Code 有插件可以看，但这个 CLI 让你可以在浏览器里分享给没有插件的人看，或者在服务器上查看。

*   **HTML 模板里的 `{content}` 是什么？**
    这是 Python 字符串格式化的占位符。代码运行时，会读取你的 `.mmd` 文件内容，替换掉这个占位符，生成最终的 HTML 网页。

*   **`http.server` 是什么？**
    这是 Python 自带的一个非常基础的 Web 服务器模块。虽然它不适合用于生产环境（性能不高），但用于这种本地开发预览工具简直完美，因为它不需要安装任何第三方依赖。
