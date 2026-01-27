"""
Utility functions for auto-instrumentation and patching.
"""

import inspect
from typing import Any, Type, Optional, List
from .decorators import trace


def trace_class(
    cls: Optional[Type[Any]] = None,
    *,
    include_private: bool = False,
    exclude: Optional[List[str]] = None,
    **trace_kwargs: Any,
) -> Any:
    """
    Class decorator to automatically trace all methods in a class.

    Args:
        cls: The class to instrument.
        include_private: If True, traces methods starting with '_'. Defaults to False.
        exclude: List of method names to skip.
        **trace_kwargs: Arguments passed to the @trace decorator (e.g., capture_args).

    Usage:
        @trace_class
        class MyService:
            def method1(self): ...
            def method2(self): ...
    """

    def _decorate_class(klass: Type[Any]) -> Type[Any]:
        exclude_set = set(exclude or [])

        for name, method in inspect.getmembers(klass):
            # Skip excluded methods
            if name in exclude_set:
                continue

            # Skip private methods unless requested
            if name.startswith("_") and not include_private:
                # But always skip magic methods like __init__, __str__ unless explicitly handled?
                # Usually we don't want to trace __init__ by default as it clutters the diagram
                # and __repr__ MUST NOT be traced to avoid recursion in logging.
                continue

            # Double check it's actually a function/method defined in this class (or inherited)
            # inspect.isfunction or inspect.isroutine is good.
            if inspect.isfunction(method) or inspect.iscoroutinefunction(method):
                # Apply the trace decorator
                # We need to handle staticmethods and classmethods carefully if we iterate __dict__
                # But inspect.getmembers returns the bound/unbound method.
                # However, modifying the class requires setting the attribute on the class.

                # A safer way is to inspect __dict__ to see what is actually defined in THIS class
                # vs inherited. But trace_class usually implies tracing this class's behavior.

                # Let's try to set the attribute.
                try:
                    setattr(klass, name, trace(**trace_kwargs)(method))
                except (AttributeError, TypeError):
                    # Some attributes might be read-only or not settable
                    pass
        return klass

    if cls is None:
        return _decorate_class
    return _decorate_class(cls)


def patch_object(obj: Any, method_name: str, **trace_kwargs: Any) -> None:
    """
    Monkey-patches a method on an object or class with tracing.

    Useful for third-party libraries where you cannot modify the source code.

    Args:
        obj: The object or class or module to patch.
        method_name: The name of the function/method to patch.
        **trace_kwargs: Arguments for @trace.

    Usage:
        import requests
        patch_object(requests, 'get', action="HTTP GET")
    """
    if not hasattr(obj, method_name):
        raise AttributeError(f"{obj} has no attribute '{method_name}'")

    original = getattr(obj, method_name)

    # Apply trace decorator
    decorated = trace(**trace_kwargs)(original)

    # Replace
    setattr(obj, method_name, decorated)
