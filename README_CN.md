# MermaidTrace: 能画图的 Python 日志工具

[![PyPI version](https://img.shields.io/pypi/v/mermaid-trace.svg?style=flat-square)](https://pypi.org/project/mermaid-trace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mermaid-trace.svg?style=flat-square)](https://pypi.org/project/mermaid-trace/)
[![License](https://img.shields.io/pypi/l/mermaid-trace.svg?style=flat-square)](LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/xt765/mermaid-trace/ci.yml?style=flat-square&label=CI)](https://github.com/xt765/mermaid-trace/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/xt765/mermaid-trace?style=flat-square&logo=codecov)](https://codecov.io/gh/xt765/mermaid-trace)

**别再干读日志了。开始“看”懂它们吧。**

MermaidTrace 是一个专业的日志工具，能从你的代码执行中自动生成 [Mermaid JS](https://mermaid.js.org/) 时序图。它非常适合可视化复杂的业务逻辑、微服务交互或异步流程。

## ✨ 特性

- **装饰器驱动**：只需在函数上添加 `@trace` 或 `@trace_interaction` 即可。
- **自动绘图**：生成 `.mmd` 文件，可在 VS Code、GitHub 或 Mermaid Live Editor 中查看。
- **异步支持**：无缝支持 `asyncio` 协程。
- **上下文推断**：利用 `contextvars` 自动追踪嵌套调用并推断 `source`（调用方）参与者。
- **FastAPI 集成**：内置中间件，实现零配置的 HTTP 请求追踪。
- **CLI 工具**：内置查看器，可在浏览器中即时预览图表。

## 🚀 快速开始

### 安装

```bash
pip install mermaid-trace
```

### 基础用法

```python
from mermaid_trace import trace, configure_flow
import time

# 1. 配置输出文件
configure_flow("my_flow.mmd")

# 2. 添加装饰器
@trace(source="Client", target="PaymentService", action="Process Payment")
def process_payment(amount):
    if check_balance(amount):
        return "Success"
    return "Failed"

@trace(source="PaymentService", target="Database", action="Check Balance")
def check_balance(amount):
    return True

# 3. 运行代码
process_payment(100)
```

### 嵌套调用（上下文推断）

你不需要每次都指定 `source`（调用方）。MermaidTrace 会根据当前上下文自动推断。

```python
@trace(source="Client", target="API")
def main():
    # 在这里，当前的参与者是 "API"
    service_call()

@trace(target="Service") # source 被自动推断为 "API"
def service_call():
    pass
```

### FastAPI 集成

```python
from fastapi import FastAPI
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app = FastAPI()
app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### CLI 查看器

即时可视化生成的 `.mmd` 文件：

```bash
mermaid-trace serve my_flow.mmd
```

## 📂 文档

- [英文文档](docs/en/README.md)
- [中文文档](README_CN.md)

## 🤝 贡献

欢迎贡献！详情请参阅 [CONTRIBUTING.md](docs/zh/CONTRIBUTING.md)。

## 📄 许可证

MIT
