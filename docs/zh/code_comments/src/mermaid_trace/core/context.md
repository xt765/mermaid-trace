# 文件: src/mermaid_trace/core/context.py

## 概览
`context.py` 模块提供了线程安全且异步友好的上下文管理系统。它是追踪调用者/被调用者关系的核心，确保在复杂的异步调用或多线程环境下，追踪信息（如 `trace_id` 和当前参与者）能够正确传播。

## 核心功能分析

### 1. `LogContext` 类
该类利用 Python 的 `contextvars.ContextVar` 机制来管理全局上下文信息（如 `request_id`、`user_id`、`participant` 等）。

- **为什么使用 `ContextVar`？**
    - 与 `threading.local()` 不同，`ContextVar` 原生支持 Python 的 `async/await` 事件循环。
    - 它能确保上下文在 `await` 挂起点之间保持不变，同时在并发任务之间保持隔离。

### 2. 关键设计模式：复制-更新-设置 (Copy-Update-Set)
由于 `ContextVar` 存储的对象在不同上下文中应该是隔离的，`LogContext` 遵循以下模式来修改上下文：
1. **获取**: 检索当前字典。
2. **复制**: 创建字典的浅拷贝（`copy()`），防止意外修改父级或其他并行的上下文。
3. **更新**: 在拷贝上修改数据。
4. **设置**: 将新字典设置回 `ContextVar`。

### 3. 作用域管理 (`scope` 和 `ascope`)
- **同步 `scope`**: 使用 `with` 语句临时改变上下文。块结束后，上下文会自动恢复到进入前的状态。
- **异步 `ascope`**: 专为 `async with` 设计，确保即使协程挂起，该任务的上下文也保持一致。
- **Token 机制**: 内部使用 `ContextVar.set()` 返回的 `Token` 来精确还原上下文，这比手动删除键更安全、更高效。通过 `set_all` 和 `reset` 方法可以更细粒度地控制这一过程。

### 4. 追踪 ID 的延迟初始化 (`current_trace_id`)
如果当前上下文中不存在 `trace_id`，它会自动生成一个 UUIDv4 并存入上下文。这保证了：
- 任何时候请求追踪 ID 都能得到一个有效值。
- 同一执行流中的所有日志都会共享同一个 ID，从而在 Mermaid 图表中关联起来。
- 支持通过 `set_trace_id` 从外部（如 HTTP Header）注入已有的追踪 ID。

## 源代码与中文注释

```python
"""
日志上下文管理模块

本模块提供了一个线程安全、异步友好的上下文管理系统，用于在整个应用程序中跟踪执行上下文。
它使用 Python 的 ContextVar 机制，确保在同步和异步环境中都能正确传播上下文。
"""

from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator
import uuid


class LogContext:
    """
    管理日志的全局上下文信息（例如 request_id, user_id, current_participant）。

    此类利用 `contextvars.ContextVar` 来确保线程安全以及在异步 (asyncio) 环境中的正确传播。
    与 `threading.local()` 不同，`ContextVar` 原生支持 Python 的异步/等待事件循环。
    """

    # ContextVar 存储当前执行上下文（任务/线程）唯一的字典
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        检索当前的上下文字典。如果尚未设置，则创建一个空字典。
        """
        try:
            return cls._context_store.get()
        except LookupError:
            empty_dict: Dict[str, Any] = {}
            cls._context_store.set(empty_dict)
            return empty_dict

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        在当前上下文中设置特定的键值对。遵循 复制-修改-设置 模式。
        """
        ctx = cls._get_store().copy()
        ctx[key] = value
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        一次性更新当前上下文中的多个键。
        """
        if not data:
            return
        ctx = cls._get_store().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        安全地从当前上下文中检索值。
        """
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        获取当前上下文字典的完整拷贝。
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        用于临时更新上下文的同步上下文管理器。
        退出时会利用 Token 自动恢复之前的状态。
        """
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            cls._context_store.reset(token)

    @classmethod
    @asynccontextmanager
    async def ascope(cls, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        用于在协程中临时更新上下文的异步上下文管理器。
        """
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            cls._context_store.reset(token)

    @classmethod
    def set_all(cls, data: Dict[str, Any]) -> Token[Dict[str, Any]]:
        """
        用提供的数据替换整个上下文。返回一个 Token 用于后续恢复。
        """
        return cls._context_store.set(data.copy())

    @classmethod
    def reset(cls, token: Token[Dict[str, Any]]) -> None:
        """
        使用 Token 手动恢复上下文。
        """
        cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        获取当前活跃的参与者（对象/模块）名称。默认为 'Unknown'。
        """
        return str(cls.get("participant", "Unknown"))

    @classmethod
    def set_participant(cls, name: str) -> None:
        """
        手动设置当前参与者名称。
        """
        cls.set("participant", name)

    @classmethod
    def current_trace_id(cls) -> str:
        """
        检索当前追踪 ID。如果不存在，则延迟生成一个新 ID。
        """
        tid = cls.get("trace_id")
        if not tid:
            tid = str(uuid.uuid4())
            cls.set("trace_id", tid)
        return str(tid)

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        """
        手动设置追踪 ID（例如从 HTTP Header 解析得到）。
        """
        cls.set("trace_id", trace_id)
```
