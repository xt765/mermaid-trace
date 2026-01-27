# 文件: src/mermaid_trace/core/decorators.py

## 概览
`decorators.py` 是 MermaidTrace 的核心装饰器模块。它实现了 `@trace` 装饰器的所有逻辑，包括拦截函数调用、自动识别参与者、捕获参数、记录返回结果以及处理异常。

## 核心功能分析

### 1. `@trace` (即 `trace_interaction`)
这是用户最常接触的接口。它支持两种用法：
- **简单模式**: `@trace`，直接使用默认配置。
- **配置模式**: `@trace(target="DB", action="Query")`，自定义图表中的显示名称和动作。

### 2. 参与者识别 (`_resolve_target`)
该函数实现了智能猜测逻辑，用于确定“谁”是当前被调用的目标：
- **显式指定**: 优先使用装饰器参数中的 `target`。
- **类实例/类方法**: 
    - 如果第一个参数是 `self`（具有 `__class__`），则取其类名。
    - 如果第一个参数是 `cls`（类型对象），则取其类名。
- **普通函数**: 取其所属模块的名称（只取最后一部分，如 `auth`）。

### 3. 对象显示优化与 `FlowRepr`
为了防止日志爆炸并提升图表可读性，模块引入了自定义的 `FlowRepr` 类：
- **对象简化**: 自动检测并简化包含内存地址的默认 Python 对象表示（如 `<__main__.Obj at 0x...>` -> `<Obj>`）。
- **容器合并**: 自动识别并合并列表（list）或元组（tuple）中连续出现的相同项（如 `[<UserDB> x 5]`）。
- **正则表达式清理**: 在最后阶段使用正则进一步清理残留的内存地址格式。

### 4. 安全表示 (`_safe_repr`)
- **截断与深度**: 使用 `FlowRepr` 限制字符串长度和递归深度。
- **容错处理**: 捕获所有在生成 `repr` 时可能发生的异常，确保追踪过程不影响主业务。

### 5. 包装器逻辑 (`_create_decorator`)
- **同步/异步支持**: 通过 `inspect.iscoroutinefunction` 自动识别并返回对应的包装器（`wrapper` 或 `async_wrapper`）。
- **参数解耦**: 为了解决 Ruff PLR0913 (参数过多) 检查，引入了 `_TraceConfig` 和 `_TraceMetadata` 数据类，将配置项和元数据进行分组管理。
- **上下文切换**:
    - 在调用函数前，先记录“请求”事件。
    - **关键点**: 使用 `LogContext.scope` 将当前被调用的目标设置为新的“当前参与者”，这样该函数内部调用的其他被追踪函数就能正确识别出调用者是谁。
    - 函数返回后，记录“返回”事件，并带上返回值。

### 6. 异常处理 (`_log_error`)
- 如果函数执行抛出异常，装饰器会捕获它。
- 使用 `traceback.format_exception` 获取完整的堆栈信息。
- 记录一个特殊的错误事件（在 Mermaid 中显示为 `X` 箭头）。
- **不拦截异常**: 记录完后立即 `raise`，确保业务逻辑的异常处理流程不变。

## 术语说明
- **Source (源)**: 发起调用的参与者。
- **Target (目标)**: 接收调用的参与者。
- **Action (动作)**: 箭头上的文字说明，默认为函数名的标题化（Title Case）。
- **Trace ID**: 用于关联一整条调用链的唯一 ID。

## 源代码与中文注释

```python
"""
函数追踪装饰器模块
=================================

本模块实现了拦截函数调用、捕获执行细节并将其记录为结构化事件的核心逻辑。
它提供了 `@trace` 装饰器，负责生成 Mermaid 时序图所需的所有元数据。

关键组件:
---------------
1.  **`@trace` 装饰器**: 用户使用的主要接口。
2.  **上下文管理**: 使用 `LogContext` 跟踪“谁调用了谁”，确保嵌套调用链正确。
3.  **事件记录**: 生成包含源、目标、动作和参数的 `FlowEvent` 对象。
4.  **自动目标解析**: 智能猜测参与者名称（优先使用类名，其次是模块名）。
"""

import functools
import logging
import inspect
import re
import reprlib
import traceback
from dataclasses import dataclass
from typing import (
    Optional,
    Any,
    Callable,
    Tuple,
    Dict,
    Union,
    TypeVar,
    cast,
    overload,
    List,
)

from .events import FlowEvent
from .context import LogContext
from .config import config

# 流程事件的专用 Logger 名称
FLOW_LOGGER_NAME = "mermaid_trace.flow"

F = TypeVar("F", bound=Callable[..., Any])

def get_flow_logger() -> logging.Logger:
    """
    返回用于记录 FlowEvent 的专用 Logger 实例。
    该 logger 将追踪日志与标准应用程序日志隔离开来。
    """
    return logging.getLogger(FLOW_LOGGER_NAME)

class FlowRepr(reprlib.Repr):
    """
    自定义 Repr 类，用于简化 Python 对象表示。
    1. 将包含内存地址的默认表示简化为 <ClassName> 格式。
    2. 自动合并列表/元组中连续相同的项，使图表更简洁。
    """

    def _group_items(self, items_str: List[str]) -> List[str]:
        """合并列表中连续相同的字符串。"""
        if not items_str:
            return []
        res = []
        current_item = items_str[0]
        current_count = 1
        for i in range(1, len(items_str)):
            if items_str[i] == current_item:
                current_count += 1
            else:
                if current_count > 1:
                    res.append(f"{current_item} x {current_count}")
                else:
                    res.append(current_item)
                current_item = items_str[i]
                current_count = 1
        # 处理最后一组
        if current_count > 1:
            res.append(f"{current_item} x {current_count}")
        else:
            res.append(current_item)
        return res

    def repr_list(self, obj: List[Any], level: int) -> str:
        """列表表示，支持重复项合并。"""
        n = len(obj)
        if n == 0:
            return "[]"
        items_str = []
        for i in range(min(n, self.maxlist)):
            items_str.append(self.repr1(obj[i], level - 1))

        grouped = self._group_items(items_str)
        if n > self.maxlist:
            grouped.append("...")
        return "[" + ", ".join(grouped) + "]"

    def repr_tuple(self, obj: Tuple[Any, ...], level: int) -> str:
        """元组表示，支持重复项合并。"""
        n = len(obj)
        if n == 0:
            return "()"
        if n == 1:
            return "(" + self.repr1(obj[0], level - 1) + ",)"
        items_str = []
        for i in range(min(n, self.maxtuple)):
            items_str.append(self.repr1(obj[i], level - 1))

        grouped = self._group_items(items_str)
        if n > self.maxtuple:
            grouped.append("...")
        return "(" + ", ".join(grouped) + ")"

    def repr1(self, x: Any, level: int) -> str:
        """重写单项表示，自动清理内存地址。"""
        # 检查对象是否使用了默认的 object.__repr__
        # 默认 repr 看起来像 <module.Class object at 0x...>
        raw = repr(x)
        if " object at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # 简化为 <ClassName>
            return f"<{x.__class__.__name__}>"

        # 处理其他包含内存地址的特殊 repr
        if " at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            # 尝试提取类名或直接简化
            return f"<{x.__class__.__name__}>"

        return super().repr1(x, level)

def _safe_repr(
    obj: Any, max_len: Optional[int] = None, max_depth: Optional[int] = None
) -> str:
    """
    安全地创建对象的字符串表示。
    
    此函数对于防止日志膨胀和追踪期间的运行时错误至关重要。
    它处理：
    1. **截断**: 限制字符串长度。
    2. **深度控制**: 限制嵌套结构的递归深度。
    3. **错误处理**: 捕获对象 `__repr__` 可能抛出的异常。
    4. **简化**: 自动简化包含内存地址的 Python 对象表示。
    """
    final_max_len = max_len if max_len is not None else config.max_string_length
    final_max_depth = max_depth if max_depth is not None else config.max_arg_depth

    try:
        # 使用自定义 FlowRepr 提供限制大小和简化表示的标准方法
        a_repr = FlowRepr()
        a_repr.maxstring = final_max_len
        a_repr.maxother = final_max_len
        a_repr.maxlevel = final_max_depth

        r = a_repr.repr(obj)

        # 最后一遍：使用正则捕获任何剩余的内存地址
        # (例如，reprlib 没有递归进入的类型)
        # 1. <__main__.Class object at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) object at 0x[0-9a-fA-F]+>",
            r"<\2>",
            r,
        )
        # 2. <Class at 0x...> -> <Class>
        r = re.sub(
            r"<([a-zA-Z0-9_.]+\.)?([a-zA-Z0-9_]+) at 0x[0-9a-fA-F]+>",
            r"<\2>",
            r,
        )

        # 双重检查长度限制，因为 reprlib 有时可能会略微超出
        if len(r) > final_max_len:
            return r[:final_max_len] + "..."
        return r
    except Exception:
        # 如果 repr() 失败（例如属性访问在 __repr__ 中引发错误）
        return "<unrepresentable>"


@dataclass
class _TraceConfig:
    """内部追踪配置容器，用于规避 PLR0913 (参数过多) 检查。"""

    capture_args: Optional[bool] = None
    max_arg_length: Optional[int] = None
    max_arg_depth: Optional[int] = None


def _format_args(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    config_obj: _TraceConfig,
) -> str:
    """
    将函数参数格式化为单个字符串，用于图表箭头标签。
    
    示例输出: "1, 'test', debug=True"
    
    这个字符串将显示在 Mermaid 图表的箭头上 (例如: `User->System: login(args...)`)。
    """
    final_capture = (
        config_obj.capture_args
        if config_obj.capture_args is not None
        else config.capture_args
    )
    if not final_capture:
        return ""

    parts: list[str] = []

    # 处理位置参数
    for arg in args:
        parts.append(
            _safe_repr(
                arg, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
            )
        )

    # 处理关键字参数
    for k, v in kwargs.items():
        val_str = _safe_repr(
            v, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
        )
        parts.append(f"{k}={val_str}")

    return ", ".join(parts)


def _resolve_target(
    func: Callable[..., Any], args: Tuple[Any, ...], target_override: Optional[str]
) -> str:
    """
    确定图表中“目标”参与者（被调用者）的名称。
    """
    if target_override:
        return target_override

    if args:
        first_arg = args[0]
        # 类方法
        if isinstance(first_arg, type):
            return first_arg.__name__
        # 实例方法 (排除简单类型)
        if hasattr(first_arg, "__class__") and not isinstance(
            first_arg, (str, int, float, bool, list, dict, set, tuple)
        ):
            return str(first_arg.__class__.__name__)

    module = inspect.getmodule(func)
    if module:
        return module.__name__.split(".")[-1]

    return "Unknown"


@dataclass
class _TraceMetadata:
    """内部追踪元数据容器，用于规避 PLR0913 (参数过多) 检查。"""

    source: str
    target: str
    action: str
    trace_id: str


def _log_interaction(
    logger: logging.Logger,
    meta: _TraceMetadata,
    params: str,
) -> None:
    """记录调用事件。"""
    req_event = FlowEvent(
        source=meta.source,
        target=meta.target,
        action=meta.action,
        message=meta.action,
        params=params,
        trace_id=meta.trace_id,
    )
    logger.info(
        f"{meta.source}->{meta.target}: {meta.action}", extra={"flow_event": req_event}
    )


def _log_return(
    logger: logging.Logger,
    source: str,
    target: str,
    action: str,
    result: Any,
    trace_id: str,
    config_obj: _TraceConfig,
) -> None:
    """记录返回事件。"""
    result_str = ""
    final_capture = (
        config_obj.capture_args
        if config_obj.capture_args is not None
        else config.capture_args
    )

    if final_capture:
        result_str = _safe_repr(
            result, max_len=config_obj.max_arg_length, max_depth=config_obj.max_arg_depth
        )

    resp_event = FlowEvent(
        source=target,
        target=source,
        action=action,
        message="Return",
        is_return=True,
        result=result_str,
        trace_id=trace_id,
    )
    logger.info(f"{target}->{source}: Return", extra={"flow_event": resp_event})


def _log_error(
    logger: logging.Logger,
    meta: _TraceMetadata,
    error: Exception,
) -> None:
    """记录异常事件。"""
    stack_trace = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )

    err_event = FlowEvent(
        source=meta.target,
        target=meta.source,
        action=meta.action,
        message=str(error),
        is_return=True,
        is_error=True,
        error_message=str(error),
        stack_trace=stack_trace,
        trace_id=meta.trace_id,
    )
    logger.error(
        f"{meta.target}-x{meta.source}: Error", extra={"flow_event": err_event}
    )


@overload
def trace_interaction(func: F) -> F: ...

@overload
def trace_interaction(
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: Optional[bool] = None,
    max_arg_length: Optional[int] = None,
    max_arg_depth: Optional[int] = None,
) -> Callable[[F], F]: ...

def trace_interaction(
    func: Optional[F] = None,
    *,
    source: Optional[str] = None,
    target: Optional[str] = None,
    name: Optional[str] = None,
    action: Optional[str] = None,
    capture_args: Optional[bool] = None,
    max_arg_length: Optional[int] = None,
    max_arg_depth: Optional[int] = None,
) -> Union[F, Callable[[F], F]]:  # noqa: PLR0913
    """追踪装饰器主入口。"""
    final_target = target or name

    if func is not None and callable(func):
        return _create_decorator(
            func,
            source,
            final_target,
            action,
            _TraceConfig(capture_args, max_arg_length, max_arg_depth),
        )

    def factory(f: F) -> F:
        return _create_decorator(
            f,
            source,
            final_target,
            action,
            _TraceConfig(capture_args, max_arg_length, max_arg_depth),
        )

    return factory


def _create_decorator(
    func: F,
    source: Optional[str],
    target: Optional[str],
    action: Optional[str],
    config_obj: _TraceConfig,
) -> F:
    """内部装饰器工厂。"""
    if action is None:
        action = func.__name__.replace("_", " ").title()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_source = source or LogContext.current_participant()
        trace_id = LogContext.current_trace_id()
        current_target = _resolve_target(func, args, target)

        meta = _TraceMetadata(current_source, current_target, action, trace_id)
        logger = get_flow_logger()
        params_str = _format_args(args, kwargs, config_obj)

        _log_interaction(logger, meta, params_str)

        with LogContext.scope({"participant": current_target, "trace_id": trace_id}):
            try:
                result = func(*args, **kwargs)
                _log_return(
                    logger,
                    current_source,
                    current_target,
                    action,
                    result,
                    trace_id,
                    config_obj,
                )
                return result
            except Exception as e:
                _log_error(logger, meta, e)
                raise e

    # ... 异步 wrapper 逻辑类似 (省略)
    return cast(F, wrapper)
```
