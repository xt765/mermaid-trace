"""
命令行接口 (CLI) 模块 - MermaidTrace.

本模块作为 MermaidTrace 命令行工具的入口点。
它提供了通过本地 HTTP 服务器预览 Mermaid 图表文件 (.mmd) 的功能，
底层利用了 `server.py` 中基于 FastAPI 的健壮实现。

使用方法:
    直接运行此模块或通过 `mermaid-trace` 命令（如果已安装）调用。
    示例: `mermaid-trace serve diagram.mmd --port 8080`
"""

import argparse  # 用于解析命令行参数的标准库
import sys       # 用于访问系统特定的参数和函数，如退出程序

def serve(target: str, port: int = 8000) -> None:
    """
    启动本地 HTTP 服务器以预览 Mermaid 图表。

    此函数将实际的服务器逻辑委托给 `mermaid_trace.server.run_server`。
    如果缺少必要的依赖项（如 fastapi, uvicorn），它会提供安装说明。

    参数:
        target (str): 要服务的 .mmd 文件或目录的路径。
        port (int): 服务器绑定的端口号（默认值: 8000）。
    """
    try:
        # 尝试从 server 模块导入运行函数和依赖检查标志
        # 延迟导入是为了避免在不需要服务器功能时加载沉重的依赖
        from .server import run_server, HAS_SERVER_DEPS

        # 检查是否安装了服务器所需的依赖（fastapi, uvicorn 等）
        if HAS_SERVER_DEPS:
            # 依赖齐全，启动服务器
            run_server(target, port)
        else:
            # 依赖缺失，打印错误信息并提示用户安装
            # 注意：虽然提示中使用 pip，但在现代 Python 开发中推荐使用 uv 等工具
            print("Error: The preview server requires additional dependencies.")
            print("Please install them with:")
            print("    pip install mermaid-trace[server]")
            print("Or manually:")
            print("    pip install fastapi uvicorn")
            sys.exit(1)  # 非零状态码退出，表示发生错误

    except ImportError:
        # 捕获导入 server 模块本身失败的情况（例如文件损坏或路径错误）
        print("Error: Could not import server module.")
        sys.exit(1)


def main() -> None:
    """
    CLI 应用程序的主入口点。
    负责解析命令行参数并根据子命令调用相应的功能函数。
    """
    # 创建顶级参数解析器
    parser = argparse.ArgumentParser(
        description="MermaidTrace CLI - 在浏览器中预览 Mermaid 图表"
    )

    # 创建子命令解析器，用于区分不同的操作（如 'serve'）
    # dest="command" 表示将子命令的名称存储在 args.command 属性中
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="可用命令"
    )

    # --- 'serve' 命令定义 ---
    # 添加 'serve' 子命令：用于启动实时预览服务器
    serve_parser = subparsers.add_parser(
        "serve",
        help="在浏览器中服务 Mermaid 文件或目录，支持实时重载",
    )
    
    # 添加 'path' 位置参数：指定要预览的文件或文件夹
    serve_parser.add_argument(
        "path", help="要服务的 .mmd 文件或目录的路径"
    )
    
    # 添加 '--port' 可选参数：指定服务器监听端口
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="绑定的端口 (默认: 8000)"
    )
    
    # 添加 '--master' 废弃参数
    # 保留此参数是为了向后兼容旧版本脚本，但在代码中会被忽略
    serve_parser.add_argument(
        "--master",
        action="store_true",
        help="已废弃: Master 模式现在是默认模式。",
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 根据解析出的子命令分发到对应的处理函数
    if args.command == "serve":
        # 如果是 'serve' 命令，调用 serve 函数
        serve(args.path, args.port)


if __name__ == "__main__":
    # 当脚本被直接运行时执行 main 函数
    main()
