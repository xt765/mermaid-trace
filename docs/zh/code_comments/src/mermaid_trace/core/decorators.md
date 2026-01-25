# 文件: src/mermaid_trace/core/decorators.py

## 概览
本文件包含核心的装饰器逻辑 (`trace` / `trace_interaction`)。这些装饰器负责拦截函数调用，记录“开始调用”事件，执行函数，然后记录“返回”或“错误”事件。

## 核心功能分析

### `_resolve_target` (目标解析)
这是一个关键的辅助函数，用于确定时序图中的参与者名称（Target）。它使用启发式算法：
1.  **Override**: 如果用户在装饰器中显式指定了 `target` 或 `name`，优先级最高。
2.  **Instance Method**: 如果第一个参数包含 `__class__` 属性（通常是 `self`），则使用类名。
3.  **Class Method**: 如果第一个参数是类型（`cls`），则使用类名。
4.  **Module Function**: 如果都不是，则回退到定义该函数的模块名。

### 上下文传播 (Context Propagation)
装饰器不仅记录日志，还负责维护调用链的上下文。
-   **Step 1**: 它从 `LogContext` 获取当前的 `source`（即谁调用了我）。
-   **Step 2**: 记录 `Source -> Target` 的调用日志。
-   **Step 3**: 使用 `LogContext.scope` 将当前上下文更新为 `participant = Target`。
-   **Step 4**: 执行实际函数。此时，函数内部的任何子调用都会看到 `source` 是当前的 `Target`，从而正确绘制出下一级箭头。

### 参数捕获与截断
为了防止日志文件过大或包含敏感信息，装饰器支持：
-   `capture_args=False`: 完全关闭参数记录。
-   `_safe_repr`: 使用 `reprlib` 对长字符串和深层嵌套对象进行截断，确保生成的日志既有用又安全。

## 源代码与中文注释

```python
import functools
import logging
import inspect
import reprlib
from typing import Optional, Any, Callable, Tuple, Dict, Union, TypeVar, cast, overload

from .events import FlowEvent
from .context import LogContext

FLOW_LOGGER_NAME = "mermaid_trace.flow"

# 为被装饰的函数定义泛型类型变量
F = TypeVar("F", bound=Callable[..., Any])

def get_flow_logger() -> logging.Logger:
    """返回流程事件的专用日志记录器。"""
    return logging.getLogger(FLOW_LOGGER_NAME)

def _safe_repr(obj: Any, max_len: int = 50, max_depth: int = 1) -> str:
    """
    安全地创建对象的字符串表示形式。
    
    通过截断长字符串/对象并在 __repr__ 调用（例如严格对象）期间处理异常，
    防止产生巨大的日志文件。
    """
    try:
        # 创建自定义 repr 对象以控制深度和长度
        a_repr = reprlib.Repr()
        a_repr.maxstring = max_len
        a_repr.maxother = max_len
        a_repr.maxlevel = max_depth
        
        r = a_repr.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable>"

def _format_args(
    args: Tuple[Any, ...], 
    kwargs: Dict[str, Any], 
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1
) -> str:
    """
    将函数参数格式化为单个字符串 "arg1, arg2, k=v"。
    用于图表中的箭头标签。
    """
    if not capture_args:
        return ""

    parts = []
    for arg in args:
        parts.append(_safe_repr(arg, max_len=max_arg_length, max_depth=max_arg_depth))
        
    for k, v in kwargs.items():
        val_str = _safe_repr(v, max_len=max_arg_length, max_depth=max_arg_depth)
        parts.append(f"{k}={val_str}")
        
    return ", ".join(parts)

def _resolve_target(func: Callable[..., Any], args: Tuple[Any, ...], target_override: Optional[str]) -> str:
    """
    确定图表中参与者（目标）的名称。
    
    解析优先级:
    1. **覆盖**: 如果用户显式提供了 `target="Name"`，使用它。
    2. **实例方法**: 如果第一个参数看起来像 `self`（有 __class__），
       使用类名。
    3. **类方法**: 如果第一个参数是类型 (cls)，使用类名。
    4. **模块函数**: 回退到包含该函数的模块名称。
    5. **回退**: "Unknown"。
    """
    if target_override:
        return target_override
        
    # 启发式: 如果是方法调用，args[0] 通常是 'self'。
    if args:
        first_arg = args[0]
        # 检查它是否看起来像类实例
        # 我们检查 hasattr(__class__) 来广泛区分对象和基元/容器，
        # 确保我们不会将传递给函数的普通列表错误标记为 "List" 参与者。
        if hasattr(first_arg, "__class__") and not isinstance(first_arg, (str, int, float, bool, list, dict, type)):
             return str(first_arg.__class__.__name__)
        # 检查它是否看起来像类 (cls) - 例如 @classmethod
        if isinstance(first_arg, type):
             return first_arg.__name__

    # 对于独立函数，回退到模块名
    module = inspect.getmodule(func)
    if module:
        return module.__name__.split(".")[-1]
    return "Unknown"

def _log_interaction(logger: logging.Logger, 
                     source: str, 
                     target: str, 
                     action: str, 
                     params: str, 
                     trace_id: str) -> None:
    """
    记录 'Call' 事件（函数开始）。
    箭头: source -> target
    """
    req_event = FlowEvent(
        source=source, target=target, 
        action=action, message=action,
        params=params, trace_id=trace_id
    )
    # 'extra' 字典至关重要: Handler 将获取它来格式化 Mermaid 行
    logger.info(f"{source}->{target}: {action}", extra={"flow_event": req_event})

def _log_return(logger: logging.Logger, 
                source: str, 
                target: str, 
                action: str, 
                result: Any, 
                trace_id: str,
                capture_args: bool = True,
                max_arg_length: int = 50,
                max_arg_depth: int = 1) -> None:
    """
    记录 'Return' 事件（函数结束）。
    箭头: target --> source (虚线返回)
    
    注意: 这里的 'source' 是原始调用者，'target' 是被调用者。
    所以返回箭头从 target 回到 source。
    """
    result_str = ""
    if capture_args:
        result_str = _safe_repr(result, max_len=max_arg_length, max_depth=max_arg_depth)
        
    resp_event = FlowEvent(
        source=target, target=source, 
        action=action, message="Return", 
        is_return=True, result=result_str, trace_id=trace_id
    )
    logger.info(f"{target}->{source}: Return", extra={"flow_event": resp_event})

def _log_error(logger: logging.Logger, 
               source: str, 
               target: str, 
               action: str, 
               error: Exception, 
               trace_id: str) -> None:
    """
    如果函数引发异常，则记录 'Error' 事件。
    箭头: target -x source (错误返回)
    """
    err_event = FlowEvent(
        source=target, target=source, action=action, 
        message=str(error), is_return=True, is_error=True, error_message=str(error),
        trace_id=trace_id
    )
    logger.error(f"{target}-x{source}: Error", extra={"flow_event": err_event})

@overload
def trace_interaction(func: F) -> F:
    ...

@overload
def trace_interaction(
    *, 
    source: Optional[str] = None, 
    target: Optional[str] = None, 
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1
) -> Callable[[F], F]:
    ...

def trace_interaction(
    func: Optional[F] = None, 
    *, 
    source: Optional[str] = None, 
    target: Optional[str] = None,
    name: Optional[str] = None, 
    action: Optional[str] = None,
    capture_args: bool = True,
    max_arg_length: int = 50,
    max_arg_depth: int = 1
) -> Union[F, Callable[[F], F]]:
    """
    用于在 Mermaid 图表中追踪函数执行的主要装饰器。
    
    它支持两种操作模式:
    1. **简单**: `@trace` (无参数)
    2. **配置**: `@trace(action="Login", target="AuthService")`
    
    参数:
        func: 被装饰的函数（在简单模式下自动传入）。
        source: 调用方参与者的显式名称（很少使用，通常从 Context 推断）。
        target: 被调用方参与者的显式名称（覆盖自动解析）。
        name: 'target' 的别名（为了更清晰的 API 使用）。
        action: 箭头的标签（默认为函数名）。
        capture_args: 是否在日志中包含参数和返回值。默认为 True。
        max_arg_length: 参数/结果表示的最大字符串长度。默认为 50。
        max_arg_depth: 参数/结果表示的最大递归深度。默认为 1。
    """
    
    # 处理别名
    final_target = target or name
    
    # 模式 1: @trace 不带括号使用
    if func is not None and callable(func):
        return _create_decorator(func, source, final_target, action, capture_args, max_arg_length, max_arg_depth)
        
    # 模式 2: @trace(...) 带参数使用 -> 返回工厂
    def factory(f: F) -> F:
        return _create_decorator(f, source, final_target, action, capture_args, max_arg_length, max_arg_depth)
    return factory

def _create_decorator(
    func: F, 
    source: Optional[str], 
    target: Optional[str], 
    action: Optional[str],
    capture_args: bool,
    max_arg_length: int,
    max_arg_depth: int
) -> F:
    """
    构造实际的包装器函数。
    处理同步和异步函数。
    
    此函数将包装器创建逻辑与 `trace_interaction` 中的参数解析逻辑分离，
    使代码更清晰且更易于测试。
    """
    
    # 预计算静态元数据以节省运行时时间
    if action is None:
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """同步函数包装器。"""
        # 1. 解析上下文
        # 'source' 是谁调用了我们（来自 Context）。'target' 是我们是谁（从 self/cls 解析）。
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)
        
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs, capture_args, max_arg_length, max_arg_depth)
        
        # 2. 记录请求（代码块开始）
        _log_interaction(logger, current_source, current_target, action, params_str, trace_id)
        
        # 3. 使用新上下文执行
        # 我们将 'current_target' 推入为任何内部调用的新 'participant' (source)。
        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = func(*args, **kwargs)
                # 4. 记录成功返回
                _log_return(logger, current_source, current_target, action, result, trace_id, capture_args, max_arg_length, max_arg_depth)
                return result
            except Exception as e:
                # 5. 记录错误返回
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        """异步函数包装器（协程）。"""
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)
        
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs, capture_args, max_arg_length, max_arg_depth)
        
        # 2. 记录请求（代码块开始）
        _log_interaction(logger, current_source, current_target, action, params_str, trace_id)
        
        # 使用异步上下文管理器 (ascope) 确保上下文跨 await 正确传播
        async with LogContext.ascope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = await func(*args, **kwargs)
                _log_return(logger, current_source, current_target, action, result, trace_id, capture_args, max_arg_length, max_arg_depth)
                return result
            except Exception as e:
                _log_error(logger, current_source, current_target, action, e, trace_id)
                raise

    # 检测被包装的函数是否为协程，以选择正确的包装器
    if inspect.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    return cast(F, wrapper)

# 方便导入的别名
trace = trace_interaction
```
