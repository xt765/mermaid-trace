from typing import Any, Dict, Optional
import sys
from .base import LoggerBackend

try:
    from loguru import logger as loguru_logger
except ImportError:
    loguru_logger = None # type: ignore

class LoguruLogger(LoggerBackend):
    """
    Adapter for Loguru.
    """
    def __init__(self, name: str = "logcapy", json_output: bool = True):
        if loguru_logger is None:
            raise ImportError("Loguru is not installed.")
        
        self.logger = loguru_logger
        self.logger.remove() # Remove default handler
        
        format_str = "{time} | {level} | {message} | {extra}"
        if json_output:
            self.logger.add(sys.stdout, serialize=True)
        else:
            self.logger.add(sys.stdout, format=format_str)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self.logger.bind(context=context or {}, **kwargs).debug(message)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self.logger.bind(context=context or {}, **kwargs).info(message)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self.logger.bind(context=context or {}, **kwargs).warning(message)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs: Any) -> None:
        opt = self.logger.opt(exception=exc_info)
        opt.bind(context=context or {}, **kwargs).error(message)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs: Any) -> None:
        opt = self.logger.opt(exception=exc_info)
        opt.bind(context=context or {}, **kwargs).critical(message)

    def configure(self, config: Any) -> None:
        pass
