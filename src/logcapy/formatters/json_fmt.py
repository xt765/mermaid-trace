import json
import logging
import datetime
import traceback
from typing import Any

class JSONFormatter(logging.Formatter):
    """
    Formatter to output logs in JSON format.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]),
                "stack_trace": self.formatException(record.exc_info)
            }

        # Add extra fields (context)
        if hasattr(record, "context") and isinstance(record.context, dict): # type: ignore
            log_record["context"] = record.context # type: ignore

        # Merge other extra fields
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename",
                           "funcName", "levelname", "levelno", "lineno", "module",
                           "msecs", "message", "msg", "name", "pathname", "process",
                           "processName", "relativeCreated", "stack_info", "thread", "threadName",
                           "context"]:
                # Try to serialize, skip if fails or ignore
                try:
                    json.dumps(value)
                    log_record[key] = value
                except (TypeError, OverflowError):
                    pass

        return json.dumps(log_record, default=str)
