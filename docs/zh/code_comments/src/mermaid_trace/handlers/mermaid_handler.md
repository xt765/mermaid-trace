# 文件: src/mermaid_trace/handlers/mermaid_handler.py

## 概览
`mermaid_handler.py` 模块提供了一个自定义的日志处理器 `MermaidFileHandler`。它的主要职责是将追踪到的事件持久化到 `.mmd` 文件中，并确保生成的每一份文件都是符合 Mermaid 语法的合法文档。

## 核心功能分析

### 1. `MermaidHandlerMixin` 类
这是一个混入类 (Mixin)，为不同的日志处理器（如 `FileHandler`、`RotatingFileHandler` 等）提供 Mermaid 特有的处理逻辑。

- **核心职责**:
    - **头部管理**: 定义了 `_write_header` 方法，用于在文件开始处写入 Mermaid 语法（如 `sequenceDiagram`）。
    - **智能 emit**: 增强了标准的 `emit` 方法，增加了轮转检查 (`shouldRollover`)、头部写入检查以及与 `MermaidFormatter` 协作的逻辑。
    - **缓冲区刷新**: 重写了 `flush` 方法，确保在关闭文件或手动刷新时，`MermaidFormatter` 中的折叠缓冲区也能被正确写出。

### 2. `MermaidFileHandler` 类
继承自 `MermaidHandlerMixin` 和 `logging.FileHandler`。

- **设计策略**:
    - **线程安全**: 利用 `logging.FileHandler` 的内置锁机制。
    - **目录自动创建**: 在初始化时自动创建目标路径，增强易用性。

### 3. `RotatingMermaidFileHandler` 类
继承自 `MermaidHandlerMixin` 和 `logging.handlers.RotatingFileHandler`。

- **解决的问题**: 针对生产环境，防止单个 `.mmd` 文件因追踪数据过多而体积爆炸。
- **轮转逻辑**: 当文件达到 `maxBytes` 时，自动进行切割。由于混入了 `MermaidHandlerMixin`，新创建的文件会自动获得正确的 Mermaid 头部，确保每个分片文件都可独立渲染。

### 4. `TimedRotatingMermaidFileHandler` 类
继承自 `MermaidHandlerMixin` 和 `logging.handlers.TimedRotatingFileHandler`。

- **应用场景**: 适用于按天、按小时等固定时间周期归档追踪数据的场景。

## 源代码与中文注释

```python
"""
Mermaid 文件处理器模块

本模块提供一个自定义日志处理器，将 FlowEvent 对象写入 Mermaid (.mmd) 文件。
它负责 Mermaid 语法格式化、文件头处理，并确保线程安全的文件写入。
通过使用 Mixin 模式，将 Mermaid 逻辑无缝集成到标准的轮转处理器中。
"""

import logging
import logging.handlers
import os
from typing import Any, Optional, TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from mermaid_trace.core.formatter import MermaidFormatter

class MermaidHandlerMixin:
    """
    为日志处理器提供 Mermaid 特定逻辑的混入类。
    """
    title: str
    terminator: str
    # 这些属性由 logging.Handler 或其子类提供
    formatter: Optional[logging.Formatter]
    stream: Any

    def _write_header(self) -> None:
        """
        向文件写入初始的 Mermaid 语法行。
        """
        # 默认头部定义
        header = f"sequenceDiagram\n    title {self.title}\n    autonumber\n\n"

        # 如果关联的格式化程序提供了定制头部，则优先使用
        if self.formatter and hasattr(self.formatter, "get_header"):
            try:
                # 使用 getattr 动态调用以通过类型检查
                header = getattr(self.formatter, "get_header")(self.title)
                # 安全检查：确保头部以换行符结尾
                if not header.endswith("\n"):
                    header += "\n"
            except Exception:
                pass

        if self.stream:
            self.stream.write(header)
            # 立即刷新，确保头部先行写入磁盘
            self.stream.flush()

    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录并将其写入 Mermaid 文件。
        如果父类支持，则在此处处理轮转逻辑。
        """
        # 只处理包含结构化追踪数据的记录
        if not hasattr(record, "flow_event"):
            return

        try:
            # 1. 处理轮转 (适用于 RotatingFileHandler 和 TimedRotatingFileHandler)
            if hasattr(self, "shouldRollover") and getattr(self, "shouldRollover")(record):
                getattr(self, "doRollover")()

            # 2. 确保文件流已打开（处理 delay=True 的情况）
            if self.stream is None:
                if hasattr(self, "_open"):
                    self.stream = getattr(self, "_open")()

            # 3. 检查是否需要写入头部（仅对空文件写入一次）
            # 如果文件指针在 0 位置，说明是新文件、空文件或刚刚轮转后的文件
            if self.stream and hasattr(self.stream, "tell") and self.stream.tell() == 0:
                self._write_header()

            # 4. 格式化记录。
            # 注意：对于正在折叠的重复调用，msg 可能为空字符串。
            if hasattr(self, "format"):
                msg = getattr(self, "format")(record)
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
                    # 注意：我们这里不调用 self.flush()，以便让 Formatter 的折叠缓存正常工作
        except Exception:
            if hasattr(self, "handleError"):
                getattr(self, "handleError")(record)

    def flush(self) -> None:
        """
        同时刷新文件流和格式化程序中的缓冲事件。
        """
        if self.formatter and hasattr(self.formatter, "flush"):
            try:
                # 显式刷出 Formatter 中最后缓存的折叠块
                msg = getattr(self.formatter, "flush")()
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
            except Exception:
                pass

        # 确保调用父类的 flush
        super_flush = getattr(super(), "flush", None)
        if callable(super_flush):
            super_flush()

    def close(self) -> None:
        """
        安全关闭处理器，确保所有缓冲数据已持久化。
        """
        self.flush()
        super_close = getattr(super(), "close", None)
        if callable(super_close):
            super_close()


class MermaidFileHandler(MermaidHandlerMixin, logging.FileHandler):
    """
    将 `FlowEvent` 对象写入 Mermaid (.mmd) 文件的标准处理器。
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ):
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(filename, mode, encoding, delay)
        self.title = title
        self.terminator = "\n"


class RotatingMermaidFileHandler(
    MermaidHandlerMixin, logging.handlers.RotatingFileHandler
):
    """
    支持按大小轮转的 Mermaid 文件处理器。
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: str = "utf-8",
        delay: bool = False,
    ):  # noqa: PLR0913
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.title = title
        self.terminator = "\n"


class TimedRotatingMermaidFileHandler(
    MermaidHandlerMixin, logging.handlers.TimedRotatingFileHandler
):
    """
    支持按时间轮转的 Mermaid 文件处理器。
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        when: str = "h",
        interval: int = 1,
        backupCount: int = 0,
        encoding: str = "utf-8",
        delay: bool = False,
        utc: bool = False,
        atTime: Any = None,
        errors: Any = None,
    ):  # noqa: PLR0913
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime, errors
        )
        self.title = title
        self.terminator = "\n"
```