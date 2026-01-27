# MermaidTrace: The Python Logger That Draws Diagrams

🌐 **Language**: [English](README.md) | [中文](README_CN.md)

[![PyPI version](https://img.shields.io/pypi/v/mermaid-trace.svg?style=flat-square&color=blue)](https://pypi.org/project/mermaid-trace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mermaid-trace.svg?style=flat-square&color=blue)](https://pypi.org/project/mermaid-trace/)
[![License](https://img.shields.io/github/license/xt765/mermaid-trace?style=flat-square)](LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/xt765/mermaid-trace/ci.yml?style=flat-square&label=CI)](https://github.com/xt765/mermaid-trace/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/xt765/mermaid-trace?style=flat-square&logo=codecov)](https://codecov.io/gh/xt765/mermaid-trace)

---

## 📋 Overview

**Stop reading logs. Start watching them.**

MermaidTrace is a specialized logging tool that automatically generates [Mermaid JS](https://mermaid.js.org/) sequence diagrams from your code execution. It's perfect for visualizing complex business logic, microservice interactions, or asynchronous flows.

---

## 📚 Documentation

### Core Documentation

[User Guide](docs/en/USER_GUIDE.md) · [API Reference](docs/en/API.md) · [Contributing Guidelines](docs/en/CONTRIBUTING.md) · [Changelog](docs/en/CHANGELOG.md) · [License](docs/en/LICENSE)

### Code Comment Documents (Chinese)

| Category | Links |
| :--- | :--- |
| **Core Modules** | [Context](docs/zh/code_comments/src/mermaid_trace/core/context.md) · [Decorators](docs/zh/code_comments/src/mermaid_trace/core/decorators.md) · [Events](docs/zh/code_comments/src/mermaid_trace/core/events.md) · [Formatter](docs/zh/code_comments/src/mermaid_trace/core/formatter.md) |
| **Handlers** | [Async Handler](docs/zh/code_comments/src/mermaid_trace/handlers/async_handler.md) · [Mermaid Handler](docs/zh/code_comments/src/mermaid_trace/handlers/mermaid_handler.md) |
| **Integrations** | [FastAPI](docs/zh/code_comments/src/mermaid_trace/integrations/fastapi.md) |
| **Others** | [init](docs/zh/code_comments/src/mermaid_trace/__init__.md) · [CLI](docs/zh/code_comments/src/mermaid_trace/cli.md) |

---

## ✨ Key Features

- **Decorator-Driven**: Just add `@trace` or `@trace_interaction` to your functions.
- **Auto-Instrumentation**: Use `@trace_class` to trace a whole class at once.
- **Third-Party Patching**: Use `patch_object` to trace calls inside external libraries.
- **Auto-Diagramming**: Generates `.mmd` files that can be viewed in VS Code, GitHub, or Mermaid Live Editor.
- **Async Support**: Works seamlessly with `asyncio` coroutines.
- **Context Inference**: Automatically tracks nested calls and infers `source` participants using `contextvars`.
- **Intelligent Collapsing**: Prevents diagram explosion by collapsing repetitive high-frequency calls and identifying recurring patterns (e.g., loops).
- **Detailed Exceptions**: Captures full stack traces for errors, displayed in interactive notes.
- **Simplified Objects**: Automatically cleans up memory addresses (e.g., `<__main__.Obj at 0x...>` -> `<Obj>`) and **groups consecutive identical items** in lists/tuples (e.g., `[<Obj> x 5]`) for cleaner diagrams.
- **Log Rotation**: Supports `RotatingMermaidFileHandler` for handling long-running systems by splitting logs based on size or time.
- **FastAPI Integration**: Includes middleware for zero-config HTTP request tracing, supporting distributed tracing via `X-Trace-ID` and `X-Source` headers.
- **CLI Tool**: Built-in viewer with live-reload to preview diagrams in your browser.

---

## 🚀 Quick Start

### Installation

```bash
pip install mermaid-trace
```

### Basic Usage

```python
from mermaid_trace import trace, configure_flow
import time

# 1. Configure output
# Recommendation: Store diagrams in a dedicated directory (e.g., mermaid_diagrams/)
configure_flow("mermaid_diagrams/my_flow.mmd", async_mode=True)

# 2. Add decorators
@trace(source="Client", target="PaymentService", action="Process Payment")
def process_payment(amount):
    if check_balance(amount):
        return "Success"
    return "Failed"

@trace(source="PaymentService", target="Database", action="Check Balance")
def check_balance(amount):
    return True

# 3. Run your code
process_payment(100)
```

### Configuration

You can configure global settings via `configure_flow` or environment variables to control performance and behavior.

```python
configure_flow(
    "flow.mmd", 
    overwrite=True,    # Overwrite the file on each restart (default: True)
    level=logging.DEBUG, 
    queue_size=5000,  # Increase buffer for high-throughput
    config_overrides={
        "capture_args": False,       # Disable arg capturing for max performance
        "max_string_length": 100     # Increase string truncation limit
    }
)
```

**Environment Variables:**
- `MERMAID_TRACE_CAPTURE_ARGS` (true/false)
- `MERMAID_TRACE_MAX_STRING_LENGTH` (int)
- `MERMAID_TRACE_MAX_ARG_DEPTH` (int)
- `MERMAID_TRACE_QUEUE_SIZE` (int)

### Nested Calls (Context Inference)

You don't need to specify `source` every time. MermaidTrace infers it from the current context.

```python
@trace(source="Client", target="API")
def main():
    # Inside here, current participant is "API"
    service_call()

@trace(target="Service") # source inferred as "API"
def service_call():
    pass
```

### FastAPI Integration

```python
from fastapi import FastAPI
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app = FastAPI()
app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### CLI Viewer

Visualize your generated `.mmd` files instantly:

```bash
mermaid-trace serve my_flow.mmd
```

### Examples

Check out the [examples/](examples/) directory for a complete set of demos covering all features:
- **[Basic Usage](examples/01_basic_usage.py)**: Decorators and class methods.
- **[Advanced Instrumentation](examples/02_advanced_instrumentation.py)**: `@trace_class` and `patch_object` for third-party libraries.
- **[Async & Concurrency](examples/03_async_concurrency.py)**: Tracing `asyncio` and concurrent tasks.
- **[Error Handling](examples/04_error_handling.py)**: Stack trace capture and error rendering.
- **[Intelligent Collapsing](examples/05_intelligent_collapsing.py)**: Keeping diagrams clean in loops.
- **[FastAPI Integration](examples/06_fastapi_integration.py)**: Middleware for web apps.
- **[Full Stack App](examples/07_full_stack_app.py)**: Comprehensive example with FastAPI, SQLAlchemy, and Pydantic.
- **[Log Rotation](examples/08-log-rotation.py)**: Handling long-running processes with file rotation.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) for details.

---

## 📄 License

MIT
