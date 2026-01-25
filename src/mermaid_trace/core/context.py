from contextvars import ContextVar, Token
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator

class LogContext:
    """
    Manages global context information for logging (e.g., request_id, user_id, current_participant).
    
    This class provides a thread-safe and async-safe mechanism to store and retrieve
    contextual data without passing it explicitly as arguments to every function.

    **The Problem:**
    In modern async/threaded applications, passing metadata like `request_id` or `user_id` 
    down the call stack to every single function is cumbersome, error-prone, and clutters APIs.

    **The Solution: Context Variables**
    This class utilizes Python's `contextvars` module to store data that is "local" to a 
    specific execution context (a thread or an asyncio task). It behaves like Thread-Local 
    Storage (TLS) but is fully compatible with asyncio's event loop.

    **Key Concepts:**
    1. **Context Isolation:** Data set in one request/task is invisible to others.
    2. **Copy-on-Write (COW):** Ensures that branching tasks inherit context safely without 
       polluting the parent's context or sibling tasks.
    3. **Scopes:** Context can be temporarily modified for a specific block of code using 
       context managers (`with` or `async with`), automatically reverting changes afterwards.
    """
    
    # The underlying storage mechanism.
    # `ContextVar` is a native Python feature (since 3.7).
    # It creates a variable that automatically tracks the current execution context.
    # The default value is not set here; we handle the empty case in `_get_store`.
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context")

    @classmethod
    def _get_store(cls) -> Dict[str, Any]:
        """
        Retrieves the current context dictionary for the active task/thread.
        
        If no context exists yet for this task/thread, it initializes and returns 
        a fresh empty dictionary.
        
        Returns:
            Dict[str, Any]: The current context dictionary.
        """
        try:
            return cls._context_store.get()
        except LookupError:
            # If no context is set, return an empty dict.
            # Note: We don't set it back to the store here to avoid unnecessary writes
            # until data is actually added.
            return {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Sets a single context variable safely using the Copy-on-Write principle.

        **Deep Dive: Copy-on-Write (COW)**
        Why do we copy the dictionary before changing it?
        
        Imagine `Task A` sets a context. `Task B` is spawned from `Task A` and inherits
        the context object reference. If `Task B` modifies the dictionary in-place, 
        `Task A` would see those changes! This causes "context pollution" and hard-to-debug 
        race conditions.
        
        By copying:
        1. We take the current state.
        2. We create a shallow copy (new object in memory).
        3. We modify the copy.
        4. We bind the copy as the *new* context for *this* task only.
        
        The parent task retains its reference to the original dictionary.
        
        Args:
            key (str): The context variable name.
            value (Any): The value to store.
        """
        # 1. Get current data
        # 2. .copy() creates a new dict object in memory (snapshot)
        ctx = cls._get_store().copy()
        
        # 3. Update the new object
        ctx[key] = value
        
        # 4. Bind the new object to the current ContextVar
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        Updates multiple context variables at once using Copy-on-Write.
        
        This is more efficient than calling `set()` multiple times as it performs
        only one copy operation and one set operation.
        
        Args:
            data (Dict[str, Any]): A dictionary of key-value pairs to merge into the context.
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
        
        Args:
            key (str): The context variable name.
            default (Any, optional): Value to return if key is missing. Defaults to None.
            
        Returns:
            Any: The value associated with the key, or the default value.
        """
        return cls._get_store().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Retrieves a snapshot of all current context variables.
        
        Returns:
            Dict[str, Any]: A shallow copy of the context dictionary.
                            Returning a copy prevents external code from accidentally 
                            mutating the internal state.
        """
        return cls._get_store().copy()

    @classmethod
    @contextmanager
    def scope(cls, data: Dict[str, Any]) -> Iterator[None]:
        """
        Synchronous Context Manager for temporary context updates.
        
        This allows you to set context variables that only exist within the `with` block.
        Once the block exits (normally or via exception), the context is reverted to 
        its previous state.
        
        **Usage:**
        ```python
        with LogContext.scope({"process": "payment"}):
            # Context has "process": "payment" here
            process_payment()
        # Context is restored to original state here (process key removed or reverted)
        ```

        **How it works (Token Mechanism):**
        1. We calculate the new state (merging current context with `data`).
        2. `_context_store.set()` returns a `Token`. This token acts like a "save point" 
           pointing to the *previous* value of the ContextVar.
        3. We yield control to the user's code block.
        4. In the `finally` block, we use `reset(token)` to revert the variable to the "save point".
        
        Args:
            data (Dict[str, Any]): The temporary context data to apply.
        """
        # 1. Prepare new state (Copy-on-Write logic manually applied)
        current_ctx = cls._get_store().copy()
        current_ctx.update(data)
        
        # 2. Set new state and get restoration token
        token = cls._context_store.set(current_ctx)
        try:
            yield
        finally:
            # 3. Restore previous state using the token
            cls._context_store.reset(token)

    @classmethod
    @asynccontextmanager
    async def ascope(cls, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        Asynchronous Context Manager for temporary context updates.
        
        Identical logic to `scope`, but compatible with `async with` statements.
        This is essential for asyncio applications where context must be maintained
        across `await` points.
        
        **Usage:**
        ```python
        async with LogContext.ascope({"request_id": "123"}):
            await process_async_request()
        ```
        
        Args:
            data (Dict[str, Any]): The temporary context data to apply.
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
        Typically used by middleware or framework integrations to initialize the 
        context at the very start of a request lifecycle (e.g., extracting headers).
        
        Args:
            data (Dict[str, Any]): The new context dictionary.
            
        Returns:
            Token: A token that can be used to reset the context later if needed.
        """
        return cls._context_store.set(data.copy())

    @classmethod
    def reset(cls, token: Token[Dict[str, Any]]) -> None:
        """
        Manually resets the context using a token.
        
        Args:
            token (Token): The token returned by `set()` or `set_all()`.
        """
        cls._context_store.reset(token)

    @classmethod
    def current_participant(cls) -> str:
        """
        Helper to get the current active participant (for sequence diagrams).
        
        This is used to determine "who" is calling a function. If not explicitly set,
        it defaults to 'Unknown'.
        
        Returns:
            str: The name of the current participant.
        """
        return str(cls.get("participant", "Unknown"))

    @classmethod
    def set_participant(cls, name: str) -> None:
        """
        Sets the current participant name in the context.
        
        Args:
            name (str): The name of the participant (e.g., "Client", "Database", "ServiceA").
        """
        cls.set("participant", name)
