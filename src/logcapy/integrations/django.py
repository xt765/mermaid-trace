import uuid
import time
from typing import Callable
from ..core.context import LogContext
from ..config import global_config

try:
    from django.http import HttpRequest, HttpResponse
except ImportError:
    HttpRequest = object # type: ignore
    HttpResponse = object # type: ignore

class LogCapyMiddleware:
    """
    Django Middleware for LogCapy.
    """
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = global_config.get_logger()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()
        
        # 1. Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 2. Context
        LogContext.clear()
        LogContext.set("request_id", request_id)
        LogContext.set("method", request.method)
        LogContext.set("path", request.path)
        LogContext.set("user_agent", request.META.get("HTTP_USER_AGENT"))
        
        try:
            response = self.get_response(request)
            
            duration = time.time() - start_time
            self.logger.info(
                f"{request.method} {request.path} - {response.status_code} - {duration:.4f}s",
                context=LogContext.get_all()
            )
            
            response["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Unhandled exception in {request.method} {request.path}: {e}",
                context=LogContext.get_all(),
                exc_info=True
            )
            raise e
