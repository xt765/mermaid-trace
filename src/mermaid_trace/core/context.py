"""
Log Context Management Module

This module provides a thread-safe, async-friendly context management system
for tracking execution context across the application. It uses Python's ContextVar
mechanism to ensure proper context propagation in both synchronous and asynchronous
environments.
"""

from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator
import uuid


class LogContext:
    """
    Manages global context information for logging (e.g., request_id, user_id, current_participant).

    This class utilizes `contextvars.ContextVar` to ensure thread-safety and
    correct context propagation in asynchronous (asyncio) environments. Unlike
    `threading.local()`, `ContextVar` works natively with Python's async/await
    event loop, ensuring that context is preserved across `await` points but isolated
    between different concurrent tasks.
    """

    # ContextVar stores a dictionary unique to the current execution context (Task/Thread)
    # The name "log_context" is used for debugging purposes
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        Retrieves the current context dictionary.

        If the context variable has not been set in the current context,
        it creates a fresh empty dictionary, sets it to the contextvar,
        and returns it. This prevents LookupError and ensures there's
        always a valid dictionary to work with.

        Returns:
            Dict[str, Any]: Current context dictionary for the execution flow
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
        Sets a specific key-value pair in the current context.

        Important: ContextVars are immutable collections. To modify the context,
        we must:
        1. Retrieve the current dictionary using _get_store()
        2. Create a shallow copy to avoid affecting parent contexts
        3. Update the copy with the new key-value pair
        4. Re-set the ContextVar with the new dictionary

        Args:
            key (str): Name of the context variable to set
            value (Any): Value to associate with the key
        """
        ctx = cls._get_store().copy()
        ctx[key] = value
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        Updates multiple keys in the current context at once.

        This follows the same Copy-Update-Set pattern as `set()` to maintain
        context isolation between different execution flows.

        Args:
            data (Dict[str, Any]): Dictionary of key-value pairs to update in context
        """
        if not data:
            return
        ctx = cls._get_store().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Retrieves a value from the current context safely.

        Args:
            key (str): Name of the context variable to retrieve
            default (Any, optional): Default value if key doesn't exist. Defaults to None.

        Returns:
            Any: Value associated with the key, or default if key not found
        """
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Returns a copy of the entire context dictionary.

        Returns:
            Dict[str, Any]: Complete copy of the current context
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        Synchronous context manager for temporary context updates.

        Usage:
            with LogContext.scope({"user_id": 123}):
                # user_id is 123 here
                some_function()
            # user_id reverts to previous value (or disappears) here

        Mechanism:
            1. Copies current context and updates it with new data
            2. Sets the ContextVar to this new state, receiving a `Token`
            3. Yields control to the block
            4. Finally, uses the `Token` to reset the ContextVar to its exact state
               before the block entered

        Args:
            data (Dict[str, Any]): Dictionary of context values to set within the scope

        Yields:
            None: Control to the block using this context manager
        """
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            # Reset restores context to state before .set() was called
            cls._context_store.reset(token)

    @classmethod
    @asynccontextmanager
    async def ascope(cls, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        Async context manager for temporary context updates in coroutines.

        Usage:
            async with LogContext.ascope({"request_id": "abc"}):
                await some_async_function()

        This is functionally identical to `scope` but designed for `async with` blocks.
        It ensures that even if the code inside `yield` suspends execution (await),
        the context remains valid for that task.

        Args:
            data (Dict[str, Any]): Dictionary of context values to set within the scope

        Yields:
            None: Control to the async block using this context manager
        """
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            cls._context_store.reset(token)

    # Alias for backward compatibility if needed
    ascope_async = ascope

    @classmethod
    def set_all(cls, data: Dict[str, Any]) -> Token[Dict[str, Any]]:
        """
        Replaces the entire context with the provided data.
        Returns a Token that can be used to manually reset the context later.

        Args:
            data (Dict[str, Any]): New context dictionary to replace the current one

        Returns:
            Token[Dict[str, Any]]: Token for resetting context to previous state
        """
        return cls._context_store.set(data.copy())

    @classmethod
    def reset(cls, token: Token[Dict[str, Any]]) -> None:
        """
        Manually resets the context using a Token obtained from `set` or `set_all`.

        Args:
            token (Token[Dict[str, Any]]): Token returned by set_all() method
        """
        cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        Helper method to get the 'participant' field, representing the current active object/module.
        Defaults to 'Unknown' if not set.

        Returns:
            str: Name of the current participant in the trace flow
        """
        return str(cls.get("participant", "Unknown"))

    @classmethod
    def set_participant(cls, name: str) -> None:
        """
        Helper method to set the 'participant' field.

        Args:
            name (str): Name of the participant to set
        """
        cls.set("participant", name)

    @classmethod
    def current_trace_id(cls) -> str:
        """
        Retrieves the current trace ID for correlating events in a single flow.

        Lazy Initialization Logic:
        If no trace_id exists in the current context, it generates a new UUIDv4
        and sets it immediately. This ensures that:
        1. A trace ID is always available when asked for
        2. Once generated, the same ID persists for the duration of the context
           (unless manually changed), linking all subsequent logs together

        Returns:
            str: Unique trace ID for the current execution flow
        """
        tid = cls.get("trace_id")
        if not tid:
            tid = str(uuid.uuid4())
            cls.set("trace_id", tid)
        return str(tid)

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        """
        Manually sets the trace ID (e.g., from an incoming HTTP request header).
        """
        cls.set("trace_id", trace_id)
