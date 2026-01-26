"""
Function Tracing Decorator Module

This module provides the core tracing functionality for MermaidTrace. It includes:
- A decorator (`trace`/`trace_interaction`) to instrument functions for tracing
- Helper functions for formatting and logging trace events
- Context management for tracking call chains

The decorator can be applied to both synchronous and asynchronous functions,
and automatically handles context propagation for nested calls.
"""

import functools
import logging
import inspect
import reprlib
from typing import Optional, Any, Callable, Tuple, Dict, Union, TypeVar, cast, overload

from .events import FlowEvent
from .context import LogContext

# Logger name for flow events - used to isolate tracing logs from other application logs
FLOW_LOGGER_NAME = "mermaid_trace.flow"

# Define generic type variable for the decorated function
F = TypeVar("F", bound=Callable[..., Any])


def get_flow_logger() -> logging.Logger:
    """Returns the dedicated logger for flow events.

    Returns:
        logging.Logger: Logger instance configured for tracing events
    """
    return logging.getLogger(FLOW_LOGGER_NAME)


def _safe_repr(obj: Any, max_len: int = 50, max_depth: int = 1) -> str:
    """
    Safely creates a string representation of an object.

    Prevents massive log files by truncating long strings/objects
    and handling exceptions during __repr__ calls (e.g. strict objects).

    Args:
        obj: The object to represent as a string
        max_len: Maximum length of the resulting string
        max_depth: Maximum recursion depth for nested objects

    Returns:
        str: Safe, truncated representation of the object
    """
    try:
        # Create a custom repr object to control depth and length
        a_repr = reprlib.Repr()
        a_repr.maxstring = max_len
        a_repr.maxother = max_len
        a_repr.maxlevel = max_depth

        r = a_repr.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        # Fallback if repr() fails for any reason
        return "<unrepresentable>"


def _format_args(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1,
) -> str:
    """
    Formats function arguments into a single string "arg1, arg2, k=v".
    Used for the arrow label in the diagram.

    Args:
        args: Positional arguments to format
        kwargs: Keyword arguments to format
        capture_args: Whether to capture and format arguments at all
        max_arg_length: Maximum length of each argument representation
        max_arg_depth: Maximum recursion depth for nested arguments

    Returns:
        str: Formatted string of arguments, or empty string if capture_args is False
    """
    if not capture_args:
        return ""

    parts: list[str] = []

    # Format positional arguments
    for arg in args:
        parts.append(_safe_repr(arg, max_len=max_arg_length, max_depth=max_arg_depth))

    # Format keyword arguments
    for k, v in kwargs.items():
        val_str = _safe_repr(v, max_len=max_arg_length, max_depth=max_arg_depth)
        parts.append(f"{k}={val_str}")

    return ", ".join(parts)


def _resolve_target(
    func: Callable[..., Any], args: Tuple[Any, ...], target_override: Optional[str]
) -> str:
    """
    Determines the name of the participant (Target) for the diagram.

    Resolution Priority:
    1. **Override**: If the user explicitly provided `target="Name"`, use it.
    2. **Instance Method**: If the first arg looks like `self` (has __class__),
       use the class name.
    3. **Class Method**: If the first arg is a type (cls), use the class name.
    4. **Module Function**: Fallback to the name of the module containing the function.
    5. **Fallback**: "Unknown".

    Args:
        func: The function being called
        args: Positional arguments passed to the function
        target_override: Explicit target name provided by the user, if any

    Returns:
        str: Resolved target name for the diagram
    """
    if target_override:
        return target_override

    # Heuristic: If it's a method call, args[0] is usually 'self' or 'cls'
    if args:
        first_arg = args[0]
        # Check if it looks like a class instance (not a primitive or container)
        if hasattr(first_arg, "__class__") and not isinstance(
            first_arg, (str, int, float, bool, list, dict, type)
        ):
            return str(first_arg.__class__.__name__)
        # Check if it looks like a class (cls) - e.g. @classmethod
        if isinstance(first_arg, type):
            return first_arg.__name__

    # Fallback to module name for standalone functions
    module = inspect.getmodule(func)
    if module:
        return module.__name__.split(".")[-1]
    return "Unknown"


def _log_interaction(
    logger: logging.Logger,
    source: str,
    target: str,
    action: str,
    params: str,
    trace_id: str,
) -> None:
    """
    Logs the 'Call' event (Start of function).
    Generates a FlowEvent and logs it with the appropriate context.

    Args:
        logger: Logger instance to use for logging
        source: Name of the source participant (caller)
        target: Name of the target participant (callee)
        action: Name of the action being performed
        params: Formatted string of function arguments
        trace_id: Unique trace identifier for correlation
    """
    req_event = FlowEvent(
        source=source,
        target=target,
        action=action,
        message=action,
        params=params,
        trace_id=trace_id,
    )
    # The 'extra' dict is critical: the Handler will pick this up to format the Mermaid line
    logger.info(f"{source}->{target}: {action}", extra={"flow_event": req_event})


def _log_return(
    logger: logging.Logger,
    source: str,
    target: str,
    action: str,
    result: Any,
    trace_id: str,
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1,
) -> None:
    """
    Logs the 'Return' event (End of function).
    Arrow: target --> source (Dotted line return)

    Note: 'source' here is the original caller, 'target' is the callee.
    So the return arrow goes from target back to source.

    Args:
        logger: Logger instance to use for logging
        source: Name of the original caller
        target: Name of the callee that's returning
        action: Name of the action being returned from
        result: Return value of the function
        trace_id: Unique trace identifier for correlation
        capture_args: Whether to include the return value in the log
        max_arg_length: Maximum length of the return value representation
        max_arg_depth: Maximum recursion depth for nested return values
    """
    result_str = ""
    if capture_args:
        result_str = _safe_repr(result, max_len=max_arg_length, max_depth=max_arg_depth)

    resp_event = FlowEvent(
        source=target,
        target=source,
        action=action,
        message="Return",
        is_return=True,
        result=result_str,
        trace_id=trace_id,
    )
    logger.info(f"{target}->{source}: Return", extra={"flow_event": resp_event})


def _log_error(
    logger: logging.Logger,
    source: str,
    target: str,
    action: str,
    error: Exception,
    trace_id: str,
) -> None:
    """
    Logs an 'Error' event if the function raises an exception.
    Arrow: target -x source (Error return)

    Args:
        logger: Logger instance to use for logging
        source: Name of the original caller
        target: Name of the callee that encountered an error
        action: Name of the action that failed
        error: Exception that was raised
        trace_id: Unique trace identifier for correlation
    """
    err_event = FlowEvent(
        source=target,
        target=source,
        action=action,
        message=str(error),
        is_return=True,
        is_error=True,
        error_message=str(error),
        trace_id=trace_id,
    )
    logger.error(f"{target}-x{source}: Error", extra={"flow_event": err_event})


@overload
def trace_interaction(func: F) -> F: ...


@overload
def trace_interaction(
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1,
) -> Callable[[F], F]: ...


def trace_interaction(
    func: Optional[F] = None,
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1,
) -> Union[F, Callable[[F], F]]:
    """
    Main Decorator for tracing function execution in Mermaid diagrams.

    This decorator instruments functions to log their execution flow as Mermaid
    sequence diagram events. It supports both synchronous and asynchronous functions,
    and automatically handles context propagation for nested calls.

    It supports two modes of operation:
    1. **Simple**: `@trace` (No arguments) - uses default settings
    2. **Configured**: `@trace(action="Login", target="AuthService")` - customizes behavior

    Args:
        func: The function being decorated (automatically passed in simple mode).
        source: Explicit name of the caller participant (rarely used, usually inferred from Context).
        target: Explicit name of the callee participant (overrides automatic resolution).
        name: Alias for 'target' (for clearer API usage).
        action: Label for the arrow (defaults to function name in Title Case).
        capture_args: Whether to include arguments and return values in the log. Default True.
        max_arg_length: Maximum string length for argument/result representation. Default 50.
        max_arg_depth: Maximum recursion depth for argument/result representation. Default 1.

    Returns:
        Callable: Either the decorated function (simple mode) or a decorator factory (configured mode)
    """

    # Handle alias - 'name' is an alternative name for 'target'
    final_target = target or name

    # Mode 1: @trace used without parentheses - directly decorate the function
    if func is not None and callable(func):
        return _create_decorator(
            func,
            source,
            final_target,
            action,
            capture_args,
            max_arg_length,
            max_arg_depth,
        )

    # Mode 2: @trace(...) used with arguments -> returns a factory that will decorate the function
    def factory(f: F) -> F:
        return _create_decorator(
            f, source, final_target, action, capture_args, max_arg_length, max_arg_depth
        )

    return factory


def _create_decorator(
    func: F,
    source: Optional[str],
    target: Optional[str],
    action: Optional[str],
    capture_args: bool,
    max_arg_length: int,
    max_arg_depth: int,
) -> F:
    """
    Constructs the actual wrapper function for the decorated function.
    Handles both synchronous and asynchronous functions by creating the appropriate wrapper.

    This function separates the wrapper creation logic from the argument parsing logic
    in `trace_interaction`, making the code cleaner and easier to test.

    Args:
        func: The function to decorate
        source: Explicit source name, if any
        target: Explicit target name, if any
        action: Explicit action name, if any
        capture_args: Whether to capture arguments and return values
        max_arg_length: Maximum length for argument/return value representations
        max_arg_depth: Maximum recursion depth for nested objects

    Returns:
        Callable: Decorated function with tracing logic
    """

    # Pre-calculate static metadata to save time at runtime
    if action is None:
        # Default action name is the function name, converted to Title Case
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Synchronous function wrapper that adds tracing logic."""
        # 1. Resolve Context
        # 'source' is who called us (from Context). 'target' is who we are (resolved from self/cls).
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)

        logger = get_flow_logger()
        # Format arguments for the diagram arrow label
        params_str = _format_args(
            args, kwargs, capture_args, max_arg_length, max_arg_depth
        )

        # 2. Log Request (Start of function)
        # Logs the initial "Call" arrow (Source -> Target)
        _log_interaction(
            logger, current_source, current_target, action, params_str, trace_id
        )

        # 3. Execute with New Context
        # We push 'current_target' as the NEW 'participant' (source) for any internal calls.
        # This builds the chain: A -> B, then inside B, B becomes the source for C (B -> C).
        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = func(*args, **kwargs)
                # 4. Log Success Return
                # Logs the "Return" arrow (Target --> Source)
                _log_return(
                    logger,
                    current_source,
                    current_target,
                    action,
                    result,
                    trace_id,
                    capture_args,
                    max_arg_length,
                    max_arg_depth,
                )
                return result
            except Exception as e:
                # 5. Log Error Return
                # Logs the "Error" arrow (Target --x Source)
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        """Asynchronous function wrapper that adds tracing logic."""
        # 1. Resolve Context (Same as sync)
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)

        logger = get_flow_logger()
        params_str = _format_args(
            args, kwargs, capture_args, max_arg_length, max_arg_depth
        )

        # 2. Log Request
        _log_interaction(
            logger, current_source, current_target, action, params_str, trace_id
        )

        # 3. Execute with New Context using 'ascope'
        # Use async context manager (ascope) to ensure context propagates correctly across awaits.
        # This is critical for asyncio: context must be preserved even if the task yields control.
        async with LogContext.ascope(
            {"participant": current_target, "trace_id": trace_id}
        ):
            try:
                result = await func(*args, **kwargs)
                # 4. Log Success Return
                _log_return(
                    logger,
                    current_source,
                    current_target,
                    action,
                    result,
                    trace_id,
                    capture_args,
                    max_arg_length,
                    max_arg_depth,
                )
                return result
            except Exception as e:
                # 5. Log Error Return
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    # Detect if the wrapped function is a coroutine to choose the right wrapper
    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)  # Return async wrapper for coroutines
    return cast(F, wrapper)  # Return sync wrapper for regular functions


# Alias for easy import - 'trace' is the primary name users should use
trace = trace_interaction
