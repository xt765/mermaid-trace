import logging
import sys
from typing import Any, Dict, Optional
from .base import LoggerBackend
from ..formatters.json_fmt import JSONFormatter

class StandardLogger(LoggerBackend):
    """
    Adapter for Python's standard logging library.
    """
    def __init__(self, name: str = "logcapy", json_output: bool = True):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            if json_output:
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs: Any) -> None:
        extra = kwargs.get("extra", {})
        if context:
            extra["context"] = context
        
        self.logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, context, **kwargs)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.INFO, message, context, **kwargs)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, context, **kwargs)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, context, exc_info=exc_info, **kwargs)
        
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, context, exc_info=exc_info, **kwargs)

    def configure(self, config: Any) -> None:
        # Re-configure if needed
        pass
