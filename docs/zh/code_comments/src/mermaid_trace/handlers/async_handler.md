# 文件: src/mermaid_trace/handlers/async_handler.py

## 概览
本文件实现了 `AsyncMermaidHandler`，这是一个高性能的日志处理器包装器。它的主要目的是将文件 I/O 操作从主应用程序线程中移除，从而消除日志记录对业务逻辑性能的影响。

## 核心功能分析

### 生产者-消费者模型
-   **生产者**：应用程序线程调用 `logger.info()` 时，`AsyncMermaidHandler`（继承自 `QueueHandler`）仅仅将日志记录放入一个内存队列 (`queue.Queue`)。这是一个极快的操作（微秒级）。
-   **消费者**：`QueueListener` 运行在一个独立的后台线程中。它不断从队列中取出日志记录，并调用目标处理器（如 `MermaidFileHandler`）的 `emit` 方法执行实际的磁盘写入。

### 优雅退出 (`atexit`)
为了防止程序退出时队列中仍有未写入的日志导致数据丢失，该类注册了一个 `atexit` 钩子。当 Python 解释器即将关闭时，它会调用 `stop()` 方法，停止监听器并强制刷新队列中的剩余日志到磁盘。

## 源代码与中文注释

```python
import logging
import logging.handlers
import queue
import atexit
from typing import List, Optional


class AsyncMermaidHandler(logging.handlers.QueueHandler):
    """
    使用后台线程写入日志的非阻塞日志处理器。

    此处理器将日志记录推送到队列，然后由运行在单独线程中的
    QueueListener 获取并分发到实际的处理器（例如 MermaidFileHandler）。
    """

    def __init__(self, handlers: List[logging.Handler], queue_size: int = -1):
        """
        初始化异步处理器。
        
        参数:
            handlers: 应从队列接收日志的处理器列表。
                      (例如 [MermaidFileHandler(...)])
            queue_size: 队列的最大大小。-1 表示无限。
        """
        self._log_queue: queue.Queue[logging.LogRecord] = queue.Queue(queue_size)
        super().__init__(self._log_queue)
        
        # 初始化 QueueListener
        # 它会启动一个内部线程来监控队列
        # respect_handler_level=True 确保目标处理器的日志级别被遵守
        self._listener: Optional[logging.handlers.QueueListener] = logging.handlers.QueueListener(
            self._log_queue, 
            *handlers, 
            respect_handler_level=True
        )
        self._listener.start()
        
        # 确保在退出时停止监听器并刷新队列
        # 这防止了程序结束时丢失最后几条日志
        atexit.register(self.stop)

    def stop(self) -> None:
        """
        停止监听器并刷新队列。

        这通过 `atexit` 注册，以确保所有挂起的日志
        在应用程序终止之前写入磁盘。
        """
        if self._listener:
            self._listener.stop()
            self._listener = None
```
