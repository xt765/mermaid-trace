# API Reference

## Core

### `trace` / `trace_interaction`

Decorator to trace function execution. Can be used with or without arguments.

```python
# Simple usage
@trace
def my_func(): ...

# Detailed usage
@trace(source="Client", target="Server", action="Login")
def login(username): ...
```

**Arguments:**
- `source` (Optional[str]): The caller participant name. If `None`, inferred from `contextvars`.
- `target` (Optional[str]): The callee participant name. If `None`, inferred from class name (if method) or module name.
- `action` (Optional[str]): Description of the interaction. If `None`, defaults to formatted function name (e.g., `process_payment` -> "Process Payment").

### `configure_flow`

Configures the global logger to output to a Mermaid file. This should be called once at application startup.

```python
def configure_flow(output_file: str = "flow.mmd") -> logging.Logger
```

**Arguments:**
- `output_file` (str): Path to the `.mmd` output file. Defaults to "flow.mmd".

### `LogContext`

Manages execution context (like thread-local storage) to track caller/callee relationships and trace IDs across async tasks and threads.

**Methods:**
- `LogContext.current_trace_id() -> str`: Get or generate the current Trace ID.
- `LogContext.current_participant() -> str`: Get the current active participant.
- `LogContext.scope(data)`: Synchronous context manager to temporarily update context.
- `LogContext.ascope(data)`: Asynchronous context manager (`async with`) to temporarily update context.

## Integrations

### `MermaidTraceMiddleware` (FastAPI)

Middleware for automatic HTTP request tracing. Captures request path, method, status code, and timing.

```python
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")
```

**Arguments:**
- `app`: The FastAPI/Starlette application.
- `app_name` (str): The name of the participant representing this application in the diagram.

**Headers Support:**
- `X-Source`: If sent by the client, sets the source participant name.
- `X-Trace-ID`: If sent, uses this ID for the trace session; otherwise generates a new UUID.
