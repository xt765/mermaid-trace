from typing import Any, TYPE_CHECKING
import time
import uuid

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
else:
    try:
        from fastapi import Request, Response
        from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    except ImportError:
        # Handle the case where FastAPI/Starlette are not installed.
        # We define dummy types to prevent NameErrors at import time,
        # but instantiation will fail explicitly in __init__.
        BaseHTTPMiddleware = object  # type: ignore[misc,assignment]
        Request = Any  # type: ignore[assignment]
        Response = Any  # type: ignore[assignment]
        RequestResponseEndpoint = Any  # type: ignore[assignment]

class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware to trace HTTP requests as interactions in the sequence diagram.
    
    This middleware acts as the entry point for tracing a web request. It:
    1. Identifies the client (Source).
    2. Logs the incoming request.
    3. Initializes the `LogContext` for the request lifecycle.
    4. Logs the response or error.
    """
    def __init__(self, app: Any, app_name: str = "FastAPI"):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application instance.
            app_name: The name of this service to appear in the diagram (e.g., "UserAPI").
        """
        if BaseHTTPMiddleware is object: # type: ignore[comparison-overlap]
             raise ImportError("FastAPI/Starlette is required to use MermaidTraceMiddleware")
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Intercepts the incoming request.
        
        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The function to call the next middleware or endpoint.
            
        Returns:
            Response: The HTTP response.
        """
        # 1. Determine Source (Client)
        # Try to get a specific ID from headers (useful for distributed tracing),
        # otherwise fallback to "Client".
        source = request.headers.get("X-Source", "Client")
        
        # Determine Trace ID
        # Check X-Trace-ID header or generate new UUID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        
        # 2. Determine Action
        # Format: "METHOD /path" (e.g., "GET /users")
        action = f"{request.method} {request.url.path}"
        
        logger = get_flow_logger()
        
        # 3. Log Request (Source -> App)
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            params=f"query={request.query_params}" if request.query_params else None,
            trace_id=trace_id
        )
        logger.info(f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event})
        
        # 4. Set Context and Process Request
        # We set the current participant to the app name.
        # `ascope` ensures this context applies to all code running within `call_next`.
        # This includes route handlers, dependencies, and other middlewares called after this one.
        async with LogContext.ascope({"participant": self.app_name, "trace_id": trace_id}):
            start_time = time.time()
            try:
                # Pass control to the application
                # This executes the actual route logic
                response = await call_next(request)
                
                # 5. Log Response (App -> Source)
                # Calculate execution duration for the response label
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)",
                    trace_id=trace_id
                )
                logger.info(f"{self.app_name}->{source}: Return", extra={"flow_event": resp_event})
                return response
                
            except Exception as e:
                # 6. Log Error (App --x Source)
                # This captures unhandled exceptions that bubble up to the middleware
                # Note: FastAPI's ExceptionHandlers might catch this before it reaches here.
                # If so, you might see a successful return with 500 status instead.
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e),
                    trace_id=trace_id
                )
                logger.error(f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event})
                raise
