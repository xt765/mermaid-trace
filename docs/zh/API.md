# API 参考文档

## 目录

- [核心功能 (Core)](#核心功能-core)
  - [trace / trace_interaction](#trace--trace_interaction)
  - [configure_flow](#configure_flow)
  - [LogContext](#logcontext)
  - [Event（抽象基类）](#event抽象基类)
  - [FlowEvent](#flowevent)
  - [BaseFormatter（抽象基类）](#baseformatter抽象基类)
  - [MermaidFormatter](#mermaidformatter)
  - [MermaidFileHandler](#mermaidfilehandler)
  - [AsyncMermaidHandler](#asyncmermaidhandler)
- [集成 (Integrations)](#集成-integrations)
  - [MermaidTraceMiddleware (FastAPI)](#mermaidtracemiddleware-fastapi)

## 核心功能 (Core)

### `trace` / `trace_interaction`

用于追踪函数执行的装饰器。可以带参数使用，也可以不带参数使用。

```python
# 简单用法
@trace
def my_func(): ...

# 详细用法
@trace(source="Client", target="Server", action="Login", capture_args=False)
def login(username): ...
```

**参数：**
- `source` (Optional[str]): 调用方参与者名称。如果为 `None`，则从 `contextvars` 推断。
- `target` (Optional[str]): 被调用方参与者名称。如果为 `None`，则从类名（如果是方法）或模块名推断。
- `name` (Optional[str]): `target` 的别名。显式设置参与者名称。
- `action` (Optional[str]): 交互描述。如果为 `None`，默认为格式化后的函数名（例如 `process_payment` -> "Process Payment"）。
- `capture_args` (bool): 是否记录参数和返回值。默认为 `True`。对于敏感数据可设置为 `False`。
- `max_arg_length` (int): 参数字符串表示的最大长度。默认为 50。
- `max_arg_depth` (int): 参数嵌套结构表示的最大深度。默认为 1。

### `configure_flow`

配置全局日志记录器以输出到 Mermaid 文件。应在应用程序启动时调用一次。

```python
def configure_flow(
    output_file: str = "flow.mmd",
    handlers: Optional[List[logging.Handler]] = None,
    append: bool = False,
    async_mode: bool = False
) -> logging.Logger
```

**参数：**
- `output_file` (str): `.mmd` 输出文件的路径。默认为 "flow.mmd"。
- `handlers` (List[logging.Handler]): 可选的自定义日志处理器列表。如果提供，`output_file` 将被忽略，除非您手动包含了 `MermaidFileHandler`。
- `append` (bool): 如果为 `True`，则添加新的处理器而不移除现有的。默认为 `False`。
- `async_mode` (bool): 如果为 `True`，使用非阻塞后台线程进行日志记录 (QueueHandler)。推荐用于生产环境。默认为 `False`。

### `LogContext`

管理执行上下文（类似线程本地存储），用于在异步任务和线程之间追踪调用方/被调用方关系和 Trace ID。

**方法：**
- `LogContext.current_trace_id() -> str`: 获取或生成当前的 Trace ID。
- `LogContext.current_participant() -> str`: 获取当前活跃的参与者。
- `LogContext.scope(data)`: 同步上下文管理器，用于临时更新上下文。
- `LogContext.ascope(data)`: 异步上下文管理器 (`async with`)，用于临时更新上下文。

### `Event`（抽象基类）

所有事件类型的抽象基类，为不同类型的事件提供通用接口。

**方法：**
- `get_source() -> str`: 获取事件的来源。
- `get_target() -> str`: 获取事件的目标。
- `get_action() -> str`: 获取事件的动作名称。
- `get_message() -> str`: 获取事件的消息文本。
- `get_timestamp() -> float`: 获取事件的时间戳。
- `get_trace_id() -> str`: 获取事件的追踪 ID。

### `FlowEvent`

表示执行流程中的单个交互或步骤，继承自 `Event`。

**属性：**
- `source` (str): 发起动作的参与者名称。
- `target` (str): 接收动作的参与者名称。
- `action` (str): 操作的简短可读名称。
- `message` (str): 显示在图表箭头上的实际文本标签。
- `trace_id` (str): 追踪会话的唯一标识符。
- `timestamp` (float): 事件发生时的 Unix 时间戳。
- `is_return` (bool): 指示这是否为响应箭头的标志。
- `is_error` (bool): 指示是否发生异常的标志。
- `error_message` (Optional[str]): 如果 `is_error` 为 True，则包含详细的错误文本。
- `params` (Optional[str]): 函数参数的字符串表示。
- `result` (Optional[str]): 返回值的字符串表示。

### `BaseFormatter`（抽象基类）

所有事件格式化器的抽象基类，为不同的输出格式提供通用接口。

**方法：**
- `format_event(event: Event) -> str`: 将事件格式化为所需的输出字符串。
- `format(record: logging.LogRecord) -> str`: 格式化包含事件的日志记录。

### `MermaidFormatter`

将事件转换为 Mermaid 时序图语法的自定义格式化器，继承自 `BaseFormatter`。

**方法：**
- `format_event(event: Event) -> str`: 将事件转换为 Mermaid 语法字符串。

### `MermaidFileHandler`

将 `Event` 对象写入 Mermaid (.mmd) 文件的自定义日志处理器。

**特性：**
- 使用锁确保线程安全的文件写入
- 自动管理 Mermaid 文件头
- 支持覆盖和追加两种模式
- 支持延迟写入以提高性能

### `AsyncMermaidHandler`

使用后台线程写入日志的非阻塞日志处理器。

**参数：**
- `handlers` (List[logging.Handler]): 应该从队列接收日志的处理器列表。
- `queue_size` (int): 队列的最大大小。默认为 1000。

**特性：**
- 基于队列的日志记录，具有可配置的大小限制
- 队列已满时的内置丢弃策略
- 应用程序退出时自动刷新队列

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
