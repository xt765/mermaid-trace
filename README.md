# MermaidTrace: The Python Logger That Draws Diagrams

[![PyPI version](https://img.shields.io/pypi/v/mermaid-trace.svg)](https://pypi.org/project/mermaid-trace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mermaid-trace.svg)](https://pypi.org/project/mermaid-trace/)
[![License](https://img.shields.io/pypi/l/mermaid-trace.svg)](LICENSE)
[![CI Status](https://github.com/xt765/mermaid-trace/actions/workflows/ci.yml/badge.svg)](https://github.com/xt765/mermaid-trace/actions)
[![Codecov](https://codecov.io/gh/xt765/mermaid-trace/branch/main/graph/badge.svg)](https://codecov.io/gh/xt765/mermaid-trace)

**Stop reading logs. Start watching them.**

MermaidTrace is a specialized logging tool that automatically generates [Mermaid JS](https://mermaid.js.org/) sequence diagrams from your code execution. It's perfect for visualizing complex business logic, microservice interactions, or asynchronous flows.

## ✨ Features

- **Decorator-Driven**: Just add `@trace` or `@trace_interaction` to your functions.
- **Auto-Diagramming**: Generates `.mmd` files that can be viewed in VS Code, GitHub, or Mermaid Live Editor.
- **Async Support**: Works seamlessly with `asyncio` coroutines.
- **Context Inference**: Automatically tracks nested calls and infers `source` participants using `contextvars`.
- **FastAPI Integration**: Includes middleware for zero-config HTTP request tracing.
- **CLI Tool**: Built-in viewer to preview diagrams in your browser.

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
configure_flow("my_flow.mmd")

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

## 📂 Documentation

- [English Documentation](docs/en/README.md)
- [中文文档](README_CN.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) for details.

## 📄 License

MIT
