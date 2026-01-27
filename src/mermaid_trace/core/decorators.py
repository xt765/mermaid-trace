"""
Function Tracing Decorator Module
=================================

This module provides the core tracing functionality for MermaidTrace. It implements the decorators
responsible for intercepting function calls, capturing execution details, and logging them as
structured events that can be visualized as Mermaid Sequence Diagrams.

Key Components:
---------------
1.  **`@trace` Decorator**: The primary interface for users. It can be used as a simple decorator
    `@trace` or with arguments `@trace(action="Login")`.
2.  **Context Management**: Handles the propagation of "who called whom". It uses `LogContext`
    to track the current "participant" (caller) so that nested function calls correctly
    link to their parent caller.
3.  **Event Logging**: Generates `FlowEvent` objects containing source, target, action, and
    parameters, which are then passed to the specialized logging handler.
4.  **Automatic Target Resolution**: Heuristics to intelligently guess the participant name
    from the class instance (`self`) or class (`cls`), falling back to the module name.

Usage:
------
    from mermaid_trace.core.decorators import trace

    @trace
    def my_function(x):
        return x + 1

    @trace(target="Database", action="Query Users")
    async def get_users():
        ...
"""

import functools
import logging
import inspect
import re
import reprlib
import traceback
from dataclasses import dataclass
from typing import (
    Optional,
    Any,
    Callable,
    Tuple,
    Dict,
    Union,
    TypeVar,
    cast,
    overload,
    List,
)

from .events import FlowEvent
from .context import LogContext
from .config import config

# Logger name for flow events - used to isolate tracing logs from other application logs.
# This specific name is often used to configure a separate file handler in logging configs.
FLOW_LOGGER_NAME = "mermaid_trace.flow"

# Define generic type variable for the decorated function to preserve type hints
F = TypeVar("F", bound=Callable[..., Any])


def get_flow_logger() -> logging.Logger:
    """
    Returns the dedicated logger for flow events.

    This logger is intended to be used only for emitting `FlowEvent` objects.
    It separates tracing noise from standard application logging.

    Returns:
        logging.Logger: Logger instance configured for tracing events.
    """
    return logging.getLogger(FLOW_LOGGER_NAME)


class FlowRepr(reprlib.Repr):
    """
    Custom Repr class that simplifies default Python object representations
    (those containing memory addresses) into a cleaner <ClassName> format.
    Also groups consecutive identical items in lists to keep diagrams concise.
    """

    def _group_items(self, items_str: List[str]) -> List[str]:
        """Groups consecutive identical strings in a list."""
        if not items_str:
            return []
        res = []
        current_item = items_str[0]
        current_count = 1
        for i in range(1, len(items_str)):
            if items_str[i] == current_item:
                current_count += 1
            else:
                if current_count > 1:
                    res.append(f"{current_item} x {current_count}")
                else:
                    res.append(current_item)
                current_item = items_str[i]
                current_count = 1
        # Handle the last group
        if current_count > 1:
            res.append(f"{current_item} x {current_count}")
        else:
            res.append(current_item)
        return res

    def repr_list(self, obj: List[Any], level: int) -> str:
        """Custom list representation with item grouping."""
        n = len(obj)
        if n == 0:
            return "[]"
        items_str = []
        for i in range(min(n, self.maxlist)):
            items_str.append(self.repr1(obj[i], level - 1))

        grouped = self._group_items(items_str)
        if n > self.maxlist:
            grouped.append("...")
        return "[" + ", ".join(grouped) + "]"

    def repr_tuple(self, obj: Tuple[Any, ...], level: int) -> str:
        """Custom tuple representation with item grouping."""
        n = len(obj)
        if n == 0:
            return "()"
        if n == 1:
            return "(" + self.repr1(obj[0], level - 1) + ",)"
        items_str = []
        for i in range(min(n, self.maxtuple)):
            items_str.append(self.repr1(obj[i], level - 1))

        grouped = self._group_items(items_str)
        if n > self.maxtuple:
            grouped.append("...")
        return "(" + ", ".join(grouped) + ")"

    def repr1(self, x: Any, level: int) -> str:
        # Check if the object uses the default object.__repr__
        # Default repr looks like <module.Class object at 0x...>
        raw = repr(x)
        if " object at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # Simplify to just <ClassName>
            return f"<{x.__class__.__name__}>"

        # Also handle some common cases where address is present but it's not the default repr
        if " at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # Try to extract the class name or just simplify it
            return f"<{x.__class__.__name__}>"

        return super().repr1(x, level)


def _safe_repr(
    obj: Any, max_len: Optional[int] = None, max_depth: Optional[int] = None
) -> str:
    """
    Safely creates a string representation of an object for logging purposes.

    This function is critical for preventing log bloat and runtime errors during tracing.
    It handles:
    1.  **Truncation**: Limits the length of strings to prevent huge log files.
    2.  **Depth Control**: Limits recursion for nested structures like dicts/lists.
    3.  **Error Handling**: Catches exceptions if an object's `__repr__` is buggy or strict.
    4.  **Simplification**: Automatically simplifies default Python object representations
        (containing memory addresses) into <ClassName>.

    Args:
        obj: The object to represent as a string.
        max_len: Maximum length of the resulting string before truncation.
                 Defaults to config.max_string_length if None.
        max_depth: Maximum recursion depth for nested objects.
                   Defaults to config.max_arg_depth if None.

    Returns:
        str: Safe, truncated representation of the object.
    """
    # Use config defaults if not explicitly provided
    final_max_len = max_len if max_len is not None else config.max_string_length
    final_max_depth = max_depth if max_depth is not None else config.max_arg_depth

    try:
        # Use our custom FlowRepr to provide standard way to limit representation size
        # and simplify default object reprs recursively.
        a_repr = FlowRepr()
        a_repr.maxstring = final_max_len
        a_repr.maxother = final_max_len
        a_repr.maxlevel = final_max_depth

        # Generate the representation
        r = a_repr.repr(obj)

        # Final pass: Catch any remaining memory addresses using regex
        # (e.g., in types reprlib doesn't recurse into)
        # 1. <__main__.Class object at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) object at 0x[0-9a-fA-F]+>",
            r"<\2>",
            r,
        )
        # 2. <Class at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) at 0x[0-9a-fA-F]+>",
            r"<\2>",
            r,
        )

        # Double-check length constraint as reprlib might sometimes exceed it slightly
        if len(r) > final_max_len:
            return r[:final_max_len] + "..."
        return r
    except Exception:
        # Fallback if repr() fails (e.g., property access raising error in __repr__)
        return "<unrepresentable>"


@dataclass
class _TraceConfig:
    """Internal container for tracing configuration to avoid PLR0913."""

    capture_args: Optional[bool] = None
    max_arg_length: Optional[int] = None
    max_arg_depth: Optional[int] = None


def _format_args(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    config_obj: _TraceConfig,
) -> str:
    """
    Formats function arguments into a single string for the diagram arrow label.

    Example Output: "1, 'test', debug=True"

    This string is what appears on the arrow in the Mermaid diagram (e.g., `User->System: login(args...)`).

    Args:
        args: Positional arguments tuple.
        kwargs: Keyword arguments dictionary.
        config_obj: Trace configuration object.

    Returns:
        str: Comma-separated string of formatted arguments.
    """
    final_capture = (
        config_obj.capture_args
        if config_obj.capture_args is not None
        else config.capture_args
    )
    if not final_capture:
        return ""

    parts: list[str] = []

    # Process positional arguments
    for arg in args:
        parts.append(
            _safe_repr(
                arg,
                max_len=config_obj.max_arg_length,
                max_depth=config_obj.max_arg_depth,
            )
        )

    # Process keyword arguments
    for k, v in kwargs.items():
        val_str = _safe_repr(
            v, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
        )
        parts.append(f"{k}={val_str}")

    return ", ".join(parts)


def _resolve_target(
    func: Callable[..., Any], args: Tuple[Any, ...], target_override: Optional[str]
) -> str:
    """
    Determines the name of the 'Target' participant (the callee) for the diagram.

    The 'Target' is the entity *receiving* the call. We try to infer a meaningful name
    (like the class name) so the diagram shows "User -> AuthService" instead of "User -> login".

    Resolution Logic:
    1.  **Override**: Use explicit `target` from decorator if provided.
    2.  **Instance Method**: If first arg looks like `self` (has `__class__`), use ClassName.
    3.  **Class Method**: If first arg is a type (cls), use ClassName.
    4.  **Module Function**: Use the module name (e.g., "utils" from "my.pkg.utils").
    5.  **Fallback**: "Unknown".

    Args:
        func: The function being called (for module inspection).
        args: Positional arguments (to check for self/cls).
        target_override: Explicit target name provided by user via decorator.

    Returns:
        str: The resolved name for the target participant.
    """
    if target_override:
        return target_override

    # Heuristic: Check if this is a method call where args[0] is 'self' or 'cls'
    if args:
        first_arg = args[0]

        # Check for class method (cls) - where first arg is the type itself
        if isinstance(first_arg, type):
            return first_arg.__name__

        # Check for instance method (self)
        # We filter out primitives because functions might take an int/str as first arg,
        # which shouldn't be treated as 'self'.
        if hasattr(first_arg, "__class__") and not isinstance(
            first_arg, (str, int, float, bool, list, dict, set, tuple)
        ):
            return str(first_arg.__class__.__name__)

    # Fallback: Use module name for standalone functions
    module = inspect.getmodule(func)
    if module:
        # Extract just the last part of the module path (e.g. 'auth' from 'app.core.auth')
        return module.__name__.split(".")[-1]

    return "Unknown"


@dataclass
class _TraceMetadata:
    """Internal container for trace metadata to avoid PLR0913."""

    source: str
    target: str
    action: str
    trace_id: str


def _log_interaction(
    logger: logging.Logger,
    meta: _TraceMetadata,
    params: str,
) -> None:
    """
    Logs the 'Call' event (Start of function execution).

    This corresponds to the solid arrow in Mermaid: `Source -> Target: Action(params)`

    Args:
        logger: Logger instance.
        meta: Trace metadata.
        params: Stringified arguments.
    """
    req_event = FlowEvent(
        source=meta.source,
        target=meta.target,
        action=meta.action,
        message=meta.action,
        params=params,
        trace_id=meta.trace_id,
    )
    # The 'extra' dict is crucial. The custom LogHandler extracts 'flow_event'
    # from here to format the actual Mermaid syntax line.
    logger.info(
        f"{meta.source}->{meta.target}: {meta.action}", extra={"flow_event": req_event}
    )


def _log_return(
    logger: logging.Logger,
    source: str,
    target: str,
    action: str,
    result: Any,
    trace_id: str,
    config_obj: _TraceConfig,
) -> None:
    """
    Logs the 'Return' event (End of function execution).

    This corresponds to the dotted return arrow in Mermaid: `Target --> Source: Return value`

    Note on Direction:
    - In the diagram, the return goes from `target` (callee) back to `source` (caller).
    - The code logs it as `Target->Source` to reflect this flow.

    Args:
        logger: Logger instance.
        source: The original caller (who will receive the return).
        target: The callee (who is returning).
        action: The action that is completing.
        result: The return value of the function.
        trace_id: Trace correlation ID.
        config_obj: Trace configuration object.
    """
    result_str = ""
    final_capture = (
        config_obj.capture_args
        if config_obj.capture_args is not None
        else config.capture_args
    )

    if final_capture:
        result_str = _safe_repr(
            result,
            max_len=config_obj.max_arg_length,
            max_depth=config_obj.max_arg_depth,
        )

    resp_event = FlowEvent(
        source=target,  # Return flows FROM target
        target=source,  # Return flows TO source
        action=action,
        message="Return",
        is_return=True,
        result=result_str,
        trace_id=trace_id,
    )
    logger.info(f"{target}->{source}: Return", extra={"flow_event": resp_event})


def _log_error(
    logger: logging.Logger,
    meta: _TraceMetadata,
    error: Exception,
) -> None:
    """
    Logs an 'Error' event if the function raises an exception.

    This corresponds to the 'X' arrow in Mermaid: `Target -x Source: Error Message`

    Args:
        logger: Logger instance.
        meta: Trace metadata.
        error: The exception object.
    """
    # Capture full stack trace
    stack_trace = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )

    err_event = FlowEvent(
        source=meta.target,
        target=meta.source,
        action=meta.action,
        message=str(error),
        is_return=True,
        is_error=True,  # Flags this as an error event
        error_message=str(error),
        stack_trace=stack_trace,
        trace_id=meta.trace_id,
    )
    logger.error(
        f"{meta.target}-x{meta.source}: Error", extra={"flow_event": err_event}
    )


# Overload 1: Simple usage -> @trace
@overload
def trace_interaction(func: F) -> F: ...


# Overload 2: Configured usage -> @trace(action="Login")
@overload
def trace_interaction(
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: Optional[bool] = None,
    max_arg_length: Optional[int] = None,
    max_arg_depth: Optional[int] = None,
) -> Callable[[F], F]: ...


def trace_interaction(
    func: Optional[F] = None,
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: Optional[bool] = None,
    max_arg_length: Optional[int] = None,
    max_arg_depth: Optional[int] = None,
) -> Union[F, Callable[[F], F]]:  # noqa: PLR0913
    """
    Main Decorator for tracing function execution in Mermaid diagrams.

    This decorator instruments functions to log their execution flow as Mermaid
    sequence diagram events. It supports both synchronous and asynchronous functions,
    and automatically handles context propagation for nested calls.

    It supports two modes of operation:
    1.  **Simple Mode**: `@trace` (No arguments). Uses default naming (Class/Module name) and behavior.
    2.  **Configured Mode**: `@trace(action="Login", target="AuthService")`. Customizes the diagram labels.

    Args:
        func: The function being decorated (passed automatically in Simple Mode).
        source: Explicit name of the caller participant. Rarely used, as it's usually inferred from Context.
        target: Explicit name of the callee participant. Overrides automatic `self`/`cls`/module resolution.
        name: Alias for 'target' (syntactic sugar).
        action: Label for the arrow. Defaults to the function name (Title Cased).
        capture_args: If True, logs arguments and return values. Set False for sensitive data.
        max_arg_length: Truncation limit for logging arguments/results.
        max_arg_depth: Recursion limit for logging arguments/results.

    Returns:
        Callable: The decorated function (in Simple Mode) or a decorator factory (in Configured Mode).
    """

    # Handle alias - 'name' is an alternative convenience name for 'target'
    final_target = target or name

    # Mode 1: @trace used without parentheses
    # func is passed directly. We create the wrapper immediately.
    if func is not None and callable(func):
        return _create_decorator(
            func,
            source,
            final_target,
            action,
            _TraceConfig(capture_args, max_arg_length, max_arg_depth),
        )

    # Mode 2: @trace(...) used with arguments
    # func is None. We return a "factory" function that Python will call with the function later.
    def factory(f: F) -> F:
        return _create_decorator(
            f,
            source,
            final_target,
            action,
            _TraceConfig(capture_args, max_arg_length, max_arg_depth),
        )

    return factory


def _create_decorator(
    func: F,
    source: Optional[str],
    target: Optional[str],
    action: Optional[str],
    config_obj: _TraceConfig,
) -> F:
    """
    Internal factory that constructs the actual wrapper function.

    This separates the wrapper creation logic from the argument parsing logic in `trace_interaction`.
    It handles the distinction between synchronous and asynchronous functions, returning
    the appropriate wrapper type.

    Args:
        func: The function to decorate.
        source: Configured source name.
        target: Configured target name.
        action: Configured action name.
        config_obj: Trace configuration object.

    Returns:
        Callable: The wrapped function containing tracing logic.
    """

    # Pre-calculate static metadata to save time at runtime.
    # If no action name provided, generate one from the function name (e.g., "get_user" -> "Get User")
    if action is None:
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """
        Synchronous function wrapper.
        Executes tracing logic around a standard blocking function call.
        """
        # 1. Resolve Context
        # 'current_source' is who called us. If not explicit, we get it from thread-local storage.
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()

        # 'current_target' is who we are. We figure this out from 'self', 'cls', or module name.
        current_target = _resolve_target(func, args, target)

        meta = _TraceMetadata(current_source, current_target, action, trace_id)

        logger = get_flow_logger()
        # Format arguments for the diagram arrow label
        params_str = _format_args(args, kwargs, config_obj)

        # 2. Log Request (Start of function)
        # Emits the "Call" arrow (Source -> Target)
        _log_interaction(logger, meta, params_str)

        # 3. Execute with New Context
        # We push 'current_target' as the NEW 'participant' (source) for any internal calls made by this function.
        # This builds the chain: A calls B (A->B), then B calls C (B->C).
        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                # Execute the actual user function
                result = func(*args, **kwargs)

                # 4. Log Success Return
                # Emits the "Return" arrow (Target --> Source)
                _log_return(
                    logger,
                    current_source,
                    current_target,
                    action,
                    result,
                    trace_id,
                    config_obj,
                )
                return result
            except Exception as e:
                # 5. Log Error Return
                # Emits the "Error" arrow (Target -x Source)
                _log_error(logger, meta, e)
                # Re-raise the exception so program flow isn't altered
                raise

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        """
        Asynchronous function wrapper.
        Executes tracing logic around an async/await coroutine.
        """
        # 1. Resolve Context (Same as sync)
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)

        meta = _TraceMetadata(current_source, current_target, action, trace_id)

        logger = get_flow_logger()
        params_str = _format_args(args, kwargs, config_obj)

        # 2. Log Request
        _log_interaction(logger, meta, params_str)

        # 3. Execute with New Context using 'ascope'
        # Crucial difference for Async: We use `ascope` (async scope) which uses contextvars.
        # This ensures the context is preserved across `await` points where the event loop might switch tasks.
        async with LogContext.ascope(
            {"participant": current_target, "trace_id": trace_id}
        ):
            try:
                # Await the actual user coroutine
                result = await func(*args, **kwargs)

                # 4. Log Success Return
                _log_return(
                    logger,
                    current_source,
                    current_target,
                    action,
                    result,
                    trace_id,
                    config_obj,
                )
                return result
            except Exception as e:
                # 5. Log Error Return
                _log_error(logger, meta, e)
                raise

    # Detect if the wrapped function is a coroutine (async def)
    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)  # Use async wrapper for async functions
    return cast(F, wrapper)  # Use sync wrapper for regular functions


# Alias for easy import - 'trace' is the primary name users should use
trace = trace_interaction
