# API 参考文档

## 核心功能 (Core)

### `trace` / `trace_interaction`

用于追踪函数执行的装饰器。

```python
@trace(source="Client", target="Server", action="Login")
def login(username): ...
```

**参数：**
- `source` (Optional[str]): 调用方参与者名称。如果为 `None`，则从 `contextvars` 推断。
- `target` (Optional[str]): 被调用方参与者名称。如果为 `None`，则从类名（如果是方法）或模块名推断。
- `action` (Optional[str]): 交互描述。默认为格式化后的函数名。

### `configure_flow`

配置全局日志记录器以输出到 Mermaid 文件。

```python
def configure_flow(output_file: str = "flow.mmd") -> logging.Logger
```

**参数：**
- `output_file` (str): `.mmd` 输出文件的路径。

## 集成 (Integrations)

### `MermaidTraceMiddleware` (FastAPI)

用于自动 HTTP 请求追踪的中间件。

```python
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

app.add_middleware(MermaidTraceMiddleware, app_name="MyAPI")
```

**参数：**
- `app`: FastAPI/Starlette 应用程序实例。
- `app_name` (str): 在图表中代表此应用程序的参与者名称。
