import functools
import logging
import inspect
import reprlib
from typing import Optional, Any, Callable, Tuple, Dict
from .events import FlowEvent
from .context import LogContext

# Define a specific logger namespace for flow events
# This allows independent configuration (e.g., sending these logs to a specific file)
FLOW_LOGGER_NAME = "mermaid_trace.flow"

def get_flow_logger() -> logging.Logger:
    """
    Retrieves the dedicated logger instance for flow tracing.
    """
    return logging.getLogger(FLOW_LOGGER_NAME)

def _safe_repr(obj: Any, max_len: int = 50) -> str:
    """
    Helper to safely create a string representation of an object for diagram labels.
    
    It truncates long strings to avoid cluttering the visual diagram.
    
    Args:
        obj (Any): The object to represent.
        max_len (int): Maximum length of the string before truncation.
        
    Returns:
        str: The safe string representation (e.g., "MyObj..." or "123").
    """
    try:
        r = reprlib.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        # Fallback for objects that might raise errors in __repr__
        return "<unrepresentable>"

def _format_args(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    Formats function arguments into a concise string for the diagram label.
    
    Example output: "a=1, b=2" or "x=MyObj..."
    
    It heuristically attempts to skip 'self' or 'cls' arguments to reduce noise.
    """
    parts = []
    for arg in args:
        # Check if arg is likely 'self' or 'cls' to skip
        # Logic: If it has a __class__ attribute but is NOT a primitive type,
        # it's likely a class instance (self) or class object (cls).
        if hasattr(arg, "__class__") and not isinstance(arg, (str, int, float, bool, list, dict)):
             # This is a bit aggressive but cleaner for diagrams. 
             # It assumes the first complex object is 'self'.
             continue
        parts.append(_safe_repr(arg))
        
    for k, v in kwargs.items():
        parts.append(f"{k}={_safe_repr(v)}")
        
    return ", ".join(parts)

def trace_interaction(source: Optional[str] = None, target: Optional[str] = None, action: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to log a function call as an interaction in a sequence diagram.
    
    This decorator intercepts the function call, logs a "request" event, executes
    the function, and then logs a "response" event (or "error"). It also manages
    the `LogContext` to update the current participant, ensuring nested calls
    are correctly attributed.
    
    Args:
        source (Optional[str]): The participant initiating the call. 
                                If None, it is inferred from `LogContext.current_participant()`.
        target (Optional[str]): The participant receiving the call. 
                                If None, it tries to use the class name (if method) or module name.
        action (Optional[str]): The description of the action. 
                                If None, defaults to the function name (formatted).
                                
    Returns:
        Callable: The decorated function.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Capture variables from outer scope
        nonlocal target, action
        
        # If action is not provided, generate a readable name from function name
        # e.g., "process_payment" -> "Process Payment"
        if action is None:
            action = func.__name__.replace("_", " ").title()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Synchronous wrapper function."""
            # 1. Resolve Runtime Values
            # Determine who is calling. Default to whatever is in the context.
            current_source = source or LogContext.current_participant()
            
            # Determine who is being called.
            current_target = target
            if current_target is None:
                # Heuristic: If it's a method call, args[0] is usually 'self'.
                if args and hasattr(args[0], "__class__") and not isinstance(args[0], (str, int, float, bool, list, dict)):
                     current_target = args[0].__class__.__name__
                else:
                    # Fallback to the last part of the module name
                    current_target = func.__module__.split(".")[-1]

            logger = get_flow_logger()
            
            # Format parameters for the diagram label
            params_str = _format_args(args, kwargs)
            
            # 2. Log Request (Source -> Target)
            req_event = FlowEvent(
                source=current_source, target=current_target, 
                action=action, message=action,
                params=params_str
            )
            # We pass the event object in 'extra' so our custom handler can process it
            logger.info(f"{current_source}->{current_target}: {action}", extra={"flow_event": req_event})
            
            # 3. Execute Function within new Context Scope
            # We switch the 'participant' context to the target, so any internal calls
            # made by this function will appear to originate from 'target'.
            with LogContext.scope({"participant": current_target}):
                try:
                    result = func(*args, **kwargs)
                    
                    # 4. Log Response (Target -> Source)
                    result_str = _safe_repr(result)
                    resp_event = FlowEvent(
                        source=current_target, target=current_source, 
                        action=action, message="Return", 
                        is_return=True, result=result_str
                    )
                    logger.info(f"{current_target}->{current_source}: Return", extra={"flow_event": resp_event})
                    return result
                except Exception as e:
                    # 5. Log Error (Target --x Source)
                    err_event = FlowEvent(
                        source=current_target, target=current_source, action=action, 
                        message=str(e), is_return=True, is_error=True, error_message=str(e)
                    )
                    logger.error(f"{current_target}-x{current_source}: Error", extra={"flow_event": err_event})
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Asynchronous wrapper function (for async def)."""
            # Logic mirrors the synchronous wrapper but uses 'await' and 'async with'.
            
            current_source = source or LogContext.current_participant()
            
            current_target = target
            if current_target is None:
                if args and hasattr(args[0], "__class__") and not isinstance(args[0], (str, int, float, bool, list, dict)):
                     current_target = args[0].__class__.__name__
                else:
                    current_target = func.__module__.split(".")[-1]

            logger = get_flow_logger()
            params_str = _format_args(args, kwargs)
            
            # Log Request
            req_event = FlowEvent(
                source=current_source, target=current_target, 
                action=action, message=action,
                params=params_str
            )
            logger.info(f"{current_source}->{current_target}: {action}", extra={"flow_event": req_event})
            
            # Async context scope
            async with LogContext.ascope({"participant": current_target}):
                try:
                    # Await the actual function execution
                    result = await func(*args, **kwargs)
                    
                    # Log Response
                    result_str = _safe_repr(result)
                    resp_event = FlowEvent(
                        source=current_target, target=current_source, 
                        action=action, message="Return", 
                        is_return=True, result=result_str
                    )
                    logger.info(f"{current_target}->{current_source}: Return", extra={"flow_event": resp_event})
                    return result
                except Exception as e:
                    # Log Error
                    err_event = FlowEvent(source=current_target, target=current_source, action=action, 
                        message=str(e), is_return=True, is_error=True, error_message=str(e)
                    )
                    logger.error(f"{current_target}-x{current_source}: Error", extra={"flow_event": err_event})
                    raise

        # Check if the decorated function is a coroutine (async)
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator

# Alias for cleaner usage (e.g., @trace instead of @trace_interaction)
trace = trace_interaction
