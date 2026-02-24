# MermaidTrace 示例指南 (Examples)

本目录包含了一系列系统性的示例，旨在展示 `mermaid-trace` 的核心功能、高级特性以及典型使用场景。

## 🚀 快速开始

### 在线体验
推荐直接打开 [MermaidTrace_Demo.ipynb](./MermaidTrace_Demo.ipynb) (或 [中文版](./MermaidTrace_Demo_CN.ipynb))，在 Jupyter Notebook 中交互式地运行代码并实时查看 Mermaid 图表。

### 实时预览 (Live Preview)
运行任何示例后，你可以使用 `mermaid-trace serve` 命令启动一个热重载的预览服务器。
```bash
# 1. 运行示例生成 .mmd 文件
python examples/01_basic_usage.py

# 2. 启动预览服务 (支持文件变动自动刷新)
mermaid-trace serve mermaid_diagrams/examples/basic_flow.mmd
```

---

## 示例列表

### 1. 基础用法 (Basic Usage)
- **文件**: `01_basic_usage.py`
- **核心功能**: `@trace` 装饰器、上下文自动传播、类方法追踪、**数据脱敏**。
- **描述**: 演示了如何手动使用装饰器来追踪同步代码流。展示了 WebApp、AuthService 和 Database 之间的典型交互，以及如何自动屏蔽敏感参数（如密码）。

### 2. 高级自动化插桩 (Advanced Instrumentation)
- **文件**: `02_advanced_instrumentation.py`
- **核心功能**: `@trace_class`、`patch_object`。
- **描述**: 
    - 展示如何使用 `@trace_class` 一键追踪整个类的所有方法。
    - 展示如何使用 `patch_object` 追踪第三方库（如 `requests`），解决“追踪断层”问题。

### 3. 异步与并发 (Async & Concurrency)
- **文件**: `03_async_concurrency.py`
- **核心功能**: 异步追踪、`asyncio.gather` 并发上下文隔离。
- **描述**: 演示了在并发执行多个异步任务时，MermaidTrace 如何利用 `ContextVars` 保持调用链的准确性。

### 4. 错误处理与堆栈捕获 (Error Handling & Stack Trace)
- **文件**: `04_error_handling.py`
- **核心功能**: 自动异常检测、错误箭头 (`--x`)、详细堆栈 Note 渲染。
- **描述**: 演示当代码发生崩溃时，追踪系统如何捕获异常并将其以可视化形式展现在 Mermaid 图表中，包含完整的调用栈。

### 5. 智能折叠 (Intelligent Collapsing)
- **文件**: `05_intelligent_collapsing.py`
- **核心功能**: 重复调用自动合并。
- **描述**: 演示当在循环中高频调用同一函数时，系统如何自动将其折叠，防止图表因信息过载而爆炸，保持流程清晰。

### 6. FastAPI 集成 (FastAPI Integration)
- **文件**: `06_fastapi_integration.py`
- **核心功能**: `MermaidTraceMiddleware`、**Web 请求追踪**、**采样控制**。
- **描述**: 展示了在 Web 框架中实现零侵入追踪。自动捕获 HTTP 请求、支持 Trace ID 传递（Header 注入），以及如何配置采样率以降低生产环境开销。

### 7. 综合全栈应用 (Full Stack Application)
- **文件**: `07_full_stack_app.py`
- **核心功能**: SQLAlchemy + Pydantic + FastAPI 深度集成。
- **描述**: 这是一个综合性的现实世界场景。演示了如何：
    - 追踪 Pydantic 模型的验证过程。
    - 追踪 SQLAlchemy 的数据库操作（通过 `patch_object`）。
    - 在复杂的 Web 应用架构中协调多个参与者（Schema, Service, Database）。

### 8. 日志轮转 (Log Rotation)
- **文件**: `08-log-rotation.py`
- **核心功能**: `RotatingMermaidFileHandler`。
- **描述**: 演示当图表文件达到一定大小时（如 10MB），如何自动切割文件以避免单文件过大。

### 9. LangChain 集成 (AI/LLM)
- **文件**: `09_langchain_integration.py`
- **核心功能**: `MermaidTraceCallbackHandler`。
- **描述**: 专为 LLM 应用设计。演示如何可视化 Chain、Agent 和 Tool 的执行流。支持真实调用（需 API Key）和 Mock 模式。

### 10. 分布式追踪模拟 (Distributed Tracing)
- **文件**: `10_distributed_trace_simulation.py`
- **核心功能**: **跨服务追踪**、`LogContext` 上下文恢复。
- **描述**: 模拟 Service A 调用 Service B 的场景，展示如何通过 HTTP Header 传递 Trace ID，并在 Mermaid 图表中将两个独立服务的日志串联成一条完整的调用链。

### 11. 高级数据脱敏 (Advanced Masking)
- **文件**: `11_custom_masking.py`
- **核心功能**: 复杂嵌套结构脱敏、递归掩码。
- **描述**: 演示如何配置 `config.mask_patterns` 来自动处理深层嵌套的字典和列表，保护 PII（个人敏感信息）不泄露到图表中。

### 12. 外部配置加载 (Configuration from File)
- **文件**: `12_config_from_file.py`
- **核心功能**: JSON 配置加载、动态配置更新。
- **描述**: 演示如何从外部 JSON 文件加载配置（如脱敏规则、采样率等），实现代码与配置分离的最佳实践。
