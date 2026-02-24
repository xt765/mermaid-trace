<h1 align="center">MermaidTrace: Visualize Your Python Code Logic</h1>
<p align="center">
  <img src="docs/images/logo.png" alt="MermaidTrace Logo" width="600">
</p>

<p align="center"><strong>Stop drowning in cryptic logs. One line of code to transform complex execution logic into clear Mermaid sequence diagrams.</strong></p>

<p align="center">🌐 <strong>Language</strong>: <a href="README.md">English</a> | <a href="README_CN.md">中文</a></p>

<p align="center">
  <a href="https://blog.csdn.net/Yunyi_Chi"><img src="https://img.shields.io/badge/CSDN-玄同765-orange?style=flat-square&logo=csdn" alt="CSDN Blog"></a>
  <a href="https://github.com/xt765/mermaid-trace"><img src="https://img.shields.io/badge/GitHub-mermaid--trace-black?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="https://gitee.com/xt765/mermaid-trace"><img src="https://img.shields.io/badge/Gitee-mermaid--trace-red?style=flat-square&logo=gitee" alt="Gitee"></a>
</p>
<p align="center">
  <a href="https://pypi.org/project/mermaid-trace/"><img src="https://img.shields.io/pypi/v/mermaid-trace.svg?style=flat-square&color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pepy.tech/projects/mermaid-trace"><img src="https://img.shields.io/pepy/dt/mermaid-trace.svg?style=flat-square&color=blue&logo=pypi&logoColor=white" alt="PyPI Downloads"></a>
  <a href="https://pypi.org/project/mermaid-trace/"><img src="https://img.shields.io/pypi/pyversions/mermaid-trace.svg?style=flat-square&color=blue&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License"></a>
  <a href="https://github.com/xt765/mermaid-trace/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/xt765/mermaid-trace/ci.yml?style=flat-square&label=CI&logo=github-actions&logoColor=white" alt="CI Status"></a>
  <a href="https://docs.astral.sh/ruff/"><img src="https://img.shields.io/badge/Linter-Ruff-orange?style=flat-square&logo=ruff&logoColor=white" alt="Ruff"></a>
  <a href="https://microsoft.github.io/pyright/"><img src="https://img.shields.io/badge/Type%20Checker-Pyright-blue?style=flat-square&logo=python&logoColor=white" alt="Pyright"></a>
</p>

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph User["👤 User Code"]
        A["@trace decorator"]
        B["@trace_class"]
        C["patch_object()"]
    end

    subgraph Core["⚙️ Core Layer"]
        D["Decorators"]
        E["LogContext"]
        F["FlowEvent"]
        G["MermaidFormatter"]
        H["MermaidConfig"]
    end

    subgraph Handlers["📦 Handlers"]
        I["MermaidFileHandler"]
        J["AsyncMermaidHandler"]
        K["RotatingHandler"]
    end

    subgraph Output["📄 Output"]
        L[("flow.mmd")]
        M["🌐 Live Preview"]
    end

    subgraph Integrations["🔗 Integrations"]
        N["FastAPI Middleware"]
        O["LangChain Callback"]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    E --> F
    F --> G
    H -.-> D
    G --> I
    G --> J
    G --> K
    I --> L
    J --> L
    K --> L
    L --> M
    N --> D
    O --> D

    style User fill:#e1f5fe,stroke:#01579b
    style Core fill:#fff3e0,stroke:#e65100
    style Handlers fill:#e8f5e9,stroke:#1b5e20
    style Output fill:#fce4ec,stroke:#880e4f
    style Integrations fill:#f3e5f5,stroke:#4a148c
```

---

## ⚡️ Understand MermaidTrace in 5 Seconds

#### 1. Original Code (15+ lines)
```python
@trace(source="User", target="OrderSys")
def create_order(user_id, items):
    # Complex business logic
    if not check_inventory(items):
        return "Out of Stock"

    # Nested logic calls
    price = calculate_price(items)
    discount = get_discount(user_id)
    final = price - discount

    # External service interactions
    res = pay_service.process(final)
    if res.success:
        update_stock(items)
        send_notif(user_id)
        return "Success"
    return "Failed"
```

#### 2. Auto-Generated Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    User->>OrderSys: create_order(user_id, items)
    activate OrderSys
    OrderSys->>Inventory: check_inventory(items)
    Inventory-->>OrderSys: True
    OrderSys->>Pricing: calculate_price(items)
    Pricing-->>OrderSys: 100.0
    OrderSys->>UserDB: get_discount(user_id)
    UserDB-->>OrderSys: 5.0
    OrderSys->>PayService: process(95.0)
    activate PayService
    PayService-->>OrderSys: success
    deactivate PayService
    OrderSys->>Inventory: update_stock(items)
    OrderSys->>Notification: send_notif(user_id)
    OrderSys-->>User: "Success"
    deactivate OrderSys
```

---

## 🚀 Dynamic Demo & Online Tryout

### 🎬 Quick Demo

![MermaidTrace Master Preview](docs/images/master_preview.png)

*(Master Preview: Multi-file browsing, live-reload, and interactive pan/zoom)*

```mermaid
sequenceDiagram
    participant CLI as mermaid-trace CLI
    participant App as Python App
    participant Web as Live Preview

    Note over CLI, Web: Enable Live Preview Mode
    CLI->>Web: Start HTTP Server (localhost:8000)
    App->>App: Run Logic (with @trace decorator)
    App->>App: Auto-update flow.mmd
    Web->>Web: File Change Detected (Hot Reload)
    Web-->>CLI: Render Latest Diagram
```
*(From adding decorators to browser live preview in 10 seconds)*

### 🛠️ Try Online (Google Colab)

No local setup required. Experience core features in your browser:

[![Open In Colab](https://img.shields.io/badge/Colab-Open%20in%20Colab-blue?style=flat&logo=google-colab&logoColor=white)](https://colab.research.google.com/github/xt765/mermaid-trace/blob/main/examples/MermaidTrace_Demo.ipynb)

---

## 🎯 Why MermaidTrace? (Use Cases)

### 1. Master "Legacy" Codebases
**Pain**: Taking over a complex, undocumented legacy project with tangled function calls.
**Solution**: Add `@trace_class` or `@trace` to entry points and run the code once.
**Value**: Instantly generate a complete execution path map to understand the architecture.

### 2. Automated Technical Docs
**Pain**: Manual sequence diagrams are time-consuming and quickly become outdated.
**Solution**: Integrate MermaidTrace during development.
**Value**: Diagrams stay 100% in sync with your code logic automatically.

### 3. Debug Complex Recursion & Concurrency
**Pain**: Nested calls or async tasks produce interleaved logs that are impossible to read.
**Solution**: Use built-in async support and intelligent collapsing.
**Value**: Visualize recursion depth and concurrency flow to pinpoint logic bottlenecks.

---

## 🚀 Quick Start in 3 Steps

### 1. Install
```bash
pip install mermaid-trace
```

### 2. Add Decorators
```python
from mermaid_trace import trace, configure_flow

# Configure output file
configure_flow("my_flow.mmd")

@trace(source="User", target="AuthService")
def login(username):
    return verify_db(username)

@trace(source="AuthService", target="DB")
def verify_db(username):
    return True

login("admin")
```

### 3. View Diagram

Run the built-in CLI tool to preview in real-time (with hot-reload):

```bash
# Basic preview
mermaid-trace serve my_flow.mmd

# Master mode (Directory browsing, zoom, multi-file switching)
mermaid-trace serve . --master
# Or preview a specific file in Master mode
mermaid-trace serve .\mermaid_diagrams\examples\08-log-rotation.mmd --master
```

### 🔗 LangChain Integration
Visualize LLM chains, agents, and RAG retrieval with a single handler:
```python
from mermaid_trace.integrations.langchain import MermaidTraceCallbackHandler

handler = MermaidTraceCallbackHandler(host_name="MyAIApp")
# Pass to any LangChain object
chain.invoke({"input": "..."}, config={"callbacks": [handler]})
```

---

## ✨ Key Features

- **Decorator-Driven**: Simply add `@trace` or `@trace_interaction` to functions.
- **Auto-Instrumentation**: Use `@trace_class` to trace a whole class at once.
- **Third-Party Patching**: Use `patch_object` to trace calls inside external libraries.
- **Async Support**: Seamlessly works with `asyncio` coroutines and concurrency.
- **Enhanced Web UI**: Interactive preview server with file browsing, auto-reload, and pan/zoom support (use `--master`).
- **Intelligent Collapsing**: Automatically collapses repetitive calls and identifies loops.
- **FastAPI Integration**: Middleware for zero-config HTTP request tracing.
- **LangChain Integration**: Callback Handler for LLM chains and agent visualization.
- **Detailed Exceptions**: Captures full stack traces for errors, displayed in the diagram.

---

## 📚 Documentation

### Core Documentation

[User Guide](docs/en/USER_GUIDE.md) · [API Reference](docs/en/API.md) · [Contributing Guidelines](docs/en/CONTRIBUTING.md) · [Changelog](docs/en/CHANGELOG.md) · [License](LICENSE)

### Code Comment Documents

| Category | Links |
| :--- | :--- |
| **Core Modules** | [Context](docs/en/code_comments/src/mermaid_trace/core/context.md) · [Decorators](docs/en/code_comments/src/mermaid_trace/core/decorators.md) · [Events](docs/en/code_comments/src/mermaid_trace/core/events.md) · [Formatter](docs/en/code_comments/src/mermaid_trace/core/formatter.md) |
| **Handlers** | [Async Handler](docs/en/code_comments/src/mermaid_trace/handlers/async_handler.md) · [Mermaid Handler](docs/en/code_comments/src/mermaid_trace/handlers/mermaid_handler.md) |
| **Integrations** | [FastAPI](docs/en/code_comments/src/mermaid_trace/integrations/fastapi.md) |
| **Others** | [init](docs/en/code_comments/src/mermaid_trace/__init__.md) · [CLI](docs/en/code_comments/src/mermaid_trace/cli.md) |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/en/CONTRIBUTING.md) for details.

---

## 📄 License

MIT
