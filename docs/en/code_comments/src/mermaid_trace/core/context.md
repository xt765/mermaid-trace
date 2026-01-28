# File: src/mermaid_trace/core/context.py

## Overview
The `context.py` module provides a thread-safe and async-friendly context management system. It is the core for tracking caller/callee relationships, ensuring that tracing information (such as `trace_id` and current participant) is correctly propagated in complex asynchronous call or multi-threaded environments.

## Core Functionality Analysis

### 1. `LogContext` Class
This class utilizes Python's `contextvars.ContextVar` mechanism to manage global context information (such as `request_id`, `user_id`, `participant`, etc.).

- **Why use `ContextVar`?**
    - Unlike `threading.local()`, `ContextVar` natively supports Python's `async/await` event loop.
    - It ensures context remains consistent between `await` suspension points while maintaining isolation between concurrent tasks.

### 2. Key Design Pattern: Copy-Update-Set
Since objects stored in `ContextVar` should be isolated across different contexts, `LogContext` follows this pattern to modify context:
1. **Get**: Retrieve the current dictionary.
2. **Copy**: Create a shallow copy (`copy()`) of the dictionary to prevent accidental modification of parent or other parallel contexts.
3. **Update**: Modify data on the copy.
4. **Set**: Set the new dictionary back to `ContextVar`.

### 3. Scope Management (`scope` and `ascope`)
- **Synchronous `scope`**: Uses `with` statement to temporarily change context. After block ends, context automatically reverts to pre-entry state.
- **Asynchronous `ascope`**: Designed for `async with`, ensuring task context remains consistent even if coroutine is suspended.
- **Token Mechanism**: Internally uses `Token` returned by `ContextVar.set()` to precisely restore context, which is safer and more efficient than manually deleting keys. More granular control is possible through `set_all` and `reset` methods.

### 4. Lazy Initialization of Trace ID (`current_trace_id`)
If `trace_id` doesn't exist in current context, it automatically generates a UUIDv4 and stores it in context. This ensures:
- A valid value is always returned when requesting trace ID.
- All logs in the same execution flow share the same ID, correlating them in Mermaid diagrams.
- Supports injection of existing trace ID from external sources (e.g., HTTP Header) via `set_trace_id`.

## Source Code with English Comments

```python
"""
Log context management module

This module provides a thread-safe, async-friendly context management system for tracking execution context throughout the application.
It uses Python's ContextVar mechanism to ensure proper context propagation in both synchronous and asynchronous environments.
"""

from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator
import uuid


class LogContext:
    """
    Manages global context information for logging (e.g., request_id, user_id, current_participant).

    This class utilizes `contextvars.ContextVar` to ensure thread safety and proper propagation in asyncio environments.
    Unlike `threading.local()`, `ContextVar` natively supports Python's async/await event loop.
    """

    # ContextVar stores a unique dictionary for each execution context (task/thread)
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        Retrieve the current context dictionary. If not yet set, creates an empty dictionary.
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
        Set a specific key-value pair in the current context. Follows copy-modify-set pattern.
        """
        ctx = cls._get_store().copy()
        ctx[key] = value
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        Update multiple keys in the current context at once.
        """
        if not data:
            return
        ctx = cls._get_store().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Safely retrieve value from current context.
        """
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get a complete copy of the current context dictionary.
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        Synchronous context manager for temporarily updating context.
        Automatically restores previous state on exit using Token.
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
        Asynchronous context manager for temporarily updating context in coroutines.
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
        Replace entire context with provided data. Returns Token for subsequent restoration.
        """
        return cls._context_store.set(data.copy())

    @classmethod
    def reset(cls, token: Token[Dict[str, Any]]) -> None:
        """
        Manually restore context using Token.
        """
        cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        Get the name of the currently active participant (object/module). Defaults to 'Unknown'.
        """
        return str(cls.get("participant", "Unknown"))

    @classmethod
    def set_participant(cls, name: str) -> None:
        """
        Manually set current participant name.
        """
        cls.set("participant", name)

    @classmethod
    def current_trace_id(cls) -> str:
        """
        Retrieve current trace ID. If not present, lazily generates a new ID.
        """
        tid = cls.get("trace_id")
        if not tid:
            tid = str(uuid.uuid4())
            cls.set("trace_id", tid)
        return str(tid)

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        """
        Manually set trace ID (e.g., parsed from HTTP Header).
        """
        cls.set("trace_id", trace_id)
```