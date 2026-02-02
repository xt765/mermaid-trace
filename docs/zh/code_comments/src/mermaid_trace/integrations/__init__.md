# integrations/__init__.py 模块注释

## 文件概览
`integrations/__init__.py` 是 MermaidTrace 集成模块的入口。它负责管理项目与第三方框架（如 FastAPI, Flask, Django 等）的集成组件。

## 主要作用
1. **模块化集成**: 将不同框架的适配逻辑隔离在各自的子模块中，保持核心代码的简洁。
2. **统一导出**: 允许用户通过 `from mermaid_trace.integrations import ...` 的方式便捷地访问集成组件。

## 设计模式
- **可选依赖**: 集成模块通常涉及第三方库。设计上遵循“按需加载”原则，如果用户没有安装对应的框架（例如未安装 FastAPI），不应该影响 MermaidTrace 核心功能的使用。

## 目前支持
- **FastAPI**: 提供中间件支持全链路请求追踪。
- **LangChain**: 提供 CallbackHandler 支持 LLM 执行流可视化。

## 源代码与中文注释

```python
"""
MermaidTrace 的集成包。

本包提供与各种框架和库的集成，为 FastAPI、LangChain 等流行生态系统提供自动追踪和图表生成。
"""

from .fastapi import MermaidTraceMiddleware, add_mermaid_trace_middleware
from .langchain import MermaidTraceCallbackHandler

# 公共 API 导出
__all__ = [
    "MermaidTraceMiddleware",
    "add_mermaid_trace_middleware",
    "MermaidTraceCallbackHandler",
]
```
