# File: src/mermaid_trace/integrations/fastapi.py

## Overview
The `fastapi.py` module implements the `MermaidTraceMiddleware` for FastAPI applications. This middleware automatically traces HTTP requests and responses, generating Mermaid sequence diagrams that visualize the flow of requests through the FastAPI application and any downstream services it interacts with.

## Core Functionality Analysis

### 1. `MermaidTraceMiddleware` Class
This class implements FastAPI middleware that:
- **Request Tracing**: Automatically traces incoming HTTP requests, creating a new trace ID if one isn't provided.
- **Context Propagation**: Propagates the trace context through the request lifecycle, ensuring all nested operations are included in the same diagram.
- **Response Tracking**: Captures response information, including status codes and response times, to complete the request flow in the diagram.
- **Header Support**: Reads and writes trace-related headers (e.g., `X-Trace-ID`, `X-Source`) to support distributed tracing across multiple services.

### 2. Middleware Flow
The FastAPI middleware processes requests through the following steps:
1. **Request Reception**: Intercepts incoming HTTP requests before they reach the route handler.
2. **Context Initialization**: Creates or extracts the trace ID and sets up the logging context.
3. **Request Processing**: Allows the request to be processed by the route handler while maintaining the trace context.
4. **Response Capture**: Captures the response information after the route handler completes.
5. **Diagram Update**: Updates the Mermaid diagram with the complete request-response flow.
6. **Response Return**: Returns the response to the client, including any trace headers.

### 3. Distributed Tracing Support
- **Trace ID Propagation**: Reads `X-Trace-ID` headers from incoming requests and propagates them to downstream services.
- **Source Identification**: Uses `X-Source` headers to identify the source of requests in distributed systems.
- **Service Boundary**: Clearly marks service boundaries in diagrams, making it easy to see when requests cross between services.

### 4. Configuration Options
The middleware supports various configuration options:
- **`app_name`**: The name of the FastAPI application, used as the participant name in diagrams.
- **`capture_headers`**: Whether to capture HTTP headers in the diagram for debugging.
- **`capture_body`**: Whether to capture request/response bodies (with size limits).
- **`exclude_paths`**: Paths to exclude from tracing to reduce noise in diagrams.

### 5. Performance Considerations
- **Lightweight Processing**: Minimal overhead added to request processing to ensure fast API performance.
- **Asynchronous Support**: Fully compatible with FastAPI's asynchronous request handling.
- **Selective Tracing**: Allows excluding certain paths or endpoints to focus on critical flows.

## Source Code with English Comments

```python
"""
FastAPI integration module

This module provides middleware for FastAPI applications that automatically
 traces HTTP requests and generates Mermaid sequence diagrams showing
 the flow of requests through the application and to downstream services.
"""

from typing import Dict, Optional, Set, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders

from ..core.context import LogContext
from ..core.decorators import trace_interaction
from ..core.events import FlowEvent
from ..handlers.async_handler import AsyncMermaidHandler


class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic request tracing and Mermaid diagram generation.
    
    This middleware intercepts HTTP requests and responses, creating a trace context
    and generating Mermaid sequence diagrams that visualize the request flow.
    """

    def __init__(
        self,
        app: FastAPI,
        app_name: str = "FastAPI",
        capture_headers: bool = False,
        capture_body: bool = False,
        max_body_length: int = 1000,
        exclude_paths: Optional[Set[str]] = None,
        **handler_kwargs,
    ):
        """
        Initialize the Mermaid trace middleware.
        
        Args:
            app: FastAPI application instance
            app_name: Name of the application (used as participant in diagrams)
            capture_headers: Whether to capture HTTP headers
            capture_body: Whether to capture request/response bodies
            max_body_length: Maximum length of captured bodies
            exclude_paths: Paths to exclude from tracing
            **handler_kwargs: Additional keyword arguments for the Mermaid handler
        """
        super().__init__(app)
        self.app_name = app_name
        self.capture_headers = capture_headers
        self.capture_body = capture_body
        self.max_body_length = max_body_length
        self.exclude_paths = exclude_paths or set()
        
        # Create async handler for processing events
        self.handler = AsyncMermaidHandler(**handler_kwargs)

    async def dispatch(
        self, request: Request, call_next
    ) -> Response:
        """
        Dispatch request through middleware and trace the flow.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response
        """
        # Skip tracing for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract or generate trace ID
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = LogContext.current_trace_id()

        # Extract source from headers if provided
        source = request.headers.get("X-Source", "Client")

        # Set up context
        context_data = {
            "trace_id": trace_id,
            "participant": self.app_name,
            "request_id": trace_id,
        }

        # Capture request details
        request_method = request.method
        request_path = request.url.path
        request_params = dict(request.query_params)

        # Create request event
        request_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=f"{request_method} {request_path}",
            message=f"HTTP Request",
            params=str(request_params),
            trace_id=trace_id,
        )

        # Log request event
        import logging
        logger = logging.getLogger("mermaid_trace.flow")
        logger.info(
            f"{source}->{self.app_name}: {request_method} {request_path}",
            extra={"flow_event": request_event}
        )

        # Process request with context
        response = None
        try:
            with LogContext.scope(context_data):
                # Call next middleware or route handler
                response = await call_next(request)

                # Capture response details
                status_code = response.status_code
                response_time = getattr(response, "elapsed", None)

                # Create response event
                response_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=f"Response {status_code}",
                    message=f"HTTP Response",
                    result=f"Status: {status_code}" + (
                        f", Time: {response_time}ms" if response_time else ""),
                    is_return=True,
                    trace_id=trace_id,
                )

                # Log response event
                logger.info(
                    f"{self.app_name}->{source}: Response {status_code}",
                    extra={"flow_event": response_event}
                )

        except Exception as e:
            # Create error event
            error_event = FlowEvent(
                source=self.app_name,
                target=source,
                action=f"Error",
                message=f"Exception",
                error_message=str(e),
                is_return=True,
                is_error=True,
                trace_id=trace_id,
            )

            # Log error event
            logger.error(
                f"{self.app_name}->x{source}: Error",
                extra={"flow_event": error_event}
            )
            raise

        finally:
            # Add trace ID to response headers
            if response and hasattr(response, "headers"):
                response.headers["X-Trace-ID"] = trace_id

        return response


# Helper function to add middleware to FastAPI app
def add_mermaid_trace_middleware(
    app: FastAPI,
    **kwargs,
) -> None:
    """
    Add Mermaid trace middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
        **kwargs: Middleware configuration arguments
    """
    app.add_middleware(MermaidTraceMiddleware, **kwargs)
```