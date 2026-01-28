# File: src/mermaid_trace/core/decorators.py

## Overview
`decorators.py` is the core decorator module for MermaidTrace. It implements all the logic for the `@trace` decorator, including intercepting function calls, automatically identifying participants, capturing parameters, recording return results, and handling exceptions.

## Core Functionality Analysis

### 1. `@trace` (i.e., `trace_interaction`)
This is the most commonly used interface by users. It supports two usage patterns:
- **Simple Mode**: `@trace`, using default configuration directly.
- **Config Mode**: `@trace(target="DB", action="Query")`, customizing display names and actions in diagrams.

### 2. Participant Identification (`_resolve_target`)
This function implements intelligent guessing logic to determine "who" is the current target being called:
- **Explicitly Specified**: Priority is given to `target` in decorator parameters.
- **Class Instance/Class Method**:
    - If the first parameter is `self` (with `__class__`), use its class name.
    - If the first parameter is `cls` (type object), use its class name.
- **Regular Function**: Use the name of its module (only the last part, such as `auth`).

### 3. Object Display Optimization and `FlowRepr`
To prevent log explosion and improve diagram readability, the module introduces a custom `FlowRepr` class:
- **Object Simplification**: Automatically detects and simplifies default Python object representations containing memory addresses (e.g., `<__main__.Obj at 0x...>` → `<Obj>`).
- **Container Merging**: Automatically identifies and merges consecutive identical items in lists or tuples (e.g., `[<UserDB> x 5]`).
- **Regular Expression Cleaning**: Uses regex in the final stage to further clean residual memory address formats.

### 4. Safe Representation (`_safe_repr`)
- **Truncation and Depth**: Uses `FlowRepr` to limit string length and recursion depth.
- **Fault Tolerance**: Catches all exceptions that might occur during `repr` generation, ensuring tracing doesn't affect main business logic.

### 5. Wrapper Logic (`_create_decorator`)
- **Sync/Async Support**: Automatically identifies and returns corresponding wrappers (`wrapper` or `async_wrapper`) through `inspect.iscoroutinefunction`.
- **Parameter Decoupling**: To address Ruff PLR0913 (too many parameters) check, introduces `_TraceConfig` and `_TraceMetadata` data classes to group configuration items and metadata.
- **Context Switching**:
    - Records "request" event before calling function.
    - **Key Point**: Uses `LogContext.scope` to set the currently called target as the new "current participant", so other traced functions called internally can correctly identify the caller.
    - After function returns, records "return" event with return value.

### 6. Exception Handling (`_log_error`)
- If function execution throws an exception, the decorator captures it.
- Uses `traceback.format_exception` to get complete stack information.
- Records a special error event (displayed as `X` arrow in Mermaid).
- **Does Not Intercept Exceptions**: Re-raises immediately after recording, ensuring business logic's exception handling flow remains unchanged.

## Terminology Explanation
- **Source**: The participant initiating the call.
- **Target**: The participant receiving the call.
- **Action**: Text description on the arrow, defaulting to title-cased function name.
- **Trace ID**: Unique ID used to correlate an entire call chain.

## Source Code with English Comments

```python
"""
Function tracing decorator module
=================================

This module implements core logic for intercepting function calls, capturing execution details, and recording them as structured events.
It provides the `@trace` decorator, responsible for generating all metadata needed for Mermaid sequence diagrams.

Key Components:
---------------
1.  **`@trace` Decorator**: Main interface used by users.
2.  **Context Management**: Uses `LogContext` to track "who called whom", ensuring nested call chains are correct.
3.  **Event Recording**: Generates `FlowEvent` objects containing source, target, action, and parameters.
4.  **Automatic Target Resolution**: Intelligently guesses participant names (prioritizing class names, then module names).
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

# Special Logger name for flow events
FLOW_LOGGER_NAME = "mermaid_trace.flow"

F = TypeVar("F", bound=Callable[..., Any])

def get_flow_logger() -> logging.Logger:
    """
    Return the special Logger instance for recording FlowEvent.
    This logger isolates tracing logs from standard application logs.
    """
    return logging.getLogger(FLOW_LOGGER_NAME)

class FlowRepr(reprlib.Repr):
    """
    Custom Repr class for simplifying Python object representations.
    1. Simplifies default representations containing memory addresses to <ClassName> format.
    2. Automatically merges consecutive identical items in lists/tuples for cleaner diagrams.
    """

    def _group_items(self, items_str: List[str]) -> List[str]:
        """Merge consecutive identical strings in list."""
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
        # Handle last group
        if current_count > 1:
            res.append(f"{current_item} x {current_count}")
        else:
            res.append(current_item)
        return res

    def repr_list(self, obj: List[Any], level: int) -> str:
        """List representation with duplicate merging."""
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
        """Tuple representation with duplicate merging."""
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
        """Override single item representation, automatically cleaning memory addresses."""
        # Check if object uses default object.__repr__
        # Default repr looks like <module.Class object at 0x...>
        raw = repr(x)
        if " object at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # Simplify to <ClassName>
            return f"<{x.__class__.__name__}>"

        # Handle other special reprs containing memory addresses
        if " at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # Try to extract class name or simplify directly
            return f"<{x.__class__.__name__}>"

        return super().repr1(x, level)

def _safe_repr(
    obj: Any, max_len: Optional[int] = None, max_depth: Optional[int] = None
) -> str:
    """
    Safely create string representation of object.
    
    This function is crucial for preventing log bloat and runtime errors during tracing.
    It handles:
    1. **Truncation**: Limits string length.
    2. **Depth Control**: Limits recursion depth of nested structures.
    3. **Error Handling**: Catches exceptions that object `__repr__` might throw.
    4. **Simplification**: Automatically simplifies Python object representations containing memory addresses.
    """
    final_max_len = max_len if max_len is not None else config.max_string_length
    final_max_depth = max_depth if max_depth is not None else config.max_arg_depth

    try:
        # Use custom FlowRepr for standardized method with size limits and simplification
        a_repr = FlowRepr()
        a_repr.maxstring = final_max_len
        a_repr.maxother = final_max_len
        a_repr.maxlevel = final_max_depth

        r = a_repr.repr(obj)

        # Final pass: Use regex to capture any remaining memory address formats
        # (e.g., types that reprlib doesn't recursively enter)
        # 1. <__main__.Class object at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) object at 0x[0-9a-fA-F]+">",
            r"<\2>",
            r,
        )
        # 2. <Class at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) at 0x[0-9a-fA-F]+">",
            r"<\2>",
            r,
        )

        # Double-check length limit, as reprlib might slightly exceed
        if len(r) > final_max_len:
            return r[:final_max_len] + "..."
        return r
    except Exception:
        # If repr() fails (e.g., attribute access raises error in __repr__)
        return "<unrepresentable>"


@dataclass
class _TraceConfig:
    """Internal trace configuration container to avoid PLR0913 (too many parameters) check."""

    capture_args: Optional[bool] = None
    max_arg_length: Optional[int] = None
    max_arg_depth: Optional[int] = None


def _format_args(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    config_obj: _TraceConfig,
) -> str:
    """
    Format function parameters as a single string for diagram arrow labels.
    
    Example output: "1, 'test', debug=True"
    
    This string will be displayed on arrows in Mermaid diagrams (e.g., `User->System: login(args...)`).
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
                arg, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
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
    Determine the name of the "target" participant (callee) in diagrams.
    """
    if target_override:
        return target_override

    if args:
        first_arg = args[0]
        # Class method
        if isinstance(first_arg, type):
            return first_arg.__name__
        # Instance method (exclude simple types)
        if hasattr(first_arg, "__class__") and not isinstance(
            first_arg, (str, int, float, bool, list, dict, set, tuple)
        ):
            return str(first_arg.__class__.__name__)

    module = inspect.getmodule(func)
    if module:
        return module.__name__.split(".")[-1]

    return "Unknown"


@dataclass
class _TraceMetadata:
    """Internal trace metadata container to avoid PLR0913 (too many parameters) check."""

    source: str
    target: str
    action: str
    trace_id: str


def _log_interaction(
    logger: logging.Logger,
    meta: _TraceMetadata,
    params: str,
) -> None:
    """Record call event."""
    req_event = FlowEvent(
        source=meta.source,
        target=meta.target,
        action=meta.action,
        message=meta.action,
        params=params,
        trace_id=meta.trace_id,
    )
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
    """Record return event."""
    result_str = ""
    final_capture = (
        config_obj.capture_args
        if config_obj.capture_args is not None
        else config.capture_args
    )

    if final_capture:
        result_str = _safe_repr(
            result, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
        )

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
    meta: _TraceMetadata,
    error: Exception,
) -> None:
    """Record exception event."""
    stack_trace = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )

    err_event = FlowEvent(
        source=meta.target,
        target=meta.source,
        action=meta.action,
        message=str(error),
        is_return=True,
        is_error=True,
        error_message=str(error),
        stack_trace=stack_trace,
        trace_id=meta.trace_id,
    )
    logger.error(
        f"{meta.target}-x{meta.source}: Error", extra={"flow_event": err_event}
    )


@overload
def trace_interaction(func: F) -> F: ...

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
    """Main trace decorator entry point."""
    final_target = target or name

    if func is not None and callable(func):
        return _create_decorator(
            func,
            source,
            final_target,
            action,
            _TraceConfig(capture_args, max_arg_length, max_arg_depth),
        )

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
    """Internal decorator factory."""
    if action is None:
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)

        meta = _TraceMetadata(current_source, current_target, action, trace_id)
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs, config_obj)

        _log_interaction(logger, meta, params_str)

        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = func(*args, **kwargs)
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
                _log_error(logger, meta, e)
                raise e

    # ... Async wrapper logic is similar (omitted)
    return cast(F, wrapper)
```