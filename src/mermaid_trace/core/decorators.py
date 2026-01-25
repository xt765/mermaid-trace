import functools
import logging
import inspect
import reprlib
from typing import Optional, Any
from .events import FlowEvent
from .context import LogContext

# Define a specific logger for flow events
FLOW_LOGGER_NAME = "mermaid_trace.flow"

def get_flow_logger():
    return logging.getLogger(FLOW_LOGGER_NAME)

def _safe_repr(obj: Any, max_len: int = 50) -> str:
    """Helper to safely format object for diagrams."""
    try:
        r = reprlib.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable>"

def _format_args(args, kwargs) -> str:
    """Format arguments into a string like 'a=1, b=2'."""
    parts = []
    for arg in args:
        # Check if arg is 'self' or 'cls' to skip
        if hasattr(arg, "__class__") and not isinstance(arg, (str, int, float, bool, list, dict)):
             # Heuristic: skip instance/class objects which are likely self/cls
             # This is a bit aggressive but cleaner for diagrams
             continue
        parts.append(_safe_repr(arg))
        
    for k, v in kwargs.items():
        parts.append(f"{k}={_safe_repr(v)}")
        
    return ", ".join(parts)

def trace_interaction(source: Optional[str] = None, target: Optional[str] = None, action: Optional[str] = None):
    """
    Decorator to log a function call as an interaction in a sequence diagram.
    
    Args:
        source: The participant initiating the call. If None, inferred from context.
        target: The participant receiving the call. If None, uses function name/module.
        action: The description of the action. If None, uses function name.
    """
    def decorator(func):
        # Determine target name if not provided
        nonlocal target, action
        
        # If target not provided, try to guess from class or module
        # This is tricky because at decoration time we might not know the class instance
        # For now, if target is None, we'll determine it at runtime or use module name
        
        if action is None:
            action = func.__name__.replace("_", " ").title()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve runtime values
            current_source = source or LogContext.current_participant()
            
            # If target is still None, try to use class name if it's a method
            current_target = target
            if current_target is None:
                if args and hasattr(args[0], "__class__") and not isinstance(args[0], (str, int, float, bool, list, dict)):
                     # Heuristic: first arg is 'self'?
                     current_target = args[0].__class__.__name__
                else:
                    current_target = func.__module__.split(".")[-1] # Fallback to module name

            logger = get_flow_logger()
            
            # Format params
            params_str = _format_args(args, kwargs)
            
            # 1. Log Request
            req_event = FlowEvent(
                source=current_source, target=current_target, 
                action=action, message=action,
                params=params_str
            )
            logger.info(f"{current_source}->{current_target}: {action}", extra={"flow_event": req_event})
            
            # 2. Set new context scope (current_target becomes the active participant)
            # We use scope() to ensure it pops back after execution
            with LogContext.scope({"participant": current_target}):
                try:
                    result = func(*args, **kwargs)
                    
                    # 3. Log Response
                    result_str = _safe_repr(result)
                    resp_event = FlowEvent(
                        source=current_target, target=current_source, 
                        action=action, message="Return", 
                        is_return=True, result=result_str
                    )
                    logger.info(f"{current_target}->{current_source}: Return", extra={"flow_event": resp_event})
                    return result
                except Exception as e:
                    # 4. Log Error
                    err_event = FlowEvent(
                        source=current_target, target=current_source, action=action, 
                        message=str(e), is_return=True, is_error=True, error_message=str(e)
                    )
                    logger.error(f"{current_target}-x{current_source}: Error", extra={"flow_event": err_event})
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_source = source or LogContext.current_participant()
            
            current_target = target
            if current_target is None:
                if args and hasattr(args[0], "__class__") and not isinstance(args[0], (str, int, float, bool, list, dict)):
                     current_target = args[0].__class__.__name__
                else:
                    current_target = func.__module__.split(".")[-1]

            logger = get_flow_logger()
            params_str = _format_args(args, kwargs)
            
            req_event = FlowEvent(
                source=current_source, target=current_target, 
                action=action, message=action,
                params=params_str
            )
            logger.info(f"{current_source}->{current_target}: {action}", extra={"flow_event": req_event})
            
            # Async context scope
            async with LogContext.ascope({"participant": current_target}):
                try:
                    result = await func(*args, **kwargs)
                    
                    result_str = _safe_repr(result)
                    resp_event = FlowEvent(
                        source=current_target, target=current_source, 
                        action=action, message="Return", 
                        is_return=True, result=result_str
                    )
                    logger.info(f"{current_target}->{current_source}: Return", extra={"flow_event": resp_event})
                    return result
                except Exception as e:
                    err_event = FlowEvent(source=current_target, target=current_source, action=action, 
                        message=str(e), is_return=True, is_error=True, error_message=str(e)
                    )
                    logger.error(f"{current_target}-x{current_source}: Error", extra={"flow_event": err_event})
                    raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator

# Alias for cleaner usage
trace = trace_interaction
