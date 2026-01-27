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
"""

import functools
import logging
import inspect
import re
import reprlib
import traceback
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
    """返回用于记录 FlowEvent 的专用 Logger 实例。"""
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
        raw = repr(x)
        # 处理标准的 <module.Class object at 0x...>
        if (
            " object at 0x" in raw
            and raw.startswith("<")
            and raw.endswith(">")
        ):
            return f"<{x.__class__.__name__}>"

        # 处理其他包含内存地址的特殊 repr
        if " at 0x" in raw and raw.startswith("<") and raw.endswith(">"):
            return f"<{x.__class__.__name__}>"

        return super().repr1(x, level)

def _safe_repr(
    obj: Any, max_len: Optional[int] = None, max_depth: Optional[int] = None
) -> str:
    """
    安全地创建对象的字符串表示。
    1. 限制长度和深度。
    2. 自动简化内存地址。
    3. 合并容器重复项。
    """
    final_max_len = max_len if max_len is not None else config.max_string_length
    final_max_depth = max_depth if max_depth is not None else config.max_arg_depth

    try:
        a_repr = FlowRepr()
        a_repr.maxstring = final_max_len
        a_repr.maxother = final_max_len
        a_repr.maxlevel = final_max_depth

        r = a_repr.repr(obj)

        # 使用正则进行最后的二次清理（针对某些特殊类型）
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

        if len(r) > final_max_len:
            return r[:final_max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable>"

# ... 模块其余部分 (_format_args, _resolve_target, _create_decorator 等) 逻辑保持一致
```
