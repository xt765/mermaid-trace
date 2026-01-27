# MermaidTrace 示例指南 (Examples)

本目录包含了一系列系统性的示例，旨在展示 `mermaid-trace` 的核心功能、高级特性以及典型使用场景。

## 示例列表

### 1. 基础用法 (Basic Usage)
- **文件**: `01_basic_usage.py`
- **核心功能**: `@trace` 装饰器、上下文自动传播、类方法追踪。
- **描述**: 演示了如何手动使用装饰器来追踪同步代码流。展示了 WebApp、AuthService 和 Database 之间的典型交互。
- **运行命令**: `python examples/01_basic_usage.py`

### 2. 高级自动化插桩 (Advanced Instrumentation)
- **文件**: `02_advanced_instrumentation.py`
- **核心功能**: `@trace_class`、`patch_object`。
- **描述**: 
    - 展示如何使用 `@trace_class` 一键追踪整个类的所有方法。
    - 展示如何使用 `patch_object` 追踪第三方库（如 `requests`），解决“追踪断层”问题。
- **依赖**: `pip install requests`
- **运行命令**: `python examples/02_advanced_instrumentation.py`

### 3. 异步与并发 (Async & Concurrency)
- **文件**: `03_async_concurrency.py`
- **核心功能**: 异步追踪、`asyncio.gather` 并发上下文隔离。
- **描述**: 演示了在并发执行多个异步任务时，MermaidTrace 如何利用 `ContextVars` 保持调用链的准确性。
- **运行命令**: `python examples/03_async_concurrency.py`

### 4. 错误处理与堆栈捕获 (Error Handling & Stack Trace)
- **文件**: `04_error_handling.py`
- **核心功能**: 自动异常检测、错误箭头 (`--x`)、详细堆栈 Note 渲染。
- **描述**: 演示当代码发生崩溃时，追踪系统如何捕获异常并将其以可视化形式展现在 Mermaid 图表中，包含完整的调用栈。
- **运行命令**: `python examples/04_error_handling.py`

### 5. 智能折叠 (Intelligent Collapsing)
- **文件**: `05_intelligent_collapsing.py`
- **核心功能**: 重复调用自动合并。
- **描述**: 演示当在循环中高频调用同一函数时，系统如何自动将其折叠，防止图表因信息过载而爆炸，保持流程清晰。
- **运行命令**: `python examples/05_intelligent_collapsing.py`

### 6. FastAPI 集成 (FastAPI Integration)
- **文件**: `06_fastapi_integration.py`
- **核心功能**: `MermaidTraceMiddleware`、全链路追踪。
- **描述**: 展示了在 Web 框架中实现零侵入追踪。通过中间件自动捕获所有进入系统的 HTTP 请求，并与内部业务逻辑追踪串联。
- **依赖**: `pip install fastapi uvicorn`
- **运行命令**: `python examples/06_fastapi_integration.py`

### 7. 综合全栈应用 (Full Stack Application)
- **文件**: `07_full_stack_app.py`
- **核心功能**: SQLAlchemy + Pydantic + FastAPI 深度集成。
- **描述**: 这是一个综合性的现实世界场景。演示了如何：
    - 追踪 Pydantic 模型的验证过程。
    - 追踪 SQLAlchemy 的数据库操作（通过 `patch_object`）。
    - 在复杂的 Web 应用架构中协调多个参与者（Schema, Service, Database）。
- **依赖**: `pip install fastapi uvicorn sqlalchemy pydantic`
- **运行命令**: `python examples/07_full_stack_app.py`

## 如何查看结果

运行示例后，会在当前目录生成对应的 `.mmd` 文件（例如 `basic_flow.mmd`）。你可以：
1. 使用项目自带的 CLI 查看器：`mermaid-trace preview <filename>.mmd`
2. 在 VS Code 中使用 Mermaid 插件直接查看。
3. 将内容复制到 [Mermaid Live Editor](https://mermaid.live/)。
