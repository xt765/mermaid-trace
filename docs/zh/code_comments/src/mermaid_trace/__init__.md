# 文件: src/mermaid_trace/__init__.py

## 概览
本文件是 `mermaid-trace` 包的入口点。它导出了主要的 API，如 `trace` 装饰器、`LogContext` 上下文管理器和 `configure_flow` 配置函数。

## 核心功能分析

### configure_flow
这是配置日志系统的核心函数。它负责：
1.  初始化专用的 Logger (`mermaid_trace.flow`)。
2.  管理 Handler（处理器）的生命周期：
    -   默认情况下，它会清除现有的 Handler，保证配置的幂等性。
    -   通过 `append=True` 参数，允许用户追加新的 Handler 而不覆盖旧的。
3.  **异步支持**：通过 `async_mode` 参数，它能够将实际的 Handler 包装在 `AsyncMermaidHandler` (QueueHandler) 中，从而将文件写入操作移至后台线程，避免阻塞主循环。

## 源代码与中文注释

```python
"""
MermaidTrace: 将 Python 代码执行流可视化为 Mermaid 时序图。

该包提供了自动追踪函数调用并生成兼容 Mermaid 的时序图（.mmd 文件）的工具。
旨在帮助开发者理解应用程序的流程、调试复杂的交互并记录系统行为。

关键组件:
- `trace`: 用于检测函数进行追踪的装饰器。它捕获参数、返回值和错误，并将它们记录为交互。
- `LogContext`: 管理执行上下文（类似于线程本地存储），用于在异步任务和线程之间追踪调用者/被调用者关系。
- `configure_flow`: 设置日志处理器以将图表写入文件。它处理处理器配置、文件模式和异步日志设置。
"""

from .core.decorators import trace_interaction, trace
from .handlers.mermaid_handler import MermaidFileHandler
from .handlers.async_handler import AsyncMermaidHandler
from .core.events import FlowEvent
from .core.context import LogContext
from .core.formatter import MermaidFormatter

# 默认不导入集成模块，以避免硬依赖
# 如果需要，用户必须显式导入集成（如 FastAPI）。

from importlib.metadata import PackageNotFoundError, version
from typing import List, Optional

import logging

def configure_flow(
    output_file: str = "flow.mmd",
    handlers: Optional[List[logging.Handler]] = None,
    append: bool = False,
    async_mode: bool = False
) -> logging.Logger:
    """
    配置流程日志记录器以输出到 Mermaid 文件。
    
    此函数设置捕获追踪事件并将其写入指定输出文件所需的日志基础设施。
    应在应用程序启动时调用一次以初始化追踪系统。
    
    参数:
        output_file (str): 输出 .mmd 文件的绝对或相对路径。
                           默认为当前目录下的 "flow.mmd"。
                           如果文件不存在，将使用正确的头部创建它。
        handlers (List[logging.Handler], optional): 自定义日志处理器列表。
                                                    如果提供，'output_file' 将被忽略，除非
                                                    你显式包含 MermaidFileHandler。
                                                    如果你想将日志流式传输到其他目的地，这很有用。
        append (bool): 如果为 True，则添加新处理器而不移除现有处理器。
                       默认为 False（清除现有处理器以防止重复记录）。
        async_mode (bool): 如果为 True，使用非阻塞后台线程进行日志记录 (QueueHandler)。
                           推荐用于高性能生产环境，以避免在文件 I/O 期间阻塞主执行线程。
                           默认为 False。
    
    返回:
        logging.Logger: 用于流程追踪的已配置日志记录器实例。
    """
    # 获取追踪装饰器使用的特定日志记录器
    # 此日志记录器与根日志记录器隔离，以防止污染
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(logging.INFO)
    
    # 移除现有处理器以避免重复日志（如果配置了多次）
    # 除非请求了 'append'。这确保了多次调用 configure_flow 时的幂等性。
    if not append and logger.hasHandlers():
        logger.handlers.clear()
        
    # 确定目标处理器
    target_handlers = []
    
    if handlers:
        # 如果可用，使用用户提供的处理器
        target_handlers = handlers
    else:
        # 创建默认 Mermaid 处理器
        # 此处理器知道如何写入 Mermaid 头部并格式化事件
        handler = MermaidFileHandler(output_file)
        handler.setFormatter(MermaidFormatter())
        target_handlers = [handler]
    
    if async_mode:
        # 将目标处理器包装在 AsyncMermaidHandler (QueueHandler) 中
        # QueueListener 将从队列中提取日志并分发到目标处理器
        # 这将应用程序执行与日志 I/O 解耦
        async_handler = AsyncMermaidHandler(target_handlers)
        logger.addHandler(async_handler)
    else:
        # 直接将处理器附加到日志记录器以进行同步日志记录
        # 简单可靠，适用于调试或低吞吐量应用程序
        for h in target_handlers:
            logger.addHandler(h)
    
    return logger

try:
    # 尝试检索已安装的包版本
    __version__ = version("mermaid-trace")
except PackageNotFoundError:
    # 如果包未安装（例如，本地开发），则使用回退版本
    __version__ = "0.0.0"


# 导出公共 API 以方便访问
__all__ = ["trace_interaction", "trace", "configure_flow", "MermaidFileHandler", "AsyncMermaidHandler", "LogContext", "Event", "FlowEvent", "BaseFormatter", "MermaidFormatter"]
```
