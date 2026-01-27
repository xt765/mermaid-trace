# 文件: src/mermaid_trace/handlers/mermaid_handler.py

## 概览
`mermaid_handler.py` 模块提供了一个自定义的日志处理器 `MermaidFileHandler`。它的主要职责是将追踪到的事件持久化到 `.mmd` 文件中，并确保生成的每一份文件都是符合 Mermaid 语法的合法文档。

## 核心功能分析

### 1. `MermaidFileHandler` 类
继承自标准库的 `logging.FileHandler`，从而复用了成熟的线程安全写入和缓冲机制。

- **设计策略**:
    - **自动头部管理**: 在写入第一条日志前，它会自动检查文件状态。如果是新文件或空文件（`tell() == 0`），会先写入 Mermaid 的头部定义（如 `sequenceDiagram`, `title`, `autonumber`）。
    - **延迟初始化**: 支持 `delay=True`。这意味着只有在产生第一条追踪日志时才会真正创建或打开文件，避免产生空的 `.mmd` 文件。
    - **目录自动创建**: 在初始化时会自动检查并创建目标文件所在的目录。
    - **换行符管理**: 显式设置 `self.terminator = "\n"`，确保在所有平台（包括 Windows）上生成的 Mermaid 文件都能保持正确的行分割，防止语法错误。

### 2. 关键方法
- **`_write_header`**: 负责写入图表起始语法。它会优先尝试调用格式化程序 (`formatter`) 的 `get_header` 方法，这允许不同的格式化程序定制自己的头部。
- **`emit`**: 核心写入逻辑。
    - 检查 `LogRecord` 是否包含 `flow_event`。
    - 检查当前文件指针位置。如果是 0，则调用 `_write_header`。
    - 调用 `self.format(record)` 获取格式化后的字符串。注意：如果 `MermaidFormatter` 正在折叠事件，此处可能返回空字符串，此时处理器不执行写入。
- **`flush`**: 
    - 这是一个增强版的刷新方法。它首先会尝试调用格式化程序的 `flush()` 方法。
    - **为什么？**: 因为智能折叠机制会缓冲事件。当我们需要确保所有交互都已写入磁盘（例如在程序结束前）时，必须先将 Formatter 缓冲区中最后的折叠块“挤”出来并写入文件。
- **`close`**: 在关闭文件前显式调用 `flush()`，确保所有缓冲数据不丢失。

## 源代码与中文注释

```python
"""
Mermaid 文件处理器模块

本模块提供一个自定义日志处理器，将 FlowEvent 对象写入 Mermaid (.mmd) 文件。
它负责 Mermaid 语法格式化、文件头处理，并确保线程安全的文件写入。
"""

import logging
import os


class MermaidFileHandler(logging.FileHandler):
    """
    一个自定义日志处理器，将 `FlowEvent` 对象写入 Mermaid (.mmd) 文件。

    策略与优化：
    1. 继承：继承自 `logging.FileHandler`，利用标准库提供的稳健、线程安全的文件写入能力。
    2. 头部管理：自动处理 Mermaid 文件头，确保输出文件是合法的 Mermaid 文档。
    3. 延迟初始化：文件打开和头部写入会推迟到发出第一条日志时，支持 `delay=True`。
    4. 智能刷新：与有状态的格式化程序配合，确保折叠的事件能被正确刷出。
    """

    def __init__(
        self,
        filename: str,
        title: str = "Log Flow",
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ):
        """
        初始化 Mermaid 文件处理器。
        """
        # 确保目录存在，防止打开文件时抛出 FileNotFoundError
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)

        super().__init__(filename, mode, encoding, delay)
        self.title = title
        # 显式设置换行符，确保 Mermaid 语法行分割正确
        self.terminator = "\n"

    def _write_header(self) -> None:
        """
        向文件写入初始的 Mermaid 语法行。
        """
        # 默认头部定义
        header = f"sequenceDiagram\n    title {self.title}\n    autonumber\n\n"

        # 如果关联的格式化程序提供了定制头部，则优先使用
        if self.formatter and hasattr(self.formatter, "get_header"):
            try:
                header = self.formatter.get_header(self.title)
                # 安全检查：确保头部以换行符结尾，防止与第一条日志粘连
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
        """
        # 只处理包含结构化追踪数据的记录
        if hasattr(record, "flow_event"):
            # 确保文件流已打开（处理 delay=True 的情况）
            if self.stream is None:
                self.stream = self._open()

            # 检查是否需要写入头部（仅对空文件写入一次）
            if self.stream.tell() == 0:
                self._write_header()

            # 调用格式化程序。注意：对于正在折叠的重复调用，msg 可能为空字符串。
            msg = self.format(record)
            if msg:
                if self.stream:
                    # 写入格式化后的行，并追加换行符
                    self.stream.write(msg + self.terminator)
                    # 注意：此处不调用 self.flush() 是为了性能考虑，
                    # 真正的刷新由系统缓冲区或显式的 flush() 调用完成。

    def flush(self) -> None:
        """
        强制刷新文件流，并确保格式化程序中的缓冲事件也被写出。
        """
        # 1. 首先尝试从有状态的格式化程序中“挤出”最后缓冲的事件
        if self.formatter and hasattr(self.formatter, "flush"):
            try:
                msg = self.formatter.flush()
                if msg and self.stream:
                    self.stream.write(msg + self.terminator)
            except Exception:
                pass

        # 2. 调用标准库的 flush 确保数据从 OS 缓冲区写入物理磁盘
        super().flush()

    def close(self) -> None:
        """
        安全关闭处理器，确保所有缓冲数据已持久化。
        """
        self.flush()
        super().close()
```