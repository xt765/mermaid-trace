# User Guide

## Introduction

MermaidTrace bridges the gap between code execution and architectural visualization. Unlike static analysis tools, it traces *actual* runtime calls, giving you a true picture of your system's behavior.

## How It Works

1.  **Decorate**: You place `@trace` on functions you want to appear in the diagram.
2.  **Intercept**: When the function runs, MermaidTrace logs a "Request" event (`->>`).
3.  **Execute**: The function body executes.
4.  **Return**: MermaidTrace logs a "Return" event (`-->>`) with the return value.
5.  **Visualize**: The events are written to a `.mmd` file, which renders as a sequence diagram.

## Concurrency & Trace IDs

MermaidTrace is built for modern async applications. It automatically handles concurrent requests by assigning a unique **Trace ID** to each flow.

- **Automatic**: A new Trace ID is generated when a flow starts (if one doesn't exist).
- **Propagation**: The ID is stored in `contextvars`, ensuring it follows `await` calls and background tasks automatically.
- **FastAPI**: The middleware automatically extracts `X-Trace-ID` from headers or generates a new one.

*Note: Currently, all traces are written to the same file. Use the Trace ID in the logs to filter specific sessions if needed.*

## Context Inference

One of the most powerful features is **Context Inference**.

In a sequence diagram, every arrow has a `Source` and a `Target`.
- `Target` is easy: it's the function/class being called.
- `Source` is hard: it's *who called* the function.

MermaidTrace uses Python's `contextvars` to track the "Current Participant".

**Example:**
1.  `A` calls `B`.
2.  Inside `A`, the context is set to "A".
3.  When `B` is decorated with `@trace`, it sees the context is "A", so it draws `A ->> B`.
4.  Inside `B`, the context is updated to "B".
5.  If `B` calls `C`, `C` sees the context is "B", so it draws `B ->> C`.

This means you usually only need to set the `source` on the *entry point* (the first function).

## Advanced Configuration

### Async Mode (Performance)
For high-throughput production environments, enable `async_mode` to offload file writing to a background thread. This ensures your application's main thread is never blocked by disk I/O.

```python
configure_flow("flow.mmd", async_mode=True)
```

### Data Capture Control
You can control how function arguments and return values are recorded to keep diagrams clean and secure.

```python
# Hide sensitive data
@trace(capture_args=False)
def login(password):
    pass

# Truncate long strings (default: 50 chars)
@trace(max_arg_length=10)
def process_large_data(data):
    pass
```

### Explicit Naming
If the automatic class/function name inference isn't what you want, you can explicitly name the participant.

```python
@trace(name="AuthService")  # "AuthService" will appear in the diagram
def login():
    pass
```

### Flexible Handler Configuration
You can add MermaidTrace to an existing logging setup or append multiple handlers.

```python
# Append to existing handlers instead of clearing them
configure_flow("flow.mmd", append=True)
```

## CLI Viewer

To view your diagrams, use the CLI:

```bash
mermaid-trace serve flow.mmd --port 8000
```

This starts a local server and opens your browser. It monitors the file for changes and auto-refreshes the page instantly.
