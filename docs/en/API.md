# API Reference

## Core

### `trace` / `trace_interaction`

Decorator to trace function execution.

```python
@trace(source="Client", target="Server", action="Login")
def login(username): ...
```

**Arguments:**
- `source` (Optional[str]): The caller participant name. If `None`, inferred from `contextvars`.
- `target` (Optional[str]): The callee participant name. If `None`, inferred from class name (if method) or module name.
- `action` (Optional[str]): Description of the interaction. Defaults to formatted function name.

### `configure_flow`

Configures the global logger to output to a Mermaid file.

```python
def configure_flow(output_file: str = "flow.mmd") -> logging.Logger
```

**Arguments:**
- `output_file` (str): Path to the `.mmd` output file.

## Integrations

### `MermaidTraceMiddleware` (FastAPI)

Middleware for automatic HTTP request tracing.

```python
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")
```

**Arguments:**
- `app`: The FastAPI/Starlette application.
- `app_name` (str): The name of the participant representing this application in the diagram.
