# 文件: src/mermaid_trace/core/formatter.py

## 概览
本文件实现了 `MermaidFormatter` 类，它是 Python `logging.Formatter` 的子类。它的职责是将 `FlowEvent` 对象转换为符合 Mermaid 语法的字符串行。

## 核心功能分析

### 格式化逻辑 (`_to_mermaid_line`)
这是核心转换函数。它根据事件属性决定 Mermaid 的语法：
-   **调用 (Call)**: `Source->>Target: Message`
-   **返回 (Return)**: `Target-->>Source: Message`
-   **错误 (Error)**: `Target--xSource: Message`

### 名称清洗 (`_sanitize`)
Mermaid 对参与者名称（Participant Name）有严格的语法要求（通常不支持空格或特殊字符，除非使用别名）。
为了简化实现并保证兼容性，该函数使用正则表达式将所有非字母数字字符替换为下划线。例如，`My Service` 会变成 `My_Service`。

### 消息转义 (`_escape_message`)
Mermaid 箭头上的文本如果包含换行符，会破坏图表语法。该函数将换行符替换为 HTML 的 `<br/>`，以便在图表中正确显示多行文本。

## 源代码与中文注释

```python
import logging
import re
from typing import Optional
from .events import FlowEvent

class MermaidFormatter(logging.Formatter):
    """
    自定义格式化程序，将 FlowEvents 转换为 Mermaid 时序图语法。
    """

    def format(self, record: logging.LogRecord) -> str:
        # 1. 检索 FlowEvent
        # getattr 用于安全访问，防止处理非结构化日志时出错
        event: Optional[FlowEvent] = getattr(record, 'flow_event', None)
        
        if not event:
            # 如果标准日志意外到达此处理程序，则回退到默认格式
            return super().format(record)

        # 2. 将事件转换为 Mermaid 行
        return self._to_mermaid_line(event)

    def _to_mermaid_line(self, event: FlowEvent) -> str:
        """
        将 FlowEvent 转换为 Mermaid 语法字符串。
        """
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
            
        # 可选：如果 trace_id 更改，添加注释或组（在单行格式中未实现）
        # 目前，我们只输出交互。
        
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
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
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
        msg = msg.replace('\n', '<br/>')
        # 如果需要，我们可能想要转义其他字符，但通常 : 之后的文本是宽容的。
        return msg
```
