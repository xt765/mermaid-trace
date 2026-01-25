# src/mermaid_trace/handlers/mermaid_handler.py 代码分析

## 文件概览 (File Overview)
这个文件实现了 `MermaidFileHandler`，它是 Python `logging` 模块的一个插件（Handler）。
普通的 Log Handler 可能会把日志写到控制台或文本文件，而这个 Handler 专门负责把包含 `FlowEvent` 的日志转换成 Mermaid 格式，并写入 `.mmd` 文件。

## 核心概念 (Key Concepts)

*   **Logging Handler (日志处理器)**: `logging` 模块的组件，决定日志"去哪里"。你可以有多个 Handler，比如一个写文件，一个发邮件。
*   **File Mode 'w' vs 'a'**: 
    *   `'w'` (Write): 覆盖模式。每次运行程序都会清空文件，从头开始写。
    *   `'a'` (Append): 追加模式。新日志会加在文件末尾，保留之前的记录。

## 代码详解 (Code Walkthrough)

```python
import logging
from typing import Optional
from pathlib import Path
from ..core.events import FlowEvent

class MermaidFileHandler(logging.Handler):
    """
    一个自定义日志处理器，将 `FlowEvent` 对象直接写入 Mermaid (.mmd) 文件。
    
    此处理器监听在其 `extra` 字典中包含 `flow_event` 的日志，
    并以 Mermaid 序列图语法将它们追加到文件中。
    """
    def __init__(self, filename: str, title: str = "Log Flow", mode: str = 'w'):
        """
        初始化处理器。
        
        Args:
            filename (str): 输出 .mmd 文件的路径。
            title (str): Mermaid 图表的标题。
            mode (str): 文件打开模式。'w' (覆盖) 或 'a' (追加)。
                        默认为 'w'，即初始化一个新图表。
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.title = title
        
        # 如果是写入模式，用 Mermaid 图表头初始化文件
        if mode == 'w':
            self._write_header()

    def _write_header(self) -> None:
        """
        写入初始 Mermaid 语法行 (图表类型、标题、配置)。
        """
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write("sequenceDiagram\n")
            f.write(f"    title {self.title}\n")
            f.write("    autonumber\n")  # 自动为步骤编号

    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录。
        
        此方法检查日志记录是否包含 'flow_event' 属性。
        如果存在，它将事件转换为 Mermaid 字符串并将其追加到文件中。
        
        Args:
            record (logging.LogRecord): 要处理的日志记录。
        """
        # 检查此记录是否附加了流程事件。
        # `trace` 装饰器将 'flow_event' 附加到 'extra' 字典，
        # 日志系统将其合并到 LogRecord 对象中。
        event: Optional[FlowEvent] = getattr(record, 'flow_event', None)
        
        if event:
            try:
                # 将事件转换为图表行
                line = event.to_mermaid_line()
                
                # 立即追加到文件 (简单实现)
                # 注意：在高吞吐量系统中，你可能希望缓冲写入。
                with open(self.filename, 'a', encoding='utf-8') as f:
                    f.write(f"    {line}\n")
            except Exception:
                # 如果写入失败，回退到标准错误处理
                self.handleError(record)
```

## 新手指南 (Beginner's Guide)

*   **`emit` 方法是什么？**
    所有自定义 Handler 都必须实现 `emit` 方法。当你调用 `logger.info(...)` 时，logging 系统最终会调用所有 Handler 的 `emit` 方法来实际执行输出操作。

*   **`extra` 字典去哪了？**
    在 `decorators.py` 里我们调用了 `logger.info(..., extra={"flow_event": event})`。
    Python 的 logging 系统会自动把 `extra` 里的键值对变成 `LogRecord` 对象的属性。所以我们可以用 `getattr(record, 'flow_event', None)` 来取回它。

*   **为什么每次都要 `open(..., 'a')`？**
    这段代码在每次写日志时都打开并关闭文件。对于低频日志这是可以的，也更安全（防止程序崩溃时文件没保存）。但在高并发高性能要求的场景下，通常会保持文件句柄打开，或者使用缓冲队列。
