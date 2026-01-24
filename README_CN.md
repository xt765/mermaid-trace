# LogCapy - Python's Calm Logger 🦦

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/logcapy.svg)](https://pypi.org/project/logcapy/)
[![Python versions](https://img.shields.io/pypi/pyversions/logcapy.svg)](https://pypi.org/project/logcapy/)
[![License](https://img.shields.io/github/license/username/logcapy.svg)](https://github.com/username/logcapy/blob/main/LICENSE)
[![Build Status](https://github.com/username/logcapy/actions/workflows/ci.yml/badge.svg)](https://github.com/username/logcapy/actions)
[![Code Coverage](https://img.shields.io/codecov/c/github/username/logcapy)](https://codecov.io/gh/username/logcapy)

**[English](README.md) | [简体中文](README_CN.md)**

</div>

**LogCapy** 是一个强大的 Python 库，无缝集成了异常处理与结构化日志记录。它的核心目标是实现自动化、结构化的错误管理与日志输出，让错误处理变得轻松自如。

灵感来源于情绪稳定的水豚（Capybara），LogCapy 让您的日志在代码崩溃时依然保持从容有序。

## ✨ 核心特性

- **🛡️ 智能装饰器**: `@logcapy.catch` 自动捕获异常，并记录完整的上下文信息（参数、堆栈追踪），以结构化方式输出。
- **🔄 健壮的重试机制**: `@logcapy.retry` 提供可配置的重试逻辑（指数退避策略），并自动记录每次尝试的结果。
- **🆔 上下文感知**: 利用 `contextvars` 在异步/同步调用中自动追踪 `Request ID`、`User ID` 等上下文信息。
- **🪵 后端无关**: 开箱即用支持标准库 `logging`，也能无缝集成 `loguru`。
- **📊 结构化日志**: 原生支持 JSON 输出，可直接集成到 ELK Stack、Splunk 或 Datadog。
- **🔌 框架集成**: 提供适用于 **FastAPI**、**Flask** 和 **Django** 的中间件，自动捕获请求上下文。
- **⚡ 原生异步**: 专为 `asyncio` 和现代 Python 异步生态系统设计。

## 📦 安装指南

通过 pip 安装 LogCapy：

```bash
pip install logcapy
```

安装包含额外依赖的版本（例如 `loguru` 支持或 Web 框架集成）：

```bash
# 支持 Loguru
pip install logcapy[loguru]

# Web 框架支持
pip install logcapy[fastapi]
pip install logcapy[flask]
pip install logcapy[django]

# 安装所有功能
pip install logcapy[all]
```

## 🚀 快速开始

### 基础用法

```python
from logcapy import configure, catch
import asyncio

# 1. 全局配置（输出 JSON 日志到标准输出）
configure(backend="stdlib", json_output=True)

# 2. 装饰您的函数
@catch(default_return=None)
async def dangerous_task(x, y):
    return x / y

# 3. 安全运行
asyncio.run(dangerous_task(1, 0))
```

**输出日志示例：**
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

### 重试机制

```python
from logcapy import retry

@retry(max_attempts=3, delay=1, backoff=2)
def unstable_network_call():
    # 将重试 3 次，采用指数退避（1s, 2s, 4s）
    # 每次失败都会自动记录日志
    raise ConnectionError("Network is down")
```

### FastAPI 集成

LogCapy 提供中间件，可自动处理 Request ID 和上下文日志记录。

```python
from fastapi import FastAPI
from logcapy.integrations.fastapi import LogCapyMiddleware

app = FastAPI()
app.add_middleware(LogCapyMiddleware)

@app.get("/")
async def root():
    # Request ID 会自动注入到日志中
    return {"message": "Hello World"}
```

## ⚙️ 配置说明

您可以配置 LogCapy 使用不同的后端（`stdlib` 或 `loguru`）以及输出格式。

```python
from logcapy import configure

# 使用 Loguru 作为后端
configure(backend="loguru", json_output=True)

# 使用标准库 logging（默认）
configure(backend="stdlib", json_output=False)
```

## 🛠️ 开发指南

### 前置要求

- Python 3.8+
- Hatch 或 Pip

### 运行测试

```bash
pip install .[all]
pip install pytest
pytest
```

## 🤝 贡献指南

欢迎贡献代码！请随时提交 Pull Request。

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目基于 MIT 许可证分发。详情请参阅 `LICENSE` 文件。
