# 文件: src/mermaid_trace/handlers/mermaid_handler.py

## 概览
本文件实现了 `MermaidFileHandler`，这是一个专门用于写入 `.mmd` 文件的日志处理器。它继承自 Python 标准库的 `logging.FileHandler`，从而复用了其健壮的文件锁定和缓冲机制。

## 核心功能分析

### Header 管理策略
Mermaid 文件必须以特定的 Header（如 `sequenceDiagram`）开头才能被正确渲染。
-   **覆盖模式 ('w')**: 总是写入 Header。
-   **追加模式 ('a')**: 仅当文件不存在或为空时写入 Header。这防止了在追加日志时重复写入 Header，导致生成无效的 Mermaid 文件。
-   **延迟写入 (delay=True)**: 如果启用了延迟打开，它会等到第一条日志到来时才检查并写入 Header。

### 性能优化
在 `emit` 方法中，它首先检查日志记录是否有 `flow_event` 属性。这是一个快速过滤机制：如果某些标准库日志（如 `requests` 或 `urllib` 的调试日志）意外进入了这个 Handler，它们会被直接忽略，从而避免不必要的格式化开销和文件污染。

## 源代码与中文注释

```python
import logging
import os

class MermaidFileHandler(logging.FileHandler):
    """
    自定义日志处理器，将 `FlowEvent` 对象写入 Mermaid (.mmd) 文件。
    
    策略与优化:
    1. **继承**: 继承自 `logging.FileHandler` 以利用标准库提供的健壮、
       线程安全的文件写入能力（锁定、缓冲）。
    2. **头部管理**: 自动处理 Mermaid 文件头
       (`sequenceDiagram`, `title`, `autonumber`) 以确保输出文件
       是有效的 Mermaid 文档。它智能地检测文件是新建的还是被追加的。
    3. **延迟格式化**: 实际的字符串转换发生在 `emit` 方法中
       （通过格式化程序），使处理器专注于 I/O。
    """
    
    def __init__(self, filename: str, title: str = "Log Flow", mode: str = 'a', encoding: str = 'utf-8', delay: bool = False):
        """
        初始化处理器。
        
        参数:
            filename (str): 输出 .mmd 文件的路径。
            title (str): Mermaid 图表的标题（写入头部）。
            mode (str): 文件打开模式。'w' (覆盖) 或 'a' (追加)。
            encoding (str): 文件编码。默认为 'utf-8'。
            delay (bool): 如果为 True，文件打开推迟到第一次调用 emit。
                          用于避免在没有发生日志记录时创建空文件。
        """
        # 确保目录存在以防止打开时出现 FileNotFoundError
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)
        
        # 头部策略:
        # 我们仅在以下情况下需要写入 "sequenceDiagram" 前言:
        # 1. 我们正在覆盖文件 (mode='w')。
        # 2. 我们正在追加 (mode='a')，但文件不存在或为空。
        # 这可以防止无效的 Mermaid 文件（例如，多个 "sequenceDiagram" 行）。
        should_write_header = False
        if mode == 'w':
            should_write_header = True
        elif mode == 'a':
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                should_write_header = True
        
        # 初始化标准 FileHandler（除非 delay=True，否则打开文件）
        super().__init__(filename, mode, encoding, delay)
        self.title = title
        
        # 如果需要，立即写入头部。
        if should_write_header:
            self._write_header()

    def _write_header(self) -> None:
        """
        写入初始 Mermaid 语法行到文件。
        
        此设置是 Mermaid JS 或 Live Editor 正确渲染图表所必需的。
        它定义：
        - 图表类型 (sequenceDiagram)
        - 图表标题
        - 步骤自动编号
        
        线程安全：使用处理器的内部锁来防止在 delay=True 时并发写入，
        确保头部只被写入一次。
        """
        # 使用处理器的内部锁确保线程安全
        with self.lock:
            # 如果流可用，则直接写入，否则暂时打开
            if self.stream:
                # 流已经打开（delay=False 或已调用 emit()）
                self.stream.write("sequenceDiagram\n")
                self.stream.write(f"    title {self.title}\n")
                self.stream.write("    autonumber\n")
                # Flush 确保头部立即写入磁盘，
                # 这样即使程序紧接着崩溃，它也会出现。
                self.flush()
            else:
                # 处理 'delay=True' 情况：文件尚未打开
                # 暂时打开文件只是为了写入头部
                # 这确保了即使应用程序在第一条日志之前崩溃，文件也是有效的。
                with open(self.baseFilename, self.mode, encoding=self.encoding) as f:
                    f.write("sequenceDiagram\n")
                    f.write(f"    title {self.title}\n")
                    f.write("    autonumber\n")

    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录。
        
        优化:
        - 首先检查 `flow_event` 属性。这允许此处理器
          附加到根日志记录器而不处理不相关的系统日志。
          它充当格式化之前的高性能过滤器。
        - 将实际写入委托给 `super().emit()`，它安全地处理
          线程锁定和流刷新。
        """
        # 仅处理包含我们结构化 FlowEvent 数据的记录
        if hasattr(record, 'flow_event'):
            super().emit(record)
```
