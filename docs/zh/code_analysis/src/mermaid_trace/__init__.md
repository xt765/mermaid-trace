# src/mermaid_trace/__init__.py 代码分析

## 文件概览 (File Overview)
`src/mermaid_trace/__init__.py` 是 `mermaid-trace` 包的入口文件。它的主要作用是：
1. **暴露公共 API**：让用户可以方便地导入核心功能（如 `@trace` 装饰器、配置函数等），而不需要深入到子模块中。
2. **初始化版本信息**：获取并提供当前安装包的版本号。
3. **提供配置入口**：包含 `configure_flow` 函数，用于设置日志记录器，这是使用该库的第一步。

## 核心概念 (Key Concepts)

*   **Package (包)**: Python 中包含 `__init__.py` 的目录，用于组织代码模块。
*   **Public API (公共接口)**: 开发者希望用户使用的函数和类。通过 `__all__` 列表明确定义。
*   **Logging Configuration (日志配置)**: 设置 Python `logging` 模块以特定方式（这里是写入 Mermaid 文件）处理日志的过程。

## 代码详解 (Code Walkthrough)

```python
"""
MermaidTrace: Visualize your Python code execution flow as Mermaid Sequence Diagrams.

This package provides tools to automatically trace function calls and generate
Mermaid-compatible sequence diagrams (.mmd files). It is designed to help
developers understand the flow of their applications, debug complex interactions,
and document system behavior.

Key Components:
- `trace`: A decorator to instrument functions for tracing.
- `LogContext`: Manages execution context (like thread-local storage) to track
  caller/callee relationships across async tasks and threads.
- `configure_flow`: Sets up the logging handler to write diagrams to a file.
"""

# 导入核心组件，方便用户直接从包顶层使用
from .core.decorators import trace_interaction, trace
from .handlers.mermaid_handler import MermaidFileHandler
from .core.events import FlowEvent
from .core.context import LogContext
# 注意：我们默认不导入 integrations (如 FastAPI)，以避免强制依赖。
# 用户如果需要集成，必须显式导入，例如: from mermaid_trace.integrations.fastapi import ...

from importlib.metadata import PackageNotFoundError, version

import logging

def configure_flow(output_file: str = "flow.mmd") -> logging.Logger:
    """
    配置流程记录器以输出到 Mermaid 文件。
    
    这个函数设置了捕获跟踪事件并将它们写入指定输出文件所需的日志基础设施。
    它应该在你的应用程序启动时调用一次。
    
    Args:
        output_file (str): 输出 .mmd 文件的绝对或相对路径。
                           默认为当前目录下的 "flow.mmd"。
    
    Returns:
        logging.Logger: 用于流程跟踪的已配置 logger 实例。
    """
    # 获取跟踪装饰器使用的特定 logger
    # 这里的名字 "mermaid_trace.flow" 必须与 decorators.py 中定义的一致
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(logging.INFO)
    
    # 删除现有处理器，避免如果多次调用配置函数导致重复日志
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 创建并附加自定义处理器，该处理器负责写入 Mermaid 语法
    handler = MermaidFileHandler(output_file)
    logger.addHandler(handler)
    
    return logger

try:
    # 尝试检索已安装包的版本
    __version__ = version("mermaid-trace")
except PackageNotFoundError:
    # 如果包未安装（例如，本地开发模式），使用回退版本
    __version__ = "0.0.0"


# 导出公共 API，定义当用户执行 `from mermaid_trace import *` 时会导入哪些名称
__all__ = ["trace_interaction", "trace", "configure_flow", "MermaidFileHandler", "LogContext", "FlowEvent"]
```

## 新手指南 (Beginner's Guide)

*   **为什么要用 `configure_flow`？**
    仅仅在函数上加 `@trace` 是不够的，你需要告诉程序把生成的图表数据**写到哪里**。`configure_flow` 就是做这件事的，通常在 `main.py` 的最开始调用它。

*   **`__all__` 的作用是什么？**
    它是一个白名单。如果你写了 `from mermaid_trace import *`，只有 `__all__` 列表里的东西会被导入。这是一种良好的编程习惯，可以防止污染用户的命名空间。

*   **为什么看不到 FastAPI 的导入？**
    这是一个设计模式。如果你的项目里没有安装 `fastapi`，强制导入会导致报错。通过让用户按需导入（`from mermaid_trace.integrations.fastapi import ...`），库可以保持轻量且兼容性更好。
