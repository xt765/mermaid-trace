from contextvars import ContextVar
from typing import Dict, Any, Optional

class LogContext:
    """
    Manages context information for logging (e.g., request_id, user_id).
    Uses ContextVar to ensure thread-safety and asyncio support.
    """
    _context_store: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Set a context variable.
        
        Args:
            key: The context key name.
            value: The value to store.
        """
        ctx = cls._context_store.get().copy()
        ctx[key] = value
        cls._context_store.set(ctx)

    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
        Update multiple context variables.
        
        Args:
            data: A dictionary of key-value pairs to update in the context.
        """
        ctx = cls._context_store.get().copy()
        ctx.update(data)
        cls._context_store.set(ctx)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a context variable.
        
        Args:
            key: The context key to retrieve.
            default: The default value to return if the key doesn't exist.
            
        Returns:
            The value of the context variable, or the default value.
        """
        return cls._context_store.get().get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all context variables as a dictionary.
        
        Returns:
            A dictionary containing all current context variables.
        """
        return cls._context_store.get()

    @classmethod
    def clear(cls) -> None:
        """
        Clear the current context.
        
        Resets the context to an empty dictionary.
        """
        cls._context_store.set({})
