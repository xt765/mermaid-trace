# MermaidTrace: 能画图的 Python 日志工具

🌐 **语言**: [English](README.md) | [中文](README_CN.md)

[![PyPI version](https://img.shields.io/pypi/v/mermaid-trace.svg?style=flat-square&color=blue)](https://pypi.org/project/mermaid-trace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mermaid-trace.svg?style=flat-square&color=blue)](https://pypi.org/project/mermaid-trace/)
[![License](https://img.shields.io/github/license/xt765/mermaid-trace?style=flat-square)](LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/xt765/mermaid-trace/ci.yml?style=flat-square&label=CI)](https://github.com/xt765/mermaid-trace/actions/workflows/ci.yml)
[![Codecov](https://img.shields.io/codecov/c/github/xt765/mermaid-trace?style=flat-square&logo=codecov)](https://codecov.io/gh/xt765/mermaid-trace)

---

## 📋 概述

**别再干读日志了。开始“看”懂它们吧。**

MermaidTrace 是一个专业的日志工具，能从你的代码执行中自动生成 [Mermaid JS](https://mermaid.js.org/) 时序图。它非常适合可视化复杂的业务逻辑、微服务交互或异步流程。

---

## 📚 文档

### 主要文档

[用户指南](docs/zh/USER_GUIDE.md) · [API 参考](docs/zh/API.md) · [贡献指南](docs/zh/CONTRIBUTING.md) · [更新日志](docs/zh/CHANGELOG.md) · [许可证](docs/zh/LICENSE)

### 代码注释文档

| 类别               | 链接                                                                                                                                                                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **核心模块** | [Context](docs/zh/code_comments/src/mermaid_trace/core/context.md) · [Decorators](docs/zh/code_comments/src/mermaid_trace/core/decorators.md) · [Events](docs/zh/code_comments/src/mermaid_trace/core/events.md) · [Formatter](docs/zh/code_comments/src/mermaid_trace/core/formatter.md) |
| **处理器**   | [Async Handler](docs/zh/code_comments/src/mermaid_trace/handlers/async_handler.md) · [Mermaid Handler](docs/zh/code_comments/src/mermaid_trace/handlers/mermaid_handler.md)                                                                                                           |
| **集成**     | [FastAPI](docs/zh/code_comments/src/mermaid_trace/integrations/fastapi.md)                                                                                                                                                                                                          |
| **其他**     | [init](docs/zh/code_comments/src/mermaid_trace/__init__.md) · [CLI](docs/zh/code_comments/src/mermaid_trace/cli.md)                                                                                                                                                                   |

---

## ✨ 核心特性

- **装饰器驱动**：只需在函数上添加 `@trace` 或 `@trace_interaction` 即可。
- **批量追踪**：使用 `@trace_class` 一次性追踪整个类的方法。
- **第三方库追踪**：使用 `patch_object` 对外部库方法做 patch 并加入追踪。
- **自动绘图**：生成 `.mmd` 文件，可在 VS Code、GitHub 或 Mermaid Live Editor 中查看。
- **异步支持**：无缝支持 `asyncio`协程。
- **上下文推断**：利用 `contextvars` 自动追踪嵌套调用并推断 `source`（调用方）参与者。
- **智能折叠**：通过折叠重复的高频调用和识别循环模式（如循环调用），防止时序图过载。
- **详细异常堆栈**：自动捕获完整的错误堆栈追踪，并在图表中通过 Note 显示。
- **对象显示优化**：自动清理内存地址（例如 `<__main__.Obj at 0x...>` -> `<Obj>`），并**自动合并列表/元组中连续的相同项**（例如 `[<Obj> x 5]`），使图表更整洁。
- **FastAPI 集成**：内置中间件，实现零配置的 HTTP 请求追踪，支持通过 `X-Trace-ID` 和 `X-Source` 请求头进行分布式追踪。
- **CLI 工具**：内置带热重载功能的查看器，可在浏览器中即时预览图表。

---

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
# 建议将图表存放在专门的目录中（如 mermaid_diagrams/）以保持项目整洁。
configure_flow("mermaid_diagrams/my_flow.mmd", async_mode=True)

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

### 全局配置

你可以通过 `configure_flow` 或环境变量来配置全局设置，以控制性能和行为。

```python
configure_flow(
    "flow.mmd", 
    level=logging.DEBUG, 
    queue_size=5000,  # 增加队列缓冲区以应对高并发
    config_overrides={
        "capture_args": False,       # 关闭参数捕获以获得最高性能
        "max_string_length": 100     # 增加字符串截断长度
    }
)
```

**环境变量支持：**

- `MERMAID_TRACE_CAPTURE_ARGS` (true/false)
- `MERMAID_TRACE_MAX_STRING_LENGTH` (int)
- `MERMAID_TRACE_MAX_ARG_DEPTH` (int)
- `MERMAID_TRACE_QUEUE_SIZE` (int)

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

### 示例教程

请查看 [examples/](examples/) 目录，了解涵盖所有功能的完整示例集：

- **[基础用法](examples/01_basic_usage.py)**：装饰器与类方法追踪。
- **[高级插桩](examples/02_advanced_instrumentation.py)**：`@trace_class` 与 `patch_object`（针对第三方库）。
- **[异步与并发](examples/03_async_concurrency.py)**：`asyncio` 追踪与并发上下文隔离。
- **[错误处理](examples/04_error_handling.py)**：堆栈捕获与错误箭头渲染。
- **[智能折叠](examples/05_intelligent_collapsing.py)**：在循环中保持图表整洁。
- **[FastAPI 集成](examples/06_fastapi_integration.py)**：Web 应用中间件集成。
- **[全栈综合应用](examples/07_full_stack_app.py)**：结合 FastAPI、SQLAlchemy 和 Pydantic 的全链路追踪示例。

---

## 🤝 贡献

欢迎贡献！详情请参阅 [CONTRIBUTING.md](docs/zh/CONTRIBUTING.md)。

---

## 📄 许可证

MIT
