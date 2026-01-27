# 用户指南

## 目录

- [简介](#简介)
- [工作原理](#工作原理)
- [并发与 Trace ID](#并发与-trace-id)
- [批量追踪与第三方库](#批量追踪与第三方库)
- [上下文推断 (Context Inference)](#上下文推断-context-inference)
- [图表管理](#图表管理)
  - [智能折叠](#智能折叠)
  - [异常堆栈追踪](#异常堆栈追踪)
  - [对象显示优化](#对象显示优化)
- [高级配置](#高级配置)
  - [异步模式 (性能优化)](#异步模式-性能优化)
  - [数据捕获控制](#数据捕获控制)
  - [显式命名](#显式命名)
  - [灵活的 Handler 配置](#灵活的-handler-配置)
- [CLI 查看器](#cli-查看器)

## 简介

MermaidTrace 弥合了代码执行与架构可视化之间的鸿沟。与静态分析工具不同，它追踪的是**实际**的运行时调用，为您提供系统行为的真实写照。

## 工作原理

1. **装饰**：在您希望出现在图表中的函数上添加 `@trace`。
2. **拦截**：当函数运行时，MermaidTrace 记录一个“请求”事件 (`->>`)。
3. **执行**：函数体执行。
4. **返回**：MermaidTrace 记录一个“返回”事件 (`-->>`) 以及返回值。
5. **可视化**：事件被写入 `.mmd` 文件，渲染为时序图。

## 并发与 Trace ID

MermaidTrace 专为现代异步应用程序和分布式系统打造。它通过为每个流程分配唯一的 **Trace ID** 来自动处理并发请求。

- **自动生成**：当流程开始时（如果不存在），会生成一个新的 Trace ID。
- **传播**：ID 存储在 `contextvars` 中，确保它自动跟随 `await` 调用和后台任务。
- **分布式追踪支持**：
  - **FastAPI 中间件**：自动从请求头中提取 `X-Trace-ID` 和 `X-Source`。
  - **请求头注入**：当使用 `patch_object` 对 `requests` 等库进行插桩时，Trace ID 会自动注入到发出的请求头中，从而实现跨服务的可视化追踪。

*注意：目前，所有追踪都写入同一个文件。如果需要，可以使用日志中的 Trace ID 过滤特定会话。*

## 批量追踪与第三方库

对于大型类或外部库，逐个手动添加 `@trace` 可能会很繁琐。

### 类追踪 (`trace_class`)

使用 `@trace_class` 可以一次性追踪类中的所有公共方法。

```python
from mermaid_trace import trace_class

@trace_class
class MyService:
    def method_a(self): pass
    def method_b(self): pass
```

### 第三方库补丁 (`patch_object`)

如果您想追踪对外部库（如 `requests`）的调用，可以使用 `patch_object`。

```python
import requests
from mermaid_trace import patch_object

# 现在所有对 requests.get 的调用都会出现在图表中
patch_object(requests, "get", name="Requests")
```

## 上下文推断 (Context Inference)

最强大的功能之一是 **上下文推断**。

在时序图中，每个箭头都有一个 `Source`（源）和一个 `Target`（目标）。

- `Target` 很容易确定：就是被调用的函数或类。
- `Source` 很难确定：它是 *谁调用了* 该函数。

MermaidTrace 使用 Python 的 `contextvars` 来追踪“当前参与者”。

**示例：**

1. `A` 调用 `B`。
2. 在 `A` 内部，上下文被设置为 "A"。
3. 当 `B` 被 `@trace` 装饰时，它看到上下文是 "A"，因此绘制 `A ->> B`。
4. 在 `B` 内部，上下文更新为 "B"。
5. 如果 `B` 调用 `C`，`C` 看到上下文是 "B"，因此绘制 `B ->> C`。

这意味着通常您只需要在 *入口点*（第一个函数）设置 `source`。

## 图表管理

### 文件存放规范

为了保持项目根目录的整洁，建议将生成的 `.mmd` 文件统一存放在 `mermaid_diagrams/` 目录下。该目录通常采用以下逻辑结构：

- `mermaid_diagrams/examples/`: 存放示例代码生成的图表。
- `mermaid_diagrams/tests/`: 存放测试用例生成的图表。
- `mermaid_diagrams/flows/`: 存放实际业务流程生成的图表。

在配置时，只需指定相对路径即可：

```python
configure_flow("mermaid_diagrams/flows/user_login.mmd")
```

### 智能折叠

当一个函数在循环中被多次调用，或者出现重复的调用序列时，时序图可能会变得非常混乱且难以阅读。MermaidTrace 拥有先进的**状态化模式检测**功能：

1. **单次重复折叠**：同一个函数被连续调用多次（如在 `for` 循环中），会被折叠为带计数器的单个箭头（例如：`process_item (x10)`）。
2. **模式序列折叠**：检测复杂的重复模式，如 `A -> B -> C -> A -> B -> C`。这种循环序列也会被识别并合并，同时保留模式的结构。
3. **自动刷新**：当检测到新的调用不再匹配当前模式时，系统会自动“刷新”缓冲区，将之前的统计结果写入文件并开始记录新模式。

这种行为是默认启用的，旨在确保您的图表保持高层次且信息丰富。

### 异常堆栈追踪

如果只看到错误消息，在时序图中调试异常会很困难。当被装饰的函数抛出异常时，MermaidTrace 会捕获**完整的 Python 堆栈追踪**。

- 在 Mermaid 图表中，错误箭头 (`-x`) 旁边会出现一个 Note。
- 通过查看该 Note，您可以直接看到完整的 traceback，从而无需切换回原始文本日志即可进行调试。

### 对象显示优化

MermaidTrace 旨在生成干净、易读的图表，即使是在处理复杂的数据结构时：
- **简化 Python 对象表示**：自动检测并简化包含内存地址的默认 Python 对象表示（如 `<__main__.Obj at 0x...>` -> `<Obj>`）。这去除了无意义的干扰信息。
- **列表/元组项合并**：自动识别并合并列表（list）或元组（tuple）中连续出现的相同项（如 `[<UserDB> x 5]`）。这在记录包含大量相似对象的集合时特别有用，能显著缩短消息长度。
- **安全截断**：通过 `max_string_length` 全局配置限制字符串的最大长度，防止超长参数（如 Base64 字符串）撑爆图表。

## 高级配置

### 异步模式 (性能优化)

对于高吞吐量的生产环境，请启用 `async_mode` 将文件写入操作卸载到后台线程。这确保了您的应用程序主线程永远不会被磁盘 I/O 阻塞。

```python
configure_flow("flow.mmd", async_mode=True)
```

### 数据捕获控制

您可以控制如何记录函数参数和返回值，以保持图表整洁并保护敏感数据。

#### 全局配置 (`MermaidConfig`)

您可以通过 `config` 对象或环境变量进行全局配置：

```python
from mermaid_trace import config

config.capture_args = False  # 全局禁用参数捕获
config.max_string_length = 100 # 设置全局字符串截断长度
```

环境变量支持：

- `MERMAID_TRACE_CAPTURE_ARGS`: `true`/`false`
- `MERMAID_TRACE_MAX_STRING_LENGTH`: 数字
- `MERMAID_TRACE_MAX_ARG_DEPTH`: 数字

#### 装饰器覆盖

装饰器上的参数优先级高于全局配置：

```python
# 即使全局禁用了参数捕获，该特定函数仍会捕获
@trace(capture_args=True)
def specific_function():
    pass
```

### 显式命名

如果自动推断的类名/函数名不是您想要的，您可以显式命名参与者。

```python
@trace(name="AuthService")  # 图表中将显示 "AuthService"
def login():
    pass
```

### 灵活的 Handler 配置

您可以将 MermaidTrace 添加到现有的日志设置中，或者追加多个 Handler。

```python
# 追加到现有的 Handler，而不是清除它们
configure_flow("flow.mmd", append=True)
```

## CLI 查看器

要查看您的图表，请使用 CLI：

```bash
mermaid-trace serve flow.mmd --port 8000
```

这将启动本地服务器并打开浏览器。它会监控文件更改并立即自动刷新页面。
