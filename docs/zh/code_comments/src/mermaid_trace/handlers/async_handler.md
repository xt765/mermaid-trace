# 文件: src/mermaid_trace/handlers/async_handler.py

## 概览
本文件实现了 `AsyncMermaidHandler`，这是一个高性能的日志处理器包装器。它的主要目的是将文件 I/O 操作从主应用程序线程中移除，从而消除日志记录对业务逻辑性能的影响。该处理器采用生产者-消费者模型，结合了队列大小限制和丢弃策略，以确保在高流量场景下的稳定性。

## 核心功能分析

### 生产者-消费者模型
- **生产者**：应用程序线程调用 `logger.info()` 时，`AsyncMermaidHandler`（继承自 `QueueHandler`）将日志记录放入一个内存队列 (`queue.Queue`)。
- **消费者**：`QueueListener` 运行在一个独立的后台线程中，不断从队列中取出日志记录，并调用目标处理器（如 `MermaidFileHandler`）执行实际的磁盘写入。

### 队列大小限制与丢弃策略
- 默认队列大小设置为 1000，防止内存溢出
- 当队列满时，采用超时机制（0.1秒）尝试写入
- 超时失败时，丢弃日志并打印警告，确保主应用程序不会阻塞

### 优雅退出 (`atexit`)
- 注册 `atexit` 钩子，确保程序退出时队列中的剩余日志被写入磁盘
- 防止程序意外崩溃时丢失数据

## 源代码与中文注释

```python
"""
异步 Mermaid 处理器模块

该模块提供了一个非阻塞的日志处理器，使用后台线程进行日志写入。
它旨在通过将日志 I/O 与主执行线程解耦，提高高吞吐量应用的性能。
"""
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
    
    该架构提供了几个优点：
    - 主线程不会因磁盘 I/O 而阻塞
    - 日志在后台处理
    - 在高吞吐量应用中具有更好的性能
    - 平滑处理突发流量
    """

    def __init__(
        self,
        handlers: List[logging.Handler],
        queue_size: int = 1000
    ):
        """
        初始化异步处理器。
        
        参数:
            handlers: 应从队列接收日志的处理器列表。
                      这些通常是 MermaidFileHandler 实例。
            queue_size: 队列的最大大小。默认为 1000。
                      如果队列填满，新的日志记录可能会被丢弃。
        """
        # 创建指定大小的有界队列
        self._log_queue: queue.Queue[logging.LogRecord] = queue.Queue(queue_size)
        self._queue_size = queue_size
        
        # 使用我们的队列初始化父类 QueueHandler
        super().__init__(self._log_queue)
        
        # 初始化 QueueListener 以处理队列中的记录
        # 它启动一个内部线程来监控队列
        # respect_handler_level=True 确保目标处理器的日志级别被遵守
        self._listener: Optional[logging.handlers.QueueListener] = logging.handlers.QueueListener(
            self._log_queue, 
            *handlers, 
            respect_handler_level=True
        )
        
        # 启动监听器线程
        self._listener.start()
        
        # 在程序退出时注册 stop 方法
        # 这确保了在终止前所有挂起的日志都被写入磁盘
        atexit.register(self.stop)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        使用超时和丢弃策略将日志记录发送到队列。
        
        如果队列已满，此方法将尝试在短时间超时后放入记录。
        如果失败，它将丢弃记录并打印警告。
        
        参数:
            record: 要发送的日志记录
        """
        try:
            # 尝试将记录放入队列，超时时间为 0.1 秒
            # 这防止了队列已满时主线程无限期阻塞
            self.queue.put(record, block=True, timeout=0.1)
        except queue.Full:
            # 如果队列已满，记录警告并丢弃记录
            if record.levelno >= logging.WARNING:
                # 避免使用 self.logger 导致无限递归
                print(f"WARNING: AsyncMermaidHandler 队列已满（大小: {self._queue_size}），丢弃日志记录: {record.msg}")

    def stop(self) -> None:
        """
        停止监听器并刷新队列中的所有挂起日志。

        此方法通过 `atexit` 注册，以确保在应用程序终止之前
        所有挂起的日志都被写入磁盘。
        """
        if self._listener:
            # 停止监听器 - 这将处理队列中所有剩余的记录
            self._listener.stop()
            self._listener = None
```
