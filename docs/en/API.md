# API Reference

## Table of Contents

- [Core](#core)
  - [trace / trace_interaction](#trace--trace_interaction)
  - [trace_class](#trace_class)
  - [patch_object](#patch_object)
  - [configure_flow](#configure_flow)
  - [LogContext](#logcontext)
  - [Event (Abstract Base Class)](#event-abstract-base-class)
  - [FlowEvent](#flowevent)
  - [BaseFormatter (Abstract Base Class)](#baseformatter-abstract-base-class)
  - [MermaidFormatter](#mermaidformatter)
  - [MermaidFileHandler](#mermaidfilehandler)
  - [AsyncMermaidHandler](#asyncmermaidhandler)
- [Integrations](#integrations)
  - [MermaidTraceMiddleware (FastAPI)](#mermaidtracemiddleware-fastapi)

## Core

### `trace` / `trace_interaction`

Decorator to trace function execution. Can be used with or without arguments.

```python
# Simple usage
@trace
def my_func(): ...

# Detailed usage
@trace(source="Client", target="Server", action="Login", capture_args=False)
def login(username): ...
```

**Arguments:**
- `source` (Optional[str]): The caller participant name. If `None`, inferred from `contextvars`.
- `target` (Optional[str]): The callee participant name. If `None`, inferred from class name (if method) or module name.
- `name` (Optional[str]): Alias for `target`. Explicitly sets the participant name.
- `action` (Optional[str]): Description of the interaction. If `None`, defaults to formatted function name (e.g., `process_payment` -> "Process Payment").
- `capture_args` (bool): Whether to log arguments and return values. Defaults to `True`. Set to `False` for sensitive data.
- `max_arg_length` (int): Maximum length of string representation for arguments. Defaults to 50.
- `max_arg_depth` (int): Maximum depth for nested structures in argument representation. Defaults to 1.

### `trace_class`

Class decorator to automatically apply `@trace` to methods of a class.

```python
from mermaid_trace import trace_class

@trace_class
class MyService:
    def method_a(self) -> None:
        ...
```

**Arguments:**
- `include_private` (bool): If True, traces methods starting with `_`. Defaults to False.
- `exclude` (Optional[List[str]]): Method names to skip.
- `**trace_kwargs`: Passed through to `@trace` (e.g., `capture_args=False`).

### `patch_object`

Monkey-patches a method on an object/class/module with tracing.

```python
import requests
from mermaid_trace import patch_object

patch_object(requests, "get", action="HTTP GET", target="requests")
```

**Arguments:**
- `target` (Any): Object/class/module that owns the attribute.
- `method_name` (str): Attribute name to wrap.
- `**trace_kwargs`: Passed through to `@trace`.

### `configure_flow`

Configures the global logger to output to a Mermaid file. This should be called once at application startup.

```python
def configure_flow(
    output_file: str = "flow.mmd",
    handlers: Optional[List[logging.Handler]] = None,
    append: bool = False,
    overwrite: bool = True,
    async_mode: bool = False,
    level: int = logging.INFO,
    config_overrides: Optional[Dict[str, Any]] = None,
    queue_size: Optional[int] = None,
) -> logging.Logger
```

**Arguments:**
- `output_file` (str): Path to the `.mmd` output file. Defaults to "flow.mmd".
- `handlers` (List[logging.Handler]): Optional list of custom logging handlers. If provided, `output_file` is ignored unless you include `MermaidFileHandler` manually.
- `append` (bool): If `True`, adds new handlers without removing existing ones. Defaults to `False`.
- `overwrite` (bool): If `True` (default), overwrites the output file on each restart. If `False`, appends to the existing file.
- `async_mode` (bool): If `True`, uses a non-blocking background thread for logging (QueueHandler). Recommended for production. Defaults to `False`.
- `level` (int): Logger level. Defaults to `logging.INFO`.
- `config_overrides` (Optional[Dict[str, Any]]): Overrides for global config keys (MermaidConfig fields).
- `queue_size` (Optional[int]): Queue size for async mode; overrides config.

### `LogContext`

Manages execution context (like thread-local storage) to track caller/callee relationships and trace IDs across async tasks and threads.

**Methods:**
- `LogContext.current_trace_id() -> str`: Get or generate the current Trace ID.
- `LogContext.current_participant() -> str`: Get the current active participant.
- `LogContext.scope(data)`: Synchronous context manager to temporarily update context.
- `LogContext.ascope(data)`: Asynchronous context manager (`async with`) to temporarily update context.

### `Event` (Abstract Base Class)

Abstract base class for all event types, providing a common interface for different types of events.

**Attributes:**
- `source` (str): Name of the participant that generated the event.
- `target` (str): Name of the participant that received the event.
- `action` (str): Short name describing the action performed.
- `message` (str): Detailed message describing the event.
- `timestamp` (float): Unix timestamp (seconds) when the event occurred.
- `trace_id` (str): Unique identifier for the trace session.

### `FlowEvent`

Represents a single interaction or step in the execution flow, inheriting from `Event`.

**Attributes:**
- `source` (str): The name of the participant initiating the action.
- `target` (str): The name of the participant receiving the action.
- `action` (str): A short, human-readable name for the operation.
- `message` (str): The actual text label displayed on the diagram arrow.
- `trace_id` (str): Unique identifier for the trace session.
- `timestamp` (float): Unix timestamp of when the event occurred.
- `is_return` (bool): Flag indicating if this is a response arrow.
- `is_error` (bool): Flag indicating if an exception occurred.
- `error_message` (Optional[str]): Detailed error text if `is_error` is True.
- `stack_trace` (Optional[str]): Full stack trace text if available.
- `params` (Optional[str]): Stringified representation of function arguments.
- `result` (Optional[str]): Stringified representation of the return value.
- `collapsed` (bool): Flag indicating this interaction should be visually collapsed.

### `BaseFormatter` (Abstract Base Class)

Abstract base class for all event formatters, providing a common interface for different output formats.

**Methods:**
- `format_event(event: Event) -> str`: Format an Event into the desired output string.
- `get_header(title: str) -> str`: Get the file header for the diagram format.
- `format(record: logging.LogRecord) -> str`: Format a logging record containing an event.

### `MermaidFormatter`

Custom formatter to convert Events into Mermaid sequence diagram syntax, inheriting from `BaseFormatter`.

**Methods:**
- `format_event(event: Event) -> str`: Converts an Event into a Mermaid syntax string.
- `get_header(title: str) -> str`: Returns the Mermaid sequence diagram header.

### `MermaidFileHandler`

A custom logging handler that writes `Event` objects to a Mermaid (.mmd) file.

**Features:**
- Thread-safe file writing using locks
- Automatic Mermaid header management
- Support for both overwrite and append modes
- Delay writing support for better performance

### `AsyncMermaidHandler`

A non-blocking logging handler that uses a background thread to write logs.

**Arguments:**
- `handlers` (List[logging.Handler]): A list of handlers that should receive the logs from the queue.
- `queue_size` (int): The maximum size of the queue. Default is 1000.

**Features:**
- Queue-based logging with configurable size limit
- Built-in drop policy for when queue is full
- Automatic queue flushing on application exit

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
