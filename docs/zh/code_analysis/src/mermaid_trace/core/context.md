# src/mermaid_trace/core/context.py 代码分析

## 文件概览 (File Overview)
`src/mermaid_trace/core/context.py` 是整个库的"大脑记忆区"。它负责管理当前的执行上下文（Context），比如"当前是谁在调用函数"（Participant）。
它解决了在异步（AsyncIO）和多线程环境中，如何安全地跟踪函数调用链的问题。

## 核心概念 (Key Concepts)

*   **ContextVar (上下文变量)**: Python 3.7+ 引入的神器。它像全局变量，但每个线程或异步任务看到的变量值是独立的。这对于在并发环境中跟踪请求 ID 或当前用户至关重要。
*   **Thread-Local Storage (TLS)**: 线程局部存储，旧时代的解决方案，只对线程有效，对 `asyncio` 任务无效。这里我们用 `ContextVar` 替代了它。
*   **Copy-on-Write (写时复制)**: 一种优化策略。当我们想修改上下文时，不直接修改原对象，而是复制一份新的修改。这保证了父任务的上下文不会被子任务意外污染。

## 代码详解 (Code Walkthrough)

```python
from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator

class LogContext:
    """
    管理全局上下文信息用于日志记录（例如：request_id, user_id, current_participant）。
    
    这个类提供了一种线程安全且异步安全（async-safe）的机制来存储和检索
    上下文数据，而无需显式地将它们作为参数传递给每个函数。

    **问题 (The Problem):**
    在现代异步/多线程应用程序中，将 `request_id` 或 `user_id` 等元数据
    沿调用栈向下传递给每个函数既繁琐又容易出错，还会使 API 变得混乱。

    **解决方案：上下文变量 (The Solution: Context Variables)**
    这个类利用 Python 的 `contextvars` 模块来存储特定于执行上下文（线程或 asyncio 任务）的"本地"数据。
    它的行为类似于线程局部存储 (TLS)，但完全兼容 asyncio 的事件循环。

    **关键概念 (Key Concepts):**
    1. **上下文隔离 (Context Isolation):** 一个请求/任务中设置的数据对其他请求不可见。
    2. **写时复制 (Copy-on-Write, COW):** 确保分支任务安全地继承上下文，而不会
       污染父级上下文或兄弟任务。
    3. **作用域 (Scopes):** 可以使用上下文管理器 (`with` 或 `async with`) 
       针对特定代码块临时修改上下文，之后自动恢复更改。
    """
    
    # 底层存储机制。
    # `ContextVar` 是原生 Python 功能 (自 3.7 起)。
    # 它创建一个自动跟踪当前执行上下文的变量。
    # 默认值未在此处设置；我们在 `_get_store` 中处理空情况。
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        检索当前任务/线程的上下文及其字典。
        如果尚不存在，则返回一个新的空字典。
        """
        try:
            return cls._context_store.get()
        except LookupError:
            # 如果未设置上下文，返回空字典。
            # 注意：我们这里不把它设置回 store，以避免不必要的写入，直到实际添加数据为止。
            return {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        使用写时复制原则安全地设置单个上下文变量。

        **深入解析：写时复制 (COW)**
        为什么我们在更改之前复制字典？
        
        想象 `Task A` 设置了一个上下文。`Task B` 从 `Task A` 生成并继承了
        上下文对象引用。如果 `Task B` 原地修改了字典，`Task A` 也会看到这些更改！
        这会导致"上下文污染"和难以调试的竞争条件。
        
        通过复制：
        1. 获取当前状态。
        2. 创建浅拷贝（内存中的新对象）。
        3. 修改副本。
        4. 将副本绑定为*此*任务的*新*上下文。
        
        父任务保留对其原始字典的引用。
        """
        # 1. 获取当前数据
        # 2. .copy() 创建内存中的新字典对象（快照）
        ctx = cls._get_store().copy()
        
        # 3. 更新新对象
        ctx[key] = value
        
        # 4. 将新对象绑定到当前 ContextVar
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        使用写时复制一次更新多个上下文变量。
        这比多次调用 `set()` 更高效。
        """
        if not data:
            return
            
        ctx = cls._get_store().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """检索特定的上下文变量。"""
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        检索所有当前上下文变量的快照。
        返回副本以防止外部代码意外修改内部状态。
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        用于临时上下文更新的同步上下文管理器。
        
        这允许你设置仅在 `with` 块内存在的上下文变量。
        一旦退出该块（正常或通过异常），上下文将恢复到之前的状态。
        
        **用法:**
        ```python
        with LogContext.scope({"process": "payment"}):
            # 这里的上下文包含 "process": "payment"
            process_payment()
        # 这里的上下文恢复到原始状态（process 键被移除或恢复）
        ```
        """
        # 1. 准备新状态 (手动应用写时复制逻辑)
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        
        # 2. 设置新状态并获取恢复令牌 (Token)
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            # 3. 使用令牌恢复之前的状态
            cls._context_store.reset(token)

    @classmethod
    @asynccontextmanager
    async def ascope(cls, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        用于临时上下文更新的异步上下文管理器。
        逻辑与 `scope` 相同，但兼容 `async with` 语句。
        """
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        获取当前活动参与者的辅助方法（用于序列图）。
        这用于确定"谁"在调用函数。如果未显式设置，默认为 'Unknown'。
        """
        return str(cls.get("participant", "Unknown"))

    @classmethod
    def set_participant(cls, name: str) -> None:
        """设置当前参与者名称。"""
        cls.set("participant", name)
```

## 新手指南 (Beginner's Guide)

*   **为什么要复制字典 (`.copy()`)？**
    这是一个常见的坑。如果不复制，所有共享同一个字典引用的任务都会互相干扰。比如你在处理请求 A 时修改了字典，正在处理请求 B 的任务也会看到这个修改，这在并发编程中是灾难性的。

*   **`Token` 是什么？**
    `ContextVar.set()` 不仅设置新值，还返回一个 `Token`。这个 Token 就像游戏里的"存档点"。当你调用 `reset(token)` 时，变量的值会瞬间回滚到拿到这个 Token 时的状态。这就是 `scope` 上下文管理器实现"退出时自动恢复"的原理。

*   **什么时候用 `scope` vs `ascope`？**
    *   如果你在普通函数 (`def`) 里，用 `with LogContext.scope(...)`。
    *   如果你在异步函数 (`async def`) 里，用 `async with LogContext.ascope(...)`。
