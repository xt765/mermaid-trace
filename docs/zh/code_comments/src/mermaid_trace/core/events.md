# 文件: src/mermaid_trace/core/events.py

## 概览
`events.py` 模块定义了追踪系统的事件结构。它使用 `dataclasses` 来存储追踪过程中的每一个交互细节，这些细节随后被格式化程序转换为 Mermaid 语法。

## 核心功能分析

### 1. `Event` (抽象基类)
定义了所有事件必须具备的通用属性，如源 (`source`)、目标 (`target`)、动作 (`action`)、时间戳 (`timestamp`) 和追踪 ID (`trace_id`)。

### 2. `FlowEvent` (具体类)
这是目前库中使用的主要事件类型，代表执行流中的单个交互。

- **核心属性**:
    - `source` / `target`: 发起方和接收方。
    - `action`: 操作的简短名称。
    - `message`: 箭头上的详细说明文字。
    - `trace_id`: 关联一整条调用链。
- **状态属性**:
    - `is_return`: 标记这是一个返回事件（Mermaid 中显示为虚线箭头）。
    - `is_error`: 标记发生了异常（Mermaid 中显示为 `X` 箭头）。
- **数据属性**:
    - `params`: 序列化后的函数参数。
    - `result`: 序列化后的返回值。
    - `error_message` / `stack_trace`: 发生错误时的详细信息。

## 源代码与中文注释

```python
"""
事件定义模块

本模块定义了追踪系统的事件结构。
它提供了一个抽象的 Event 基类和一个具体的 FlowEvent 实现，代表执行流中的单个交互。
"""

from abc import ABC
from dataclasses import dataclass, field
import time
from typing import Optional


class Event(ABC):
    """
    所有事件类型的抽象基类。
    """
    source: str
    target: str
    action: str
    message: str
    timestamp: float
    trace_id: str


@dataclass
class FlowEvent(Event):
    """
    代表执行流中的单个交互或步骤。
    """

    # 必填字段
    source: str       # 发起动作的参与者
    target: str       # 接收动作的参与者
    action: str       # 操作的简短名称
    message: str      # 图表箭头上显示的详细消息
    trace_id: str     # 追踪会话的唯一标识符

    # 可选字段（带默认值）
    timestamp: float = field(default_factory=time.time)  # 事件创建的 Unix 时间戳
    is_return: bool = False                              # 是否为返回箭头
    is_error: bool = False                               # 是否发生了错误
    error_message: Optional[str] = None                  # 错误消息详情
    stack_trace: Optional[str] = None                    # 完整堆栈追踪
    params: Optional[str] = None                         # 字符串化的函数参数
    result: Optional[str] = None                         # 字符串化的返回值
    collapsed: bool = False                              # 该交互是否应在视觉上折叠（循环/折叠）
```
