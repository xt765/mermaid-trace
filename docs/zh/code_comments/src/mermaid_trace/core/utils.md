# 文件: src/mermaid_trace/core/utils.py

## 概览
`utils.py` 模块提供了用于自动检测（Instrumentation）和补丁（Patching）的工具函数。它允许用户一次性对整个类或第三方库进行追踪，而无需手动给每个函数添加装饰器。

## 核心功能分析

### 1. `trace_class` (类装饰器)
该装饰器可以应用于类定义，它会自动遍历类的所有成员，并将 `@trace` 装饰器应用到所有符合条件的方法上。
- **过滤机制**:
    - 默认跳过私有方法（以 `_` 开头的方法）。
    - 始终跳过魔术方法（如 `__init__`, `__repr__`），以防止日志混乱或在生成 `repr` 时产生无限递归。
    - 支持通过 `exclude` 列表手动排除特定方法。
- **实现细节**: 使用 `inspect.getmembers` 获取成员，并使用 `setattr` 将原始方法替换为被追踪后的包装版本。

### 2. `patch_object` (猴子补丁)
该函数用于对已存在的对象、类或模块中的方法进行动态替换。
- **适用场景**: 
    - 无法修改源代码的第三方库（如 `requests`, `sqlalchemy`）。
    - 想要全局拦截某个特定行为时。
- **安全检查**: 在应用补丁前，会检查目标是否存在，防止因拼写错误导致运行时异常。

## 源代码与中文注释

```python
"""
用于自动检测和补丁的实用工具函数。
"""

import inspect
from typing import Any, Type, Optional, List
from .decorators import trace


def trace_class(
    cls: Optional[Type[Any]] = None,
    *,
    include_private: bool = False,
    exclude: Optional[List[str]] = None,
    **trace_kwargs: Any,
) -> Any:
    """
    类装饰器，自动追踪类中的所有方法。

    参数:
        cls: 要检测的类。
        include_private: 是否追踪私有方法。默认为 False。
        exclude: 要跳过的方法名称列表。
        **trace_kwargs: 传递给 @trace 装饰器的参数。
    """

    def _decorate_class(klass: Type[Any]) -> Type[Any]:
        exclude_set = set(exclude or [])

        for name, method in inspect.getmembers(klass):
            # 跳过排除列表中的方法
            if name in exclude_set:
                continue

            # 除非明确要求，否则跳过私有方法
            if name.startswith("_") and not include_private:
                # 默认不追踪 __init__ 以保持图表简洁，
                # 绝对不能追踪 __repr__，否则会导致记录日志时的无限递归。
                continue

            # 检查是否为可调用的函数或协程
            if inspect.isfunction(method) or inspect.iscoroutinefunction(method):
                try:
                    # 将方法替换为被追踪后的版本
                    setattr(klass, name, trace(**trace_kwargs)(method))
                except (AttributeError, TypeError):
                    # 忽略只读属性或不可设置的属性
                    pass
        return klass

    if cls is None:
        return _decorate_class
    return _decorate_class(cls)


def patch_object(obj: Any, method_name: str, **trace_kwargs: Any) -> None:
    """
    使用追踪功能对对象或类的方法进行猴子补丁（Monkey-patch）。
    非常适用于无法修改源码的第三方库。

    参数:
        obj: 要打补丁的对象、类或模块。
        method_name: 方法名。
        **trace_kwargs: @trace 的参数。

    用法示例:
        import requests
        patch_object(requests, 'get', action="HTTP GET")
    """
    if not hasattr(obj, method_name):
        raise AttributeError(f"{obj} 没有任何名为 '{method_name}' 的属性")

    original = getattr(obj, method_name)

    # 应用 trace 装饰器并替换原方法
    decorated = trace(**trace_kwargs)(original)
    setattr(obj, method_name, decorated)
```
