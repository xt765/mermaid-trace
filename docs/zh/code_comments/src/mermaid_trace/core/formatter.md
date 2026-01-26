# 文件: src/mermaid_trace/core/formatter.py

## 概览
本文件实现了事件格式化系统，包括 `BaseFormatter` 抽象基类和 `MermaidFormatter` 具体实现。它的职责是将 `Event` 对象转换为特定格式的字符串，主要是 Mermaid 时序图语法。

## 核心功能分析

### 抽象层设计
- **BaseFormatter**: 所有事件格式化器的抽象基类，定义了统一的格式化接口 `format_event`，便于扩展支持多种输出格式。
- **MermaidFormatter**: 继承自 `BaseFormatter`，专门将 `Event` 对象转换为 Mermaid 时序图语法。

### 格式化逻辑 (`format_event`)
这是核心转换函数，替代了原来的 `_to_mermaid_line`。它根据事件属性决定 Mermaid 的语法：
- **调用 (Call)**: `Source->>Target: Message`
- **返回 (Return)**: `Target-->>Source: Message`
- **错误 (Error)**: `Target--xSource: Message`

### 扩展支持
- 新的设计支持处理多种事件类型，不仅限于 `FlowEvent`
- 提供了对非 `FlowEvent` 类型的回退处理

## 源代码与中文注释

```python
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional
from .events import Event, FlowEvent

class BaseFormatter(ABC, logging.Formatter):
    """
    所有事件格式化器的抽象基类。
    
    这为不同的格式化器提供了公共接口，允许扩展和支持多种输出格式。
    """
    
    @abstractmethod
    def format_event(self, event: Event) -> str:
        """
        将 Event 格式化为所需的输出字符串。
        
        参数:
            event: 要格式化的事件
            
        返回:
            事件的格式化字符串表示
        """
        pass
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化包含事件的日志记录。
        
        参数:
            record: 要格式化的日志记录
            
        返回:
            记录的格式化字符串表示
        """
        # 检索 Event
        event: Optional[Event] = getattr(record, "flow_event", None)

        if not event:
            # 如果标准日志意外到达此处理程序，则回退到默认格式
            return super().format(record)

        # 将事件转换为所需格式
        return self.format_event(event)


class MermaidFormatter(BaseFormatter):
    """
    自定义格式化器，将 Events 转换为 Mermaid 时序图语法。
    """

    def format_event(self, event: Event) -> str:
        """
        将 Event 转换为 Mermaid 语法字符串。
        
        参数:
            event: 要格式化的事件
            
        返回:
            事件的 Mermaid 语法字符串表示
        """
        if not isinstance(event, FlowEvent):
            # 非 FlowEvent 类型的回退处理
            return f"{event.get_source()}->>{event.get_target()}: {event.get_message()}"
        
        # 清洗参与者名称以避免 Mermaid 中的语法错误
        src = self._sanitize(event.source)
        tgt = self._sanitize(event.target)

        # 确定箭头类型
        # ->> : 带箭头的实线（同步调用）
        # -->> : 带箭头的虚线（返回）
        # --x : 带叉的虚线（错误）
        arrow = "-->>" if event.is_return else "->>"

        msg = ""
        if event.is_error:
            arrow = "--x"
            msg = f"Error: {event.error_message}"
        elif event.is_return:
            # 对于返回，我们通常显示返回值或仅显示 "Return"
            msg = f"Return: {event.result}" if event.result else "Return"
        else:
            # 对于调用，我们显示 Action(Params) 或仅显示 Action
            msg = f"{event.message}({event.params})" if event.params else event.message

        # 转义消息以确保 Mermaid 安全（例如替换换行符）
        msg = self._escape_message(msg)

        # 格式: Source->>Target: Message
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """
        清洗参与者名称以使其成为有效的 Mermaid 标识符。
        允许字母数字和下划线。替换其他字符。
        
        Mermaid 不喜欢参与者别名中的空格或特殊字符，
        除非它们被引用（为了简单起见，我们这里不这样做），
        所以我们将它们替换为下划线。
        """
        # 将任何非字母数字字符（下划线除外）替换为下划线
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # 确保它不以数字开头（Mermaid 有时不喜欢这样）
        if clean_name and clean_name[0].isdigit():
            clean_name = "_" + clean_name
        return clean_name

    def _escape_message(self, msg: str) -> str:
        """
        转义消息文本中的特殊字符。
        Mermaid 消息可以包含大多数字符，但 : 和换行符可能很棘手。
        """
        # 将换行符替换为 <br/> 以便在 Mermaid 中显示
        msg = msg.replace("\n", "<br/>")
        # 如果需要，我们可能想要转义其他字符，但通常 : 之后的文本是宽容的。
        return msg
```
