import functools
import logging
import inspect
import reprlib
from typing import Optional, Any, Callable, Tuple, Dict, Union, TypeVar, cast

from .events import FlowEvent
from .context import LogContext

FLOW_LOGGER_NAME = "mermaid_trace.flow"

# Define generic type variable for the decorated function
F = TypeVar("F", bound=Callable[..., Any])

def get_flow_logger() -> logging.Logger:
    """Returns the dedicated logger for flow events."""
    return logging.getLogger(FLOW_LOGGER_NAME)

def _safe_repr(obj: Any, max_len: int = 50) -> str:
    """
    Safely creates a string representation of an object.
    
    Prevents massive log files by truncating long strings/objects 
    and handling exceptions during __repr__ calls (e.g. strict objects).
    """
    try:
        r = reprlib.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable>"

def _format_args(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    Formats function arguments into a single string "arg1, arg2, k=v".
    Used for the arrow label in the diagram.
    """
    parts = []
    for arg in args:
        parts.append(_safe_repr(arg))
        
    for k, v in kwargs.items():
        parts.append(f"{k}={_safe_repr(v)}")
        
    return ", ".join(parts)

def _resolve_target(func: Callable[..., Any], args: Tuple[Any, ...], target_override: Optional[str]) -> str:
    """
    Determines the name of the participant (Target) for the diagram.
    
    Resolution Priority:
    1. **Override**: If the user explicitly provided `target="Name"`, use it.
    2. **Instance Method**: If the first arg looks like `self` (has __class__), 
       use the class name.
    3. **Class Method**: If the first arg is a type (cls), use the class name.
    4. **Module Function**: Fallback to the name of the module containing the function.
    5. **Fallback**: "Unknown".
    """
    if target_override:
        return target_override
        
    # Heuristic: If it's a method call, args[0] is usually 'self'.
    if args:
        first_arg = args[0]
        # Check if it looks like a class instance
        # We check hasattr(__class__) to distinguish objects from primitives/containers broadly,
        # ensuring we don't mislabel a plain list passed as first arg to a function as a "List" participant.
        if hasattr(first_arg, "__class__") and not isinstance(first_arg, (str, int, float, bool, list, dict, type)):
             return str(first_arg.__class__.__name__)
        # Check if it looks like a class (cls) - e.g. @classmethod
        if isinstance(first_arg, type):
             return first_arg.__name__

    # Fallback to module name for standalone functions
    module = inspect.getmodule(func)
    if module:
        return module.__name__.split(".")[-1]
    return "Unknown"

def _log_interaction(logger: logging.Logger, 
                     source: str, 
                     target: str, 
                     action: str, 
                     params: str, 
                     trace_id: str) -> None:
    """
    Logs the 'Call' event (Start of function).
    Arrow: source -> target
    """
    req_event = FlowEvent(
        source=source, target=target, 
        action=action, message=action,
        params=params, trace_id=trace_id
    )
    # The 'extra' dict is critical: the Handler will pick this up to format the Mermaid line
    logger.info(f"{source}->{target}: {action}", extra={"flow_event": req_event})

def _log_return(logger: logging.Logger, 
                source: str, 
                target: str, 
                action: str, 
                result: Any, 
                trace_id: str) -> None:
    """
    Logs the 'Return' event (End of function).
    Arrow: target --> source (Dotted line return)
    
    Note: 'source' here is the original caller, 'target' is the callee.
    So the return arrow goes from target back to source.
    """
    result_str = _safe_repr(result)
    resp_event = FlowEvent(
        source=target, target=source, 
        action=action, message="Return", 
        is_return=True, result=result_str, trace_id=trace_id
    )
    logger.info(f"{target}->{source}: Return", extra={"flow_event": resp_event})

def _log_error(logger: logging.Logger, 
               source: str, 
               target: str, 
               action: str, 
               error: Exception, 
               trace_id: str) -> None:
    """
    Logs an 'Error' event if the function raises an exception.
    Arrow: target -x source (Error return)
    """
    err_event = FlowEvent(
        source=target, target=source, action=action, 
        message=str(error), is_return=True, is_error=True, error_message=str(error),
        trace_id=trace_id
    )
    logger.error(f"{target}-x{source}: Error", extra={"flow_event": err_event})

def trace_interaction(
    func: Optional[F] = None, 
    *, 
    source: Optional[str] = None, 
    target: Optional[str] = None, 
    action: Optional[str] = None
) -> Union[F, Callable[[F], F]]:
    """
    Main Decorator for tracing function execution in Mermaid diagrams.
    
    It supports two modes of operation:
    1. **Simple**: `@trace` (No arguments)
    2. **Configured**: `@trace(action="Login", target="AuthService")`
    
    Args:
        func: The function being decorated (automatically passed in simple mode).
        source: Explicit name of the caller participant (rarely used, usually inferred from Context).
        target: Explicit name of the callee participant (overrides automatic resolution).
        action: Label for the arrow (defaults to function name).
    """
    
    # Mode 1: @trace used without parentheses
    if func is not None and callable(func):
        return _create_decorator(func, source, target, action)
        
    # Mode 2: @trace(...) used with arguments -> returns a factory
    def factory(f: F) -> F:
        return _create_decorator(f, source, target, action)
    return factory

def _create_decorator(
    func: F, 
    source: Optional[str], 
    target: Optional[str], 
    action: Optional[str]
) -> F:
    """
    Constructs the actual wrapper function.
    Handles both synchronous and asynchronous functions.
    """
    
    # Pre-calculate static metadata to save time at runtime
    if action is None:
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Sync function wrapper."""
        # 1. Resolve Context
        # 'source' is who called us (from Context). 'target' is who we are (resolved from self/cls).
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)
        
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs)
        
        # 2. Log Request (Start of block)
        _log_interaction(logger, current_source, current_target, action, params_str, trace_id)
        
        # 3. Execute with New Context
        # We push 'current_target' as the NEW 'participant' (source) for any internal calls.
        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = func(*args, **kwargs)
                # 4. Log Success Return
                _log_return(logger, current_source, current_target, action, result, trace_id)
                return result
            except Exception as e:
                # 5. Log Error Return
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        """Async function wrapper (coroutine)."""
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)
        
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs)
        
        # 2. Log Request (Start of block)
        _log_interaction(logger, current_source, current_target, action, params_str, trace_id)
        
        # Use async context manager (ascope) to ensure context propagates correctly across awaits
        async with LogContext.ascope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = await func(*args, **kwargs)
                _log_return(logger, current_source, current_target, action, result, trace_id)
                return result
            except Exception as e:
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    # Detect if the wrapped function is a coroutine to choose the right wrapper
    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    return cast(F, wrapper)

# Alias for easy import
trace = trace_interaction
