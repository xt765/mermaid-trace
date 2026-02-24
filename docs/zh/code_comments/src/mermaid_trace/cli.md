# CLI 命令行工具模块 (cli.py)

`cli.py` 是 MermaidTrace 命令行工具的入口点。它提供了一个本地 HTTP 服务器，用于在浏览器中实时预览生成的 Mermaid 序列图（.mmd 文件），并支持自动刷新。

## 核心功能

- **本地预览服务器**: 启动一个微型 HTTP 服务器，将 Mermaid 文件渲染为网页。
- **Master 增强模式**: 集成 FastAPI 和 SSE 技术，提供支持文件列表浏览、缩放平移和即时更新的高级预览界面。
- **实时预览与自动刷新**: 使用浏览器端轮询（基础模式）或 SSE（Master 模式），当检测到文件变动时自动刷新页面。
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
# Try to import watchdog for efficient monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

def serve(target: str, port: int = 8000) -> None:
    """
    Start the local HTTP server to preview Mermaid diagrams.

    This function delegates the actual server logic to `mermaid_trace.server.run_server`.
    If the required dependencies (fastapi, uvicorn) are missing, it provides instructions.

    Args:
        target (str): The path to the .mmd file or directory to serve.
        port (int): The port number to bind the server to (default: 8000).
    """
    try:
        # Try to import the run function and dependency check flag from the server module
        # Delayed import is used to avoid loading heavy dependencies when server functionality is not needed
        from .server import run_server, HAS_SERVER_DEPS

        # Check if the dependencies required for the server (fastapi, uvicorn, etc.) are installed
        if HAS_SERVER_DEPS:
            # Dependencies are present, start the server
            run_server(target, port)
        else:
            # Dependencies are missing, print error message and prompt user to install
            # Note: Although pip is used in the prompt, tools like uv are recommended in modern Python development
            print("Error: The preview server requires additional dependencies.")
            print("Please install them with:")
            print("    pip install mermaid-trace[server]")
            print("Or manually:")
            print("    pip install fastapi uvicorn")
            sys.exit(1)  # Exit with non-zero status code indicating an error

    except ImportError:
        # Catch cases where importing the server module itself fails (e.g., corrupted files or wrong paths)
        print("Error: Could not import server module.")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the CLI application.
    Responsible for parsing command-line arguments and calling the corresponding handler function based on the subcommand.
    """
    # Create top-level argument parser
    parser = argparse.ArgumentParser(
        description="MermaidTrace CLI - Preview Mermaid diagrams in browser"
    )

    # Create subcommand parsers to distinguish different operations (like 'serve')
    # dest="command" means the subcommand name will be stored in the args.command attribute
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- 'serve' command definition ---
    # Add 'serve' subcommand: used to start the real-time preview server
    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve a Mermaid file or directory in the browser with live reload",
    )
    
    # Add 'path' positional argument: specify the file or folder to preview
    serve_parser.add_argument(
        "path", help="Path to the .mmd file or directory to serve"
    )
    
    # Add '--port' optional argument: specify the server listening port
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    
    # Add '--master' deprecated argument
    # Kept for backward compatibility with old version scripts, but ignored in code
    serve_parser.add_argument(
        "--master",
        action="store_true",
        help="Deprecated: Master mode is now the default.",
    )

    # Parse command-line arguments
    args = parser.parse_args()

    # Dispatch to the corresponding handler function based on the parsed subcommand
    if args.command == "serve":
        # If it is the 'serve' command, call the serve function
        serve(args.path, args.port)


if __name__ == "__main__":
    # Execute main function when script is run directly
    main()
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
