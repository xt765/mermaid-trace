try:
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp
except ImportError:
    BaseHTTPMiddleware = object # type: ignore
    RequestResponseEndpoint = object # type: ignore
    Request = object # type: ignore
    Response = object # type: ignore
    ASGIApp = object # type: ignore

import uuid
import time
from ..core.context import LogContext
from ..config import global_config

class LogCapyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette Middleware for automatic context capturing and logging.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = global_config.get_logger()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # 1. Generate or get Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 2. Inject context
        LogContext.clear() # Ensure clean context for this request
        LogContext.set("request_id", request_id)
        LogContext.set("method", request.method)
        LogContext.set("path", request.url.path)
        LogContext.set("client_ip", request.client.host if request.client else "unknown")
        LogContext.set("user_agent", request.headers.get("user-agent", "unknown"))

        try:
            response = await call_next(request)
            
            # Log access (optional, maybe DEBUG or INFO)
            duration = time.time() - start_time
            self.logger.info(
                f"{request.method} {request.url.path} - {response.status_code} - {duration:.4f}s",
                context=LogContext.get_all()
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {e}",
                context=LogContext.get_all(),
                exc_info=True
            )
            raise e # Re-raise to let FastAPI handle it (e.g. 500 response)
