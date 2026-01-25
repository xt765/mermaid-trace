# src/mermaid_trace/core/decorators.py 代码分析

## 文件概览 (File Overview)
这是魔法发生的地方。`decorators.py` 定义了 `@trace` 装饰器。
当你把 `@trace` 放在一个函数头上时，它会"劫持"这个函数的执行：
1. 在函数开始前，记录一条"请求"日志（画一条去向的箭头）。
2. 执行函数。
3. 在函数结束后，记录一条"响应"日志（画一条返回的虚线箭头）。
4. 如果出错，记录一条"错误"日志（画一条带叉的线）。

## 核心概念 (Key Concepts)

*   **Decorator (装饰器)**: Python 的一种语法糖（`@`），允许你在不修改原函数代码的情况下，增加额外的功能（比如日志、鉴权、缓存）。
*   **Wrapper Function (包装函数)**: 装饰器内部定义的函数，它包裹了原函数。当我们调用原函数时，实际上执行的是这个包装函数。
*   **Introspection (自省)**: 代码在运行时检查对象类型的能力。这里用来判断参数是 `self` (类方法) 还是普通参数，从而推断是谁在调用谁。

## 代码详解 (Code Walkthrough)

```python
import functools
import logging
import inspect
import reprlib
from typing import Optional, Any, Callable, Tuple, Dict
from .events import FlowEvent
from .context import LogContext

# 定义用于流程事件的特定 logger 命名空间
FLOW_LOGGER_NAME = "mermaid_trace.flow"

def get_flow_logger() -> logging.Logger:
    """检索用于流程跟踪的专用 logger 实例。"""
    return logging.getLogger(FLOW_LOGGER_NAME)

def _safe_repr(obj: Any, max_len: int = 50) -> str:
    """
    安全地创建对象的字符串表示形式，用于图表标签。
    截断长字符串以避免使图表混乱。
    """
    try:
        r = reprlib.repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable>"

def _format_args(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    将函数参数格式化为简洁的字符串，用于图表标签。
    例如："a=1, b=2"
    它会尝试跳过 'self' 或 'cls' 参数以减少噪音。
    """
    parts = []
    for arg in args:
        # 检查 arg 是否可能是 'self' 或 'cls' 并跳过
        # 逻辑：如果有 __class__ 属性且不是基本类型，可能是类实例。
        if hasattr(arg, "__class__") and not isinstance(arg, (str, int, float, bool, list, dict)):
             continue
        parts.append(_safe_repr(arg))
        
    for k, v in kwargs.items():
        parts.append(f"{k}={_safe_repr(v)}")
        
    return ", ".join(parts)

def trace_interaction(source: Optional[str] = None, target: Optional[str] = None, action: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    装饰器：将函数调用记录为序列图中的交互。
    
    此装饰器拦截函数调用，记录"请求"事件，执行函数，然后记录"响应"（或"错误"）事件。
    它还管理 `LogContext` 以更新当前参与者，确保嵌套调用被正确归属。
    
    Args:
        source: 发起调用的参与者。如果为 None，从 LogContext 推断。
        target: 接收调用的参与者。如果为 None，尝试使用类名或模块名。
        action: 动作描述。如果为 None，默认为函数名。
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        nonlocal target, action
        
        # 如果未提供 action，从函数名生成可读名称
        # 例如 "process_payment" -> "Process Payment"
        if action is None:
            action = func.__name__.replace("_", " ").title()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """同步包装函数。"""
            # 1. 解析运行时值
            # 确定谁在调用。默认为上下文中的任何内容。
            current_source = source or LogContext.current_participant()
            
            # 确定谁被调用。
            current_target = target
            if current_target is None:
                # 启发式：如果是方法调用，args[0] 通常是 'self'。
                if args and hasattr(args[0], "__class__") and not isinstance(args[0], (str, int, float, bool, list, dict)):
                     current_target = args[0].__class__.__name__
                else:
                    # 回退到模块名的最后一部分
                    current_target = func.__module__.split(".")[-1]

            logger = get_flow_logger()
            params_str = _format_args(args, kwargs)
            
            # 2. 记录请求 (Source -> Target)
            req_event = FlowEvent(
                source=current_source, target=current_target, 
                action=action, message=action,
                params=params_str
            )
            # 我们将事件对象传递给 'extra'，以便自定义 handler 处理它
            logger.info(f"{current_source}->{current_target}: {action}", extra={"flow_event": req_event})
            
            # 3. 在新上下文范围内执行函数
            # 我们将 'participant' 上下文切换为 target，因此此函数发出的任何内部调用
            # 都将显示为源自 'target'。
            with LogContext.scope({"participant": current_target}):
                try:
                    result = func(*args, **kwargs)
                    
                    # 4. 记录响应 (Target -> Source)
                    result_str = _safe_repr(result)
                    resp_event = FlowEvent(
                        source=current_target, target=current_source, 
                        action=action, message="Return", 
                        is_return=True, result=result_str
                    )
                    logger.info(f"{current_target}->{current_source}: Return", extra={"flow_event": resp_event})
                    return result
                except Exception as e:
                    # 5. 记录错误 (Target --x Source)
                    err_event = FlowEvent(
                        source=current_target, target=current_source, action=action, 
                        message=str(e), is_return=True, is_error=True, error_message=str(e)
                    )
                    logger.error(f"{current_target}-x{current_source}: Error", extra={"flow_event": err_event})
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """异步包装函数 (针对 async def)。"""
            # 逻辑与同步包装器相同，但使用 'await' 和 'async with'。
            # ... (代码省略，逻辑同上) ...
            # 关键区别：使用 `await func(...)` 和 `async with LogContext.ascope(...)`

        # 检查被装饰的函数是否是协程 (async)
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator

# 别名，用法更简洁 (例如 @trace 而不是 @trace_interaction)
trace = trace_interaction
```

## 新手指南 (Beginner's Guide)

*   **装饰器是如何处理 `async` 函数的？**
    这是一个高级技巧。装饰器必须检测原函数是同步 (`def`) 还是异步 (`async def`)。如果是异步的，它必须返回一个 `async` 定义的包装器，并使用 `await` 调用原函数。如果不这样做，调用异步函数时会直接返回一个协程对象而不是结果，导致代码崩溃。代码中的 `inspect.iscoroutinefunction(func)` 就是做这个检测的。

*   **`functools.wraps(func)` 是做什么的？**
    当你包装一个函数时，新的包装函数会丢失原函数的名字 (`__name__`) 和文档 (`__doc__`)。`wraps` 装饰器负责把这些元数据从原函数复制到包装函数上，这对于调试和生成文档非常重要。

*   **"启发式"判断 `self` 是什么意思？**
    代码尝试猜测 `target`（被调用者）是谁。如果第一个参数看起来像是一个对象实例（不是数字、字符串等基本类型），代码就假设它是 `self`，并使用它的类名作为 `target`。这并不总是100%准确，但在大多数面向对象编程场景下工作良好。
