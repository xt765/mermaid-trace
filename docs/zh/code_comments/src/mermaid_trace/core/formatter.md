# 文件: src/mermaid_trace/core/formatter.py

## 概览
`formatter.py` 模块负责将追踪到的 `Event` 对象转换成各种文本格式。目前，它主要支持将事件转换为 Mermaid 时序图语法。为了防止图表由于重复调用（如循环）而过度膨胀，该模块实现了一套高效的**有状态智能折叠 (Stateful Intelligent Collapsing)** 机制。

## 核心功能分析

### 1. `BaseFormatter` (抽象基类)
继承自 `logging.Formatter`，为所有格式化程序提供统一接口。
- **`format` 方法**: 重写了标准日志库的格式化逻辑。它尝试从日志记录 (`LogRecord`) 中提取 `flow_event` 属性。如果存在，则进行特定格式化；否则回退到标准日志格式。

### 2. `MermaidFormatter` (具体实现)
核心格式化类，负责生成 Mermaid 语法并处理智能折叠。

- **智能折叠逻辑 (`format` 和 `flush`)**:
    - **缓冲机制**: 事件不会立即被转换，而是进入 `_event_buffer`。这允许 Formatter 观察后续事件以检测模式。
    - **模式检测**:
        - **长度 1 (重复调用)**: 检测连续相同的调用（如 `A -> B`, `A -> B`）。
        - **长度 2 (循环调用)**: 检测连续的“调用-返回”对（如 `A -> B`, `B -> A`）。
    - **状态流转**:
        - **Case 1 (模式匹配中)**: 如果新事件符合当前已建立的模式，则仅增加 `_pattern_count` 并继续缓冲。
        - **Case 2 (模式中断)**: 如果新事件打破了当前模式，则立即调用 `flush()` 输出之前折叠的结果，并开始新的模式检测。
        - **Case 3 (初始化/空闲)**: 将第一个事件存入缓冲区，等待下一个事件来确定是直接输出还是形成模式。
    - **强制刷新 (`flush`)**: 将缓冲区中的模式（或零散事件）转换为最终的 Mermaid 文本。对于折叠的模式，它会输出一次交互并在消息后追加 `(xN)` 计数。

- **参与者清洗 (`_sanitize`)**:
    - Mermaid 对参与者 ID 有严格要求（如不能有特殊字符，且不能以数字开头）。
    - **重命名映射**: 该方法使用正则替换非法字符，并在必要时添加前缀（如以数字开头时添加 `ID_`）。
    - **冲突解决与一致性**: 维护一个映射表确保同一个原始名称始终映射到同一个 Mermaid ID。如果两个不同名称清洗后产生了相同的 ID，它会自动添加数字后缀（如 `User_1`, `User_2`）以确保唯一性。

- **消息转义 (`_escape_message`)**:
    - 将换行符转换为 `<br/>`，确保多行内容能在 Mermaid 节点中正确显示。

## 源代码与中文注释

```python
"""
事件格式化模块

本模块提供格式化程序，将 Event 对象转换为各种输出格式。
目前主要支持 Mermaid 时序图语法。
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Set, Any, List, Tuple
from .events import Event, FlowEvent


class BaseFormatter(ABC, logging.Formatter):
    """
    所有事件格式化程序的抽象基类。
    """

    @abstractmethod
    def format_event(self, event: Event) -> str:
        """将 Event 格式化为目标字符串。"""
        pass

    @abstractmethod
    def get_header(self, title: str) -> str:
        """获取图表文件的头部定义。"""
        pass

    def format(self, record: logging.LogRecord) -> str:
        """
        重写标准日志格式化方法，从 record 中提取并格式化事件。
        """
        event: Optional[Event] = getattr(record, "flow_event", None)

        if not event:
            return super().format(record)

        return self.format_event(event)


class MermaidFormatter(BaseFormatter):
    """
    将事件转换为 Mermaid 时序图语法的格式化程序。
    核心特性：支持基于窗口检测的智能重复/循环折叠。
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # 映射原始参与者名称到清洗后的 Mermaid ID
        self._participant_map: Dict[str, str] = {}
        self._used_ids: Set[str] = set()

        # 智能折叠状态：跟踪事件窗口以检测模式（长度 1 或 2）
        self._event_buffer: List[FlowEvent] = []
        self._pattern_count: int = 0
        self._current_pattern: List[Tuple[str, str, str, bool]] = []

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化包含事件的日志记录。
        如果 record 包含 FlowEvent，它将被缓冲以进行模式折叠。
        注意：必须通过调用 flush() 来获取缓冲区中最后的输出。
        """
        event: Optional[Event] = getattr(record, "flow_event", None)

        if not event or not isinstance(event, FlowEvent):
            return super().format(record)

        # 创建当前事件的唯一特征标识
        event_key = (event.source, event.target, event.action, event.is_return)

        # 情况 1: 已经处于某种模式中
        if self._current_pattern:
            pattern_len = len(self._current_pattern)
            match_idx = len(self._event_buffer) % pattern_len

            if event_key == self._current_pattern[match_idx]:
                # 匹配成功：存入缓冲区
                self._event_buffer.append(event)
                if match_idx == pattern_len - 1:
                    self._pattern_count += 1
                return ""
            else:
                # 模式中断：刷新缓冲区，并处理当前新事件
                output = self.flush()
                prefix = output + "\n" if output else ""

                self._event_buffer = [event]
                return prefix.strip()

        # 情况 2: 尚未进入模式，但缓冲区已有数据
        if self._event_buffer:
            first = self._event_buffer[0]
            first_key = (first.source, first.target, first.action, first.is_return)

            if event_key == first_key:
                # 检测到模式长度 1 (连续重复: A, A)
                self._current_pattern = [first_key]
                self._event_buffer.append(event)
                self._pattern_count = 2
                return ""
            elif (
                event.is_return
                and event.source == first.target
                and event.target == first.source
                and event.action == first.action
            ):
                # 检测到模式长度 2 (循环调用: Call, Return)
                self._current_pattern = [first_key, event_key]
                self._event_buffer.append(event)
                self._pattern_count = 1
                return ""
            else:
                # 未形成模式，输出缓冲区中的旧事件，将当前事件存入缓冲区
                output = self.format_event(first, 1)
                self._event_buffer = [event]
                return output.strip()

        # 情况 3: 缓冲区为空（初始状态）
        # 我们始终至少缓冲一个事件，以便在下一个事件到来时判断是否可以折叠
        self._event_buffer = [event]
        return ""

    def flush(self) -> str:
        """
        强制刷新当前折叠的模式并返回其 Mermaid 表示。
        在文件关闭或需要立即查看结果时调用。
        """
        if not self._event_buffer:
            return ""

        output_lines = []

        if self._current_pattern:
            pattern_len = len(self._current_pattern)
            # 仅输出模式的一个周期，但带上 (xN) 计数
            for i in range(pattern_len):
                event = self._event_buffer[i]
                line = self.format_event(event, self._pattern_count)
                output_lines.append(line)
        else:
            # 缓冲区中只有未形成模式的散乱事件
            for event in self._event_buffer:
                output_lines.append(self.format_event(event, 1))

        # 重置折叠状态
        self._event_buffer = []
        self._current_pattern = []
        self._pattern_count = 0

        return "\n".join(output_lines)

    def get_header(self, title: str = "Log Flow") -> str:
        """返回 Mermaid 时序图头部定义。"""
        return f"sequenceDiagram\n    title {title}\n    autonumber\n\n"

    def format_event(self, event: Event, count: int = 1) -> str:
        """
        将 Event 对象转换为 Mermaid 语法行。
        """
        if not isinstance(event, FlowEvent):
            return f"{event.source}->>{event.target}: {event.message}"

        # 清洗名称
        src = self._sanitize(event.source)
        tgt = self._sanitize(event.target)

        # 确定箭头类型
        arrow = "-->>" if event.is_return else "->>"

        msg = ""
        if event.is_error:
            arrow = "--x"
            msg = f"Error: {event.error_message}"
        elif event.is_return:
            msg = f"Return: {event.result}" if event.result else "Return"
        else:
            msg = f"{event.message}({event.params})" if event.params else event.message

        # 如果被折叠，追加计数
        if count > 1:
            msg += f" (x{count})"

        # 转义特殊字符
        msg = self._escape_message(msg)

        # 构建基础语法行
        line = f"{src}{arrow}{tgt}: {msg}"

        # 附加错误堆栈信息（如有）
        if event.is_error and event.stack_trace:
            short_stack = self._escape_message(event.stack_trace[:300] + "...")
            note = f"note right of {tgt}: {short_stack}"
            return f"{line}\n{note}"

        # 处理手动标记为折叠的事件
        if event.collapsed and count == 1:
            note = f"note right of {src}: ( Sampled / Collapsed Interaction )"
            return f"{line}\n{note}"

        return line

    def _sanitize(self, name: str) -> str:
        """
        清洗参与者名称以符合 Mermaid 标识符规范，并解决命名冲突。
        """
        if name in self._participant_map:
            return self._participant_map[name]

        # 替换非字母数字字符为下划线
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if clean_name and clean_name[0].isdigit():
            clean_name = "_" + clean_name

        if not clean_name:
            clean_name = "Unknown"

        # 解决 ID 冲突：如果 clean_name 已被占用，则加数字后缀
        if clean_name in self._used_ids:
            original_clean = clean_name
            counter = 1
            while clean_name in self._used_ids:
                clean_name = f"{original_clean}_{counter}"
                counter += 1

        self._participant_map[name] = clean_name
        self._used_ids.add(clean_name)
        return clean_name

    def _escape_message(self, msg: str) -> str:
        """
        对消息文本进行转义，确保 Mermaid 渲染安全。
        """
        # 将换行符替换为 HTML 换行标签
        msg = msg.replace("\n", "<br/>")
        return msg
```