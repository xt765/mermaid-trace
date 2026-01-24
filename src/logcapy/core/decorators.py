import functools
import inspect
import asyncio
import time
from typing import Callable, Type, Union, Optional, Any, Tuple, List
from ..config import global_config
from .context import LogContext

class catch:
    """
    Decorator and Context Manager to catch exceptions and log them.
    Supports both sync and async functions/contexts.
    
    Args:
        exceptions: Exception type or tuple of exceptions to catch.
        level: Logging level (e.g., "ERROR", "WARNING").
        reraise: Whether to re-raise the exception after logging.
        default_return: Value to return if exception is suppressed.
        exclude: Exception type or tuple of exceptions to exclude from catching.
        message: Custom message to prepend to the log.
    """
    def __init__(
        self,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        level: str = "ERROR",
        reraise: bool = True,
        default_return: Any = None,
        exclude: Optional[Union[Type[Exception], Tuple[Type[Exception], ...]]] = None,
        message: str = "An error occurred"
    ):
        self.exceptions = exceptions
        self.level = level
        self.reraise = reraise
        self.default_return = default_return
        self.exclude = exclude
        self.message = message
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = global_config.get_logger()
        return self._logger

    def _log_exception(self, exc: Exception, func_name: str = "<context>", args: Any = None, kwargs: Any = None):
        if self.exclude and isinstance(exc, self.exclude):
            return

        ctx = LogContext.get_all().copy()
        
        # Capture local variables if possible (tricky in decorators, easier in frame inspection)
        # For now, we capture args/kwargs for decorators
        if args is not None or kwargs is not None:
            ctx["function_args"] = str(args)
            ctx["function_kwargs"] = str(kwargs)
            
        log_method = getattr(self.logger, self.level.lower(), self.logger.error)
        log_method(
            f"{self.message}: {exc} in {func_name}",
            context=ctx,
            exc_info=True
        )

    def __call__(self, func: Callable) -> Callable:
        is_coroutine = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except self.exceptions as e:
                self._log_exception(e, func_name=func.__name__, args=args, kwargs=kwargs)
                if self.reraise:
                    raise
                return self.default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                self._log_exception(e, func_name=func.__name__, args=args, kwargs=kwargs)
                if self.reraise:
                    raise
                return self.default_return

        if is_coroutine:
            return async_wrapper
        return sync_wrapper

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val and isinstance(exc_val, self.exceptions):
            self._log_exception(exc_val)
            if not self.reraise:
                return True # Suppress exception
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    Decorator to retry a function upon exception.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to delay after each failed attempt.
        exceptions: Exception type or tuple of exceptions that trigger a retry.
    """
    def decorator(func: Callable):
        is_coroutine = inspect.iscoroutinefunction(func)
        logger = global_config.get_logger()

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Retry failed after {max_attempts} attempts for {func.__name__}: {e}", exc_info=True)
                        raise
                    
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Retry failed after {max_attempts} attempts for {func.__name__}: {e}", exc_info=True)
                        raise
                    
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff

        if is_coroutine:
            return async_wrapper
        return sync_wrapper
    return decorator
