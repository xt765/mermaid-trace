"""
FastAPI Integration Module

This module provides middleware for integrating MermaidTrace with FastAPI applications.
It automatically traces HTTP requests and responses, converting them into Mermaid
sequence diagram events.
"""

from typing import Any, TYPE_CHECKING
import time
import uuid

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

# Conditional imports to support optional FastAPI dependency
if TYPE_CHECKING:
    # For type checking only, import the actual FastAPI/Starlette types
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
else:
    try:
        # Try to import FastAPI/Starlette at runtime
        from fastapi import Request, Response
        from starlette.middleware.base import (
            BaseHTTPMiddleware,
            RequestResponseEndpoint,
        )
    except ImportError:
        # Handle the case where FastAPI/Starlette are not installed
        # Define dummy types to prevent NameErrors at import time
        # Instantiation will fail explicitly in __init__
        BaseHTTPMiddleware = object  # type: ignore[misc,assignment]
        Request = Any  # type: ignore[assignment]
        Response = Any  # type: ignore[assignment]
        RequestResponseEndpoint = Any  # type: ignore[assignment]


class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware to trace HTTP requests as interactions in the sequence diagram.

    This middleware acts as the entry point for tracing web requests, handling:
    1. Identification of the client (Source participant)
    2. Logging of incoming requests
    3. Initialization of the `LogContext` for the request lifecycle
    4. Logging of responses or errors
    5. Cleanup of context after request completion
    """

    def __init__(self, app: Any, app_name: str = "FastAPI"):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI application instance
            app_name: The name of this service to appear in the diagram (e.g., "UserAPI")

        Raises:
            ImportError: If FastAPI/Starlette are not installed
        """
        # Check if FastAPI is installed by verifying BaseHTTPMiddleware is not our dummy object
        if BaseHTTPMiddleware is object:  # type: ignore[comparison-overlap]
            raise ImportError(
                "FastAPI/Starlette is required to use MermaidTraceMiddleware"
            )

        # Initialize the parent BaseHTTPMiddleware
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Intercepts and processes incoming HTTP requests.

        This method is called for each incoming request and handles the full
        request-response cycle tracing.

        Args:
            request (Request): The incoming HTTP request object
            call_next (RequestResponseEndpoint): Function to call the next middleware or endpoint

        Returns:
            Response: The HTTP response object
        """
        # 1. Determine Source (Client participant)
        # Try to get a specific ID from X-Source header (useful for distributed tracing),
        # otherwise fallback to "Client"
        source = request.headers.get("X-Source", "Client")

        # 2. Determine Trace ID
        # Check for X-Trace-ID header (for distributed tracing) or generate new UUID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())

        # 3. Determine Action name
        # Format: "METHOD /path" (e.g., "GET /users", "POST /items")
        action = f"{request.method} {request.url.path}"

        logger = get_flow_logger()

        # 4. Log Request (Source -> App)
        # Create and log the initial request event
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            params=f"query={request.query_params}" if request.query_params else None,
            trace_id=trace_id,
        )
        logger.info(
            f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event}
        )

        # 5. Set Context and Process Request
        # Use async context manager to set the current participant to the app name
        # This context will be inherited by all code called within call_next()
        async with LogContext.ascope(
            {"participant": self.app_name, "trace_id": trace_id}
        ):
            start_time = time.time()
            try:
                # Pass control to the next middleware or endpoint
                # This executes the actual route logic and returns the response
                response = await call_next(request)

                # 6. Log Success Response (App -> Source)
                # Calculate execution duration in milliseconds
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)",
                    trace_id=trace_id,
                )
                logger.info(
                    f"{self.app_name}->{source}: Return",
                    extra={"flow_event": resp_event},
                )
                return response

            except Exception as e:
                # 7. Log Error Response (App --x Source)
                # This captures unhandled exceptions that bubble up to the middleware
                # Note: FastAPI's ExceptionHandlers might catch some exceptions before they reach here
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e),
                    trace_id=trace_id,
                )
                logger.error(
                    f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event}
                )
                # Re-raise the exception to maintain normal error handling flow
                raise
