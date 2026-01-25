# API 参考文档

## 核心功能 (Core)

### `trace` / `trace_interaction`

用于追踪函数执行的装饰器。可以带参数使用，也可以不带参数使用。

```python
# 简单用法
@trace
def my_func(): ...

# 详细用法
@trace(source="Client", target="Server", action="Login")
def login(username): ...
```

**参数：**
- `source` (Optional[str]): 调用方参与者名称。如果为 `None`，则从 `contextvars` 推断。
- `target` (Optional[str]): 被调用方参与者名称。如果为 `None`，则从类名（如果是方法）或模块名推断。
- `action` (Optional[str]): 交互描述。如果为 `None`，默认为格式化后的函数名（例如 `process_payment` -> "Process Payment"）。

### `configure_flow`

配置全局日志记录器以输出到 Mermaid 文件。应在应用程序启动时调用一次。

```python
def configure_flow(output_file: str = "flow.mmd") -> logging.Logger
```

**参数：**
- `output_file` (str): `.mmd` 输出文件的路径。默认为 "flow.mmd"。

### `LogContext`

管理执行上下文（类似线程本地存储），用于在异步任务和线程之间追踪调用方/被调用方关系和 Trace ID。

**方法：**
- `LogContext.current_trace_id() -> str`: 获取或生成当前的 Trace ID。
- `LogContext.current_participant() -> str`: 获取当前活跃的参与者。
- `LogContext.scope(data)`: 同步上下文管理器，用于临时更新上下文。
- `LogContext.ascope(data)`: 异步上下文管理器 (`async with`)，用于临时更新上下文。

## 集成 (Integrations)

### `MermaidTraceMiddleware` (FastAPI)

用于自动 HTTP 请求追踪的中间件。捕获请求路径、方法、状态码和耗时。

```python
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")
```

**参数：**
- `app`: FastAPI/Starlette 应用程序实例。
- `app_name` (str): 在图表中代表此应用程序的参与者名称。

**Headers 支持：**
- `X-Source`: 如果客户端发送此 Header，则设置源参与者名称。
- `X-Trace-ID`: 如果发送此 Header，则使用此 ID 进行追踪会话；否则生成一个新的 UUID。
