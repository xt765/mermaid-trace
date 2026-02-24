# CLI 命令行工具模块 (cli.py)

`cli.py` 是 MermaidTrace 命令行工具的入口点。在 v0.7.0 版本中，它经过了全面重构，现在作为一个轻量级的调度器，将所有 Web 服务逻辑委托给功能更强大的 `server.py` 模块。

## 核心功能

- **统一入口**: 提供 `mermaid-trace serve` 命令，无需区分模式。
- **智能依赖检查**: 在启动服务器前检查是否安装了 `fastapi` 和 `uvicorn` 等可选依赖，如果缺失则给出友好的安装提示。
- **参数解析**: 使用 `argparse` 处理命令行参数，支持指定文件路径和端口。
- **向后兼容**: 保留了 `--master` 参数（虽然已不再需要），以兼容旧版本的脚本。

## 关键设计

### 1. 延迟导入 (Lazy Import)

为了保持 CLI 工具的轻量级启动速度，`server` 模块（包含繁重的 FastAPI 依赖）仅在用户实际执行 `serve` 命令时才会被导入。

```python
def serve(...):
    try:
        from .server import run_server
        ...
```

### 2. 优雅降级与错误提示

如果用户只安装了核心库（`pip install mermaid-trace`）而没有安装服务器依赖，CLI 会捕获 `ImportError` 或检查 `HAS_SERVER_DEPS` 标志，并打印出明确的安装指引：

```text
Error: The preview server requires additional dependencies.
Please install them with:
    pip install mermaid-trace[server]
```

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
