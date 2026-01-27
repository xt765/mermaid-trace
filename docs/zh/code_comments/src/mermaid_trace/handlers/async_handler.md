# 文件: src/mermaid_trace/handlers/async_handler.py

## 概览
`async_handler.py` 模块实现了一个非阻塞的日志处理器。它采用生产者-消费者模式，利用后台线程和队列机制来处理日志记录。这种设计对于高性能应用至关重要，因为它确保了主执行线程不会因为等待磁盘 I/O（写入文件）而产生延迟。

## 核心架构分析

### 1. 设计模式：生产者-消费者
- **生产者 (AsyncMermaidHandler)**: 运行在主应用线程中。它的任务是快速拦截日志记录并将其丢入队列，然后立即返回，让业务代码继续执行。
- **中间件 (Queue)**: 一个线程安全的先进先出 (FIFO) 缓冲区。它负责在高并发压力下缓冲日志，防止日志丢失。
- **消费者 (QueueListener)**: 运行在独立的后台守护线程中。它不断从队列中取出日志，并分发给真正的处理器（如 `MermaidFileHandler`）进行持久化。

### 2. 关键特性
- **非阻塞 I/O**: 主线程只进行极快的内存操作（入队），而不进行慢速的磁盘写入。
- **应对突发流量**: 队列充当了“蓄水池”，能够吸收瞬时的大量追踪日志。
- **优雅停机与强制刷新**: 
    - 通过注册 `atexit` 钩子，在程序退出时自动调用 `stop()`。
    - `stop()` 不仅会停止后台线程并处理完队列中的剩余日志，还会显式调用底层所有 Handler 的 `flush()` 方法。
    - **为什么需要显式 flush？**: 因为 `MermaidFormatter` 是有状态的（支持智能折叠），某些事件可能还在 Formatter 的缓冲区中未转换成字符串。显式 `flush()` 确保了这些最后被折叠的交互能正确写入文件。
- **背压 (Backpressure) 处理**: 如果队列满了（通常意味着消费者太慢），`emit` 方法会尝试等待 0.1 秒。如果依然无法入队，则会丢弃该日志并向 `stderr` 打印警告，从而优先保证主程序的稳定性。

### 3. 使用场景
当追踪粒度非常细（函数调用极其频繁）或文件写入速度较慢（如写入网络文件系统）时，强烈建议开启异步模式。

## 源代码与中文注释

```python
"""
异步 Mermaid 处理器模块

本模块实现了一个非阻塞的日志处理器，利用后台线程和队列机制处理日志。
"""

import logging
import logging.handlers
import queue
import atexit
from typing import List, Optional, cast


class AsyncMermaidHandler(logging.handlers.QueueHandler):
    """
    使用生产者-消费者模式的高性能非阻塞日志处理器。
    """

    def __init__(self, handlers: List[logging.Handler], queue_size: int = 1000):
        """
        初始化异步处理器架构。
        1. 创建一个有界队列（缓冲区）。
        2. 初始化父类 QueueHandler。
        3. 启动后台 QueueListener 线程。
        """
        # 1. 创建有界队列，防止内存无限增长
        self._log_queue: queue.Queue[logging.LogRecord] = queue.Queue(queue_size)
        self._queue_size = queue_size

        # 2. 初始化父类，配置 emit 将日志发送到该队列
        super().__init__(self._log_queue)

        # 3. 初始化并启动后台监听器（消费者）
        # respect_handler_level=True 确保尊重底层处理器的日志级别设置
        self._listener: Optional[logging.handlers.QueueListener] = (
            logging.handlers.QueueListener(
                self._log_queue, *handlers, respect_handler_level=True
            )
        )
        self._listener.start()

        # 4. 注册退出钩子，确保程序退出时能优雅关闭并刷新队列
        atexit.register(self.stop)

    def emit(self, record: logging.LogRecord) -> None:
        """
        将日志记录放入队列（生产者动作）。
        """
        try:
            queue_instance = cast(queue.Queue[logging.LogRecord], self.queue)

            # 尝试入队，设置 0.1s 超时。
            # 这在“尽量保存日志”和“不冻结主程序”之间取得了平衡。
            queue_instance.put(record, block=True, timeout=0.1)

        except queue.Full:
            # 如果队列溢出，为了保证应用稳定性，不得不丢弃日志。
            if record.levelno >= logging.WARNING:
                # 使用 print 避免递归调用日志系统
                print(
                    f"警告: AsyncMermaidHandler 队列已满 (容量: {self._queue_size}), "
                    f"正在丢弃日志记录: {record.msg}"
                )

    def stop(self) -> None:
        """
        清理资源并刷新待处理的日志。
        此方法会向队列发送结束信号，并等待后台线程处理完所有剩余任务。
        """
        if self._listener:
            # 保存处理器引用，以便在监听器停止后刷新它们
            handlers = self._listener.handlers
            try:
                # 停止监听器。这会阻塞直到后台线程处理完队列中的所有记录并退出。
                self._listener.stop()
                self._listener = None

                # 关键步骤：显式刷新所有底层处理器。
                # 某些有状态的 Formatter（如 MermaidFormatter 的智能折叠）可能缓存了部分输出。
                for handler in handlers:
                    try:
                        handler.flush()
                    except Exception:
                        pass
            except Exception:
                # 忽略退出过程中的异常（例如某些模块已提前卸载）
                pass
```
