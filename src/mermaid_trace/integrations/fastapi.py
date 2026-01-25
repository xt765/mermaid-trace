try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    BaseHTTPMiddleware = object # type: ignore
    Request = None # type: ignore
    Response = None # type: ignore

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger
import time

class LogCapyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware to trace HTTP requests as sequence diagram interactions.
    """
    def __init__(self, app, app_name: str = "FastAPI"):
        if BaseHTTPMiddleware is object:
             raise ImportError("FastAPI/Starlette is required to use LogCapyMiddleware")
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next):
        # 1. Determine Source (Client)
        # Try to get from header, fallback to Client IP or "Client"
        source = request.headers.get("X-Source", "Client")
        
        # 2. Determine Action
        action = f"{request.method} {request.url.path}"
        
        logger = get_flow_logger()
        
        # 3. Log Request
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            params=f"query={request.query_params}" if request.query_params else None
        )
        logger.info(f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event})
        
        # 4. Set Context and Process
        # We set the current participant to "FastAPI" (or app_name) so subsequent calls
        # inside the app will correctly originate from here.
        async with LogContext.ascope({"participant": self.app_name}):
            start_time = time.time()
            try:
                response = await call_next(request)
                
                # 5. Log Response
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)"
                )
                logger.info(f"{self.app_name}->{source}: Return", extra={"flow_event": resp_event})
                return response
                
            except Exception as e:
                # 6. Log Error
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e)
                )
                logger.error(f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event})
                raise
