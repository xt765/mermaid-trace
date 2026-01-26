# 文件: src/mermaid_trace/core/events.py

## 概览
本文件定义了事件系统的核心抽象，包括 `Event` 抽象基类和 `FlowEvent` 具体实现。这些类用于表示执行流程中的单个交互事件，例如函数调用、返回或异常。

## 核心功能分析

### 抽象层设计
- **Event**: 所有事件类型的抽象基类，定义了统一的事件接口，便于扩展支持多种事件类型和输出格式。
- **FlowEvent**: 继承自 `Event`，表示执行流程中的单个交互事件，包含详细的事件属性。

### 中间表示 (IR)
`FlowEvent` 充当了日志系统和可视化系统之间的“中间语言”。
- 它捕获了所有关于一次交互的元数据：谁（Source/Target），做了什么（Action），结果如何（Message/Params/Result），何时发生（Timestamp），以及属于哪个会话（Trace ID）。
- 这种解耦设计使得我们可以轻松更换后端的存储或格式化方式（例如，未来支持 PlantUML 或 JSON 输出），而无需修改捕获逻辑。

### 字段映射
- `source` -> 箭头左侧
- `target` -> 箭头右侧
- `is_return` -> 决定箭头是实线 `->>` 还是虚线 `-->>`
- `is_error` -> 决定箭头是否为错误样式 `--x`

## 源代码与中文注释

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Optional


class Event(ABC):
    """
    所有事件类型的抽象基类。
    
    这为不同类型的事件提供了通用接口，允许扩展和支持多种输出格式。
    """
    
    @abstractmethod
    def get_source(self) -> str:
        """获取事件的来源。"""
        pass
    
    @abstractmethod
    def get_target(self) -> str:
        """获取事件的目标。"""
        pass
    
    @abstractmethod
    def get_action(self) -> str:
        """获取事件的动作名称。"""
        pass
    
    @abstractmethod
    def get_message(self) -> str:
        """获取事件的消息文本。"""
        pass
    
    @abstractmethod
    def get_timestamp(self) -> float:
        """获取事件的时间戳。"""
        pass
    
    @abstractmethod
    def get_trace_id(self) -> str:
        """获取事件的追踪 ID。"""
        pass


@dataclass
class FlowEvent(Event):
    """
    表示执行流程中的单个交互或步骤。

    此数据结构充当运行时代码执行与最终图表输出之间的中间表示 (IR)。每个实例
    直接对应于图表中的一个箭头或注释。

    字段映射到图表语法组件如下：
    `source` -> `target`: `message`

    属性:
        source (str):
            发起动作的参与者名称（"调用者"）。
            在时序图中：箭头左侧的参与者。
            
        target (str):
            接收动作的参与者名称（"被调用者"）。
            在时序图中：箭头右侧的参与者。
            
        action (str):
            操作的简短可读名称（例如函数名）。
            用于分组或过滤日志，但通常与 message 冗余。
            
        message (str):
            显示在图表箭头上的实际文本标签。
            示例："getUser(id=1)" 或 "Return: User(name='Alice')"。
            
        timestamp (float):
            事件发生时的 Unix 时间戳（秒）。
            用于异步处理日志时对事件进行排序。
            
        trace_id (str):
            跟踪会话的唯一标识符。
            允许从单个日志文件过滤多个并发跟踪，为
            单独的请求生成单独的图表。
            
        is_return (bool):
            指示这是否是响应箭头的标志。
            如果为 True，箭头在时序图中绘制为虚线。
            如果为 False，它是代表调用的实线。
            
        is_error (bool):
            指示是否发生异常的标志。
            如果为 True，箭头可能会以不同方式样式化以显示失败。
            
        error_message (Optional[str]):
            如果 `is_error` 为 True，则为详细的错误文本。
            可以作为注释添加或包含在箭头标签中。
            
        params (Optional[str]):
            函数参数的字符串表示。
            仅为请求事件（调用开始）捕获。
            
        result (Optional[str]):
            返回值的字符串表示。
            仅为返回事件（调用结束）捕获。
    """

    source: str
    target: str
    action: str
    message: str
    trace_id: str
    timestamp: float = field(default_factory=time.time)
    is_return: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    params: Optional[str] = None
    result: Optional[str] = None
    
    def get_source(self) -> str:
        return self.source
    
    def get_target(self) -> str:
        return self.target
    
    def get_action(self) -> str:
        return self.action
    
    def get_message(self) -> str:
        return self.message
    
    def get_timestamp(self) -> float:
        return self.timestamp
    
    def get_trace_id(self) -> str:
        return self.trace_id
```