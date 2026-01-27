# 根模块 (__init__.py)

`__init__.py` 是 MermaidTrace 库的公开入口。它定义了库的公共 API，并提供了一个便捷的配置函数 `configure_flow` 来初始化追踪系统。

## 核心功能

- **公开 API 导出**: 导出常用的装饰器、类和配置对象。
- **全局初始化**: 提供 `configure_flow` 函数，用于设置日志处理器、输出文件和运行模式。
- **解耦设计**: 默认不导入集成模块（如 FastAPI），以避免强制依赖，确保库的轻量化。

## 关键设计

### 1. 公开 API 列表

通过 `__all__` 明确定义了开发者可以直接使用的组件：

| 组件 | 类型 | 说明 |
| :--- | :--- | :--- |
| `trace` | 装饰器 | 用于追踪单个函数的调用。 |
| `trace_class` | 装饰器 | 用于追踪整个类的所有方法。 |
| `configure_flow` | 函数 | 初始化追踪系统，设置输出文件。 |
| `LogContext` | 类 | 管理执行上下文，支持跨异步任务的追踪。 |
| `config` | 对象 | 全局配置单例。 |

### 2. `configure_flow` 配置逻辑

该函数负责搭建整个日志基础设施：
- **幂等性**: 除非设置 `append=True`，否则会清除旧的处理器，防止重复记录。
- **覆盖模式**: 支持 `overwrite` 参数。如果为 `True`，每次启动时会以 `"w"` 模式打开文件，从而清空旧图表并从头开始记录。
- **异步模式**: 支持 `async_mode`，使用 `AsyncMermaidHandler` 实现非阻塞日志记录，提高性能。
- **配置覆盖**: 支持通过 `config_overrides` 参数在运行时修改全局配置。

## 源码分析与注释

```python
def configure_flow(
    output_file: str = "flow.mmd",
    handlers: Optional[List[logging.Handler]] = None,
    append: bool = False,
    overwrite: bool = True,
    async_mode: bool = False,
    level: int = logging.INFO,
    config_overrides: Optional[Dict[str, Any]] = None,
    queue_size: Optional[int] = None,
) -> logging.Logger:  # noqa: PLR0913
    """
    配置流日志记录器。
    1. 应用配置覆盖。
    2. 获取名为 'mermaid_trace.flow' 的特定记录器。
    3. 根据需要清理或保留现有处理器。
    4. 创建 MermaidFileHandler (同步) 或包装在 AsyncMermaidHandler 中 (异步)。
    """
    # 1. 应用运行时配置覆盖
    if config_overrides:
        for k, v in config_overrides.items():
            if hasattr(config, k):
                setattr(config, k, v)

    # 2. 获取内部专用记录器，与根记录器隔离
    logger = logging.getLogger("mermaid_trace.flow")
    logger.setLevel(level)

    # 3. 除非显式要求追加，否则清理现有处理器以防重复
    if not append and logger.hasHandlers():
        logger.handlers.clear()

    # 4. 准备目标处理器
    target_handlers = []
    if handlers:
        target_handlers = handlers
    else:
        # 确定文件打开模式：overwrite=True 则使用 "w"，否则使用 "a" (追加)
        mode = "w" if overwrite else "a"
        # 创建默认的 Mermaid 文件处理器并设置格式化器
        handler = MermaidFileHandler(output_file, mode=mode)
        handler.setFormatter(MermaidFormatter())
        target_handlers = [handler]

    # 5. 处理异步模式
    if async_mode:
        final_queue_size = queue_size if queue_size is not None else config.queue_size
        # 使用 AsyncMermaidHandler 包装，将日志写入队列并由后台线程处理
        async_handler = AsyncMermaidHandler(target_handlers, queue_size=final_queue_size)
        logger.addHandler(async_handler)
    else:
        # 直接添加同步处理器
        for h in target_handlers:
            logger.addHandler(h)

    return logger
```

## 使用示例

```python
from mermaid_trace import trace, configure_flow

# 初始化，输出到 test.mmd，开启异步模式
configure_flow("test.mmd", async_mode=True)

@trace
def my_function():
    pass

my_function()
```
