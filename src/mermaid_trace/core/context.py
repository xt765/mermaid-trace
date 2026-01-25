from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator

class LogContext:
    """
    Manages global context information for logging (e.g., request_id, user_id).

    **The Problem:**
    In modern async/threaded applications, passing a `request_id` or `user_id` 
    to every single function so it can be logged is messy and impractical.

    **The Solution: Context Variables**
    This class uses `contextvars` to store data that is "global" to a specific
    execution thread or async task, but invisible to others. It's like a thread-local
    storage that also works with `asyncio`.

    **Key Concepts:**
    1. **Context Isolation:** Data set in one request doesn't leak into another.
    2. **Copy-on-Write (COW):** Ensures immutability and safety when branching tasks.
    3. **Scopes:** Context can be temporarily modified for a block of code.
    """
    
    # The underlying storage mechanism.
    # `ContextVar` is a native Python feature (since 3.7).
    # It creates a variable that automatically tracks the current execution context.
    # Default is no value (LookupError), handled in `_get_store`.
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        Retrieves the current context dictionary.
        
        If no context exists yet for this task/thread, it creates a fresh empty one.
        """
        try:
            return cls._context_store.get()
        except LookupError:
            return {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Sets a single context variable safely using Copy-on-Write.

        **Deep Dive: Copy-on-Write (COW)**
        Why do we copy the dictionary before changing it?
        
        Imagine `Task A` sets a context. `Task B` is spawned from `Task A` and inherits
        the context object. If `Task B` modifies the dictionary directly, `Task A` 
        would see those changes! This causes hard-to-debug "pollution" bugs.
        
        By copying:
        1. We take the current state.
        2. We clone it (shallow copy).
        3. We modify the clone.
        4. We save the clone as the *new* context for *this* task only.
        
        The parent task keeps its original dictionary. The child gets a modified version.
        """
        # 1. Get current data
        # 2. .copy() creates a new dict object in memory
        ctx = cls._get_store().copy()
        
        # 3. Update the new object
        ctx[key] = value
        
        # 4. Bind the new object to the current ContextVar
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        Updates multiple context variables at once using Copy-on-Write.
        
        See `set()` for the explanation of why we copy first.
        """
        if not data:
            return
            
        ctx = cls._get_store().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific context variable.
        """
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Retrieves a snapshot of all current context variables.
        
        Returns a copy to prevent the caller from accidentally mutating
        the internal state.
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        Synchronous Context Manager for temporary context updates.
        
        **Usage:**
        ```python
        with LogContext.scope({"process": "payment"}):
            # Context has "process": "payment" here
            process_payment()
        # Context is restored to original state here
        ```

        **How it works (Token Mechanism):**
        1. We calculate the new state.
        2. `set()` returns a `Token`. This token acts like a "save point" or pointer
           to the *previous* value of the variable.
        3. We yield control to the user's code.
        4. In `finally`, we use `reset(token)` to revert the variable to the "save point".
        """
        # 1. Prepare new state (Copy-on-Write logic manually applied)
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        
        # 2. Set new state and get restoration token
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            # 3. Restore previous state
            cls._context_store.reset(token)

    @classmethod
    @asynccontextmanager
    async def ascope(cls, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        Asynchronous Context Manager for temporary context updates.
        
        Identical logic to `scope`, but compatible with `async with` statements.
        Essential for asyncio applications where context must be maintained
        across await points.
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
        Replaces the ENTIRE context with a new dictionary.
        
        **Advanced Usage:**
        Used by middleware to initialize context at the start of a request
        lifecycle (e.g., from HTTP headers).
        """
        return cls._context_store.set(data.copy())

    @classmethod
    def reset(cls, token: Token[Dict[str, Any]]) -> None:
        """
        Manually resets the context using a token.
        """
        cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        Helper to get the current active participant (for flow diagrams).
        Defaults to 'Unknown' if not set.
        """
        return cls.get("participant", "Unknown")

    @classmethod
    def set_participant(cls, name: str) -> None:
        """Sets the current participant."""
        cls.set("participant", name)
