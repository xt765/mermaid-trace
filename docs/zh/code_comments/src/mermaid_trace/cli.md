# CLI 命令行接口模块 (cli.py)

`cli.py` 是 MermaidTrace 命令行工具的入口点。在 v0.7.1 版本中，它已被完全重构为一个轻量级调度器，将所有 Web 服务器逻辑委托给更健壮的 `server.py` 模块。

## 安装

从 v0.7.1 开始，FastAPI 和 Uvicorn 已成为必需依赖，安装后即可使用所有功能：

```bash
pip install mermaid-trace
```

安装后即可使用所有功能，包括：
- 代码追踪和生成 .mmd 文件
- Web 预览服务器（完全离线可用）
- 实时重载和交互控制

## 核心特性

- **统一入口点**: 提供 `mermaid-trace serve` 命令用于图表预览，以及 `mermaid-trace version` 用于版本信息查询。
- **参数解析**: 使用 `argparse` 处理命令行参数，支持文件路径、端口规范和浏览器控制。
- **离线支持**: Web 预览服务器使用本地静态资源，无需网络连接即可使用。

## 可用命令

### `mermaid-trace serve`

启动本地 HTTP 服务器以实时预览 Mermaid 图表文件。

**功能特性：**
- 实时更新 - 文件修改后图表自动重新加载
- 多文件支持 - 浏览目录中的所有 .mmd 文件
- 交互控制 - 缩放、平移和导出图表为 SVG
- 热重载 - 基于 Server-Sent Events (SSE) 的即时更新

**文件模式：**
- 单文件模式：提供 .mmd 文件路径以预览该文件
- 目录模式：提供目录路径以浏览所有 .mmd 文件

**选项：**
- `path`：要预览的 .mmd 文件或包含 .mmd 文件的目录路径（必需）
- `-p, --port`：服务器的端口号（默认：8000）
- `--no-browser`：不自动打开浏览器

**示例：**
```bash
mermaid-trace serve flow.mmd              # 预览单个图表文件
mermaid-trace serve ./diagrams            # 预览目录中的所有 .mmd 文件
mermaid-trace serve flow.mmd --port 3000  # 使用自定义端口
mermaid-trace serve flow.mmd --no-browser # 不自动打开浏览器
```

### `mermaid-trace version`

显示已安装的 MermaidTrace 版本。

**示例：**
```bash
mermaid-trace version
# 输出：MermaidTrace version: 0.7.1
```

## 关键技术设计

### 1. 延迟导入

为了保持 CLI 工具的轻量级启动，`server` 模块（包含重型 FastAPI 依赖）仅在用户实际执行 `serve` 命令时才导入。

```python
def serve(...):
    try:
        from .server import run_server
        ...
```

### 2. 错误处理

如果服务器模块导入失败（例如安装损坏），CLI 会提供清晰的指导：

```text
Error: Could not import server module.
Please ensure mermaid-trace is installed correctly:
    pip install mermaid-trace
```

### 3. 离线支持

从 v0.7.1 开始，Web 预览服务器使用本地静态资源而不是外部 CDN 依赖项。这确保预览功能在无网络连接的情况下也能正常工作。

## 源码分析

```python
"""
Command Line Interface (CLI) Module - MermaidTrace.

This module provides the command-line interface for MermaidTrace,
enabling users to preview Mermaid diagram files through a local web server.
"""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version as get_version


def get_package_version() -> str:
    """
    Get the installed package version.

    Returns:
        str: Version string, e.g., "0.7.0"
    """
    try:
        return get_version("mermaid-trace")
    except PackageNotFoundError:
        return "0.0.0 (development)"


def serve(target: str, port: int = 8000, open_browser: bool = True) -> None:
    """
    Start a local HTTP server to preview Mermaid diagrams.

    This function delegates the actual server logic to `mermaid_trace.server.run_server`.
    It handles dependency checking and provides installation instructions if
    required packages (fastapi, uvicorn) are missing.

    Args:
        target: Path to the .mmd file or directory to serve.
        port: The port number to bind the server to (default: 8000).
        open_browser: Whether to automatically open the browser (default: True).
    """
    try:
        from .server import run_server, HAS_SERVER_DEPS

        if HAS_SERVER_DEPS:
            run_server(target, port, open_browser)
        else:
            print("Error: The preview server requires additional dependencies.")
            print("\nPlease install them with one of the following commands:")
            print("    uv add mermaid-trace[server]")
            print("    # or")
            print("    uv add fastapi uvicorn watchdog")
            sys.exit(1)

    except ImportError:
        print("Error: Could not import server module.")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the CLI application.

    Parses command-line arguments and invokes the appropriate function
    based on the provided subcommand.
    """
    parser = argparse.ArgumentParser(
        prog="mermaid-trace",
        description=(
            "MermaidTrace - Visualize Python execution flow as Mermaid sequence diagrams.\n\n"
            "This tool helps you understand complex code execution by automatically\n"
            "tracing function calls and generating interactive sequence diagrams.\n\n"
            "Use 'mermaid-trace <command> --help' for detailed command information."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  mermaid-trace serve flow.mmd              # Preview a single diagram file\n"
            "  mermaid-trace serve ./diagrams            # Preview all .mmd files in directory\n"
            "  mermaid-trace serve flow.mmd --port 3000  # Use custom port\n"
            "  mermaid-trace serve flow.mmd --no-browser # Don't auto-open browser\n"
            "  mermaid-trace version                     # Show version information\n\n"
            "Documentation: https://github.com/xt765/mermaid-trace\n"
            "Bug Reports: https://github.com/xt765/mermaid-trace/issues"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="available commands",
        metavar="<command>",
    )

    # Version command
    subparsers.add_parser(
        "version",
        help="Display version information",
        description="Show the installed version of MermaidTrace.",
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start live preview server for Mermaid diagrams",
        description=(
            "Start a local HTTP server to preview Mermaid diagram files with live reload.\n\n"
            "Features:\n"
            "  • Real-time Updates - Diagrams reload automatically when files change\n"
            "  • Multi-file Support - Browse all .mmd files in a directory\n"
            "  • Interactive Controls - Zoom, pan, and export diagrams as SVG\n"
            "  • Hot Reload - Server-Sent Events (SSE) for instant updates\n\n"
            "File Modes:\n"
            "  - Single File: Provide a .mmd file path to preview that file\n"
            "  - Directory: Provide a directory path to browse all .mmd files"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    serve_parser.add_argument(
        "path",
        help="Path to a .mmd file or directory containing .mmd files",
    )

    serve_parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port number for the server (default: 8000)",
    )

    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser",
    )

    serve_parser.add_argument(
        "--master",
        action="store_true",
        help="Deprecated: Master mode is now the default.",
    )

    args = parser.parse_args()

    if args.command == "serve":
        serve(args.path, args.port, open_browser=not args.no_browser)
    elif args.command == "version":
        print(f"MermaidTrace version: {get_package_version()}")


if __name__ == "__main__":
    main()
```
