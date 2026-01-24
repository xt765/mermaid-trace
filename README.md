# LogCapy - Python's Calm Logger 🦦

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/logcapy.svg)](https://pypi.org/project/logcapy/)
[![Python versions](https://img.shields.io/pypi/pyversions/logcapy.svg)](https://pypi.org/project/logcapy/)
[![License](https://img.shields.io/github/license/username/logcapy.svg)](https://github.com/username/logcapy/blob/main/LICENSE)
[![Build Status](https://github.com/username/logcapy/actions/workflows/ci.yml/badge.svg)](https://github.com/username/logcapy/actions)
[![Code Coverage](https://img.shields.io/codecov/c/github/username/logcapy)](https://codecov.io/gh/username/logcapy)

**[English](README.md) | [简体中文](README_CN.md)**

</div>

**LogCapy** is a powerful Python library that seamlessly integrates exception handling with structured logging. It aims to make error management and log output automated, structured, and stress-free.

Inspired by the calm demeanor of the Capybara, LogCapy keeps your logs composed even when your code is panicking.

## ✨ Key Features

- **🛡️ Smart Decorators**: `@logcapy.catch` automatically captures exceptions with full context (args, stack trace) and logs them structurally.
- **🔄 Robust Retry Mechanism**: `@logcapy.retry` provides configurable retry logic (exponential backoff) with integrated logging for each attempt.
- **🆔 Context Awareness**: Automatically tracks `Request ID`, `User ID`, and other context across async/sync calls using `contextvars`.
- **🪵 Backend Agnostic**: Works out-of-the-box with standard `logging` or seamlessly integrates with `loguru`.
- **📊 Structured Logging**: Native JSON output support, ready for ELK Stack, Splunk, or Datadog.
- **🔌 Framework Integration**: Ready-to-use middleware for **FastAPI**, **Flask**, and **Django** to automatically capture request context.
- **⚡ Async Native**: Built from the ground up to support `asyncio` and Python's modern async ecosystem.

## 📦 Installation

Install LogCapy via pip:

```bash
pip install logcapy
```

Install with extra dependencies (e.g., for `loguru` support or web frameworks):

```bash
# For Loguru support
pip install logcapy[loguru]

# For Web Frameworks
pip install logcapy[fastapi]
pip install logcapy[flask]
pip install logcapy[django]

# Install everything
pip install logcapy[all]
```

## 🚀 Quick Start

### Basic Usage

```python
from logcapy import configure, catch
import asyncio

# 1. Configure globally (output JSON logs to stdout)
configure(backend="stdlib", json_output=True)

# 2. Decorate your functions
@catch(default_return=None)
async def dangerous_task(x, y):
    return x / y

# 3. Run safely
asyncio.run(dangerous_task(1, 0))
```

**Output Log:**
```json
{
  "timestamp": "2023-10-27T10:00:00.123456",
  "level": "ERROR",
  "message": "An error occurred: division by zero in dangerous_task",
  "exception": {
    "type": "ZeroDivisionError",
    "message": "division by zero",
    "stack_trace": "..."
  },
  "context": {
    "function_args": "(1, 0)",
    "function_kwargs": "{}"
  }
}
```

### Retry Mechanism

```python
from logcapy import retry

@retry(max_attempts=3, delay=1, backoff=2)
def unstable_network_call():
    # Will retry 3 times with exponential backoff (1s, 2s, 4s)
    # Each failure is logged automatically
    raise ConnectionError("Network is down")
```

### FastAPI Integration

LogCapy provides middleware to automatically handle Request IDs and context logging.

```python
from fastapi import FastAPI
from logcapy.integrations.fastapi import LogCapyMiddleware

app = FastAPI()
app.add_middleware(LogCapyMiddleware)

@app.get("/")
async def root():
    # Request ID is automatically injected into logs
    return {"message": "Hello World"}
```

## ⚙️ Configuration

You can configure LogCapy to use different backends (`stdlib` or `loguru`) and output formats.

```python
from logcapy import configure

# Use Loguru as backend
configure(backend="loguru", json_output=True)

# Use Standard Logging (default)
configure(backend="stdlib", json_output=False)
```

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Hatch or Pip

### Running Tests

```bash
pip install .[all]
pip install pytest
pytest
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
