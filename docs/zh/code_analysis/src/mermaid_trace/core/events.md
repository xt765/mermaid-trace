# src/mermaid_trace/core/events.py 代码分析

## 文件概览 (File Overview)
`src/mermaid_trace/core/events.py` 定义了数据结构 `FlowEvent`。
你可以把它看作是一个"数据包"，里面装着画一条线所需的所有信息：谁调用的（Source）、调用的谁（Target）、什么动作（Action）、参数是什么、结果是什么。

## 核心概念 (Key Concepts)

*   **Data Class (数据类)**: Python 3.7+ 引入的特性 (`@dataclass`)。它自动为你生成 `__init__`, `__repr__` 等方法，非常适合用来定义只用来存数据的类。
*   **Mermaid Syntax (Mermaid 语法)**: 一种用文本描述图表的语言。例如 `A->>B: Hello` 会画出 A 指向 B 的箭头。这个文件负责把 Python 对象转换成这种文本格式。

## 代码详解 (Code Walkthrough)

```python
from dataclasses import dataclass, field
import time
from typing import Optional

@dataclass
class FlowEvent:
    """
    表示执行流程中的单个交互或步骤。
    
    此数据结构捕获生成一行 Mermaid 序列图所需的所有元数据。
    它从跟踪装饰器传递到日志处理器。
    
    Attributes:
        source (str): 发起动作的参与者名称 (调用者)。
        target (str): 接收动作的参与者名称 (被调用者)。
        action (str): 动作的简短描述 (例如：函数名)。
        message (str): 显示在图表箭头上的文本。
        timestamp (float): 事件发生的 Unix 时间戳。
        is_return (bool): 如果此事件表示函数调用的返回，则为 True。
        is_error (bool): 如果此事件表示异常/错误，则为 True。
        error_message (Optional[str]): 如果 is_error 为 True，则为错误消息。
        params (Optional[str]): 字符串化的函数参数 (用于请求事件)。
        result (Optional[str]): 字符串化的返回值 (用于响应事件)。
    """
    source: str
    target: str
    action: str
    message: str
    timestamp: float = field(default_factory=time.time)
    is_return: bool = False
    is_error: bool = False
    error_message: Optional[str] = None
    params: Optional[str] = None
    result: Optional[str] = None
    
    def to_mermaid_line(self) -> str:
        """
        将此事件转换为有效的 Mermaid 序列图语法行。
        
        Returns:
            str: 类似 "A->>B: message" 或 "B-->>A: return" 的字符串。
        """
        # 清理名称以确保它们是有效的 Mermaid 参与者标识符
        # 例如 "My Class" -> "My_Class"
        src = self._sanitize(self.source)
        tgt = self._sanitize(self.target)
        
        # 确定箭头类型
        # ->> : 带箭头的实线 (同步调用)
        # -->> : 带箭头的虚线 (返回)
        # --x : 带叉的虚线 (错误)
        arrow = "-->>" if self.is_return else "->>"
        
        # 根据事件类型格式化消息
        if self.is_error:
            arrow = "--x"
            msg = f"Error: {self.error_message}"
        elif self.is_return:
            msg = f"Return: {self.result}" if self.result else "Return"
        else:
            # 对于请求，如果可用则包含参数
            msg = f"{self.message}({self.params})" if self.params else self.message
            
        return f"{src}{arrow}{tgt}: {msg}"

    def _sanitize(self, name: str) -> str:
        """
        替换可能破坏 Mermaid 语法的参与者名称中的字符。
        
        Args:
            name (str): 原始参与者名称。
            
        Returns:
            str: 适合 Mermaid 使用的安全名称。
        """
        # 将空格、点和连字符替换为下划线
        return name.replace(" ", "_").replace(".", "_").replace("-", "_")
```

## 新手指南 (Beginner's Guide)

*   **为什么要 `_sanitize` (清理) 名称？**
    Mermaid 语法对参与者的名字很敏感。如果你写 `User Controller->>Database: Query`，Mermaid 可能会困惑，因为它不允许名字里有空格（除非用引号包起来）。把空格变成下划线 (`User_Controller`) 是最简单安全的做法。

*   **`field(default_factory=time.time)` 是什么？**
    在 dataclass 中，你不能直接写 `timestamp: float = time.time()`。因为这样 `time.time()` 只会在类定义的时候执行一次，所有实例的时间戳都会是一样的！使用 `default_factory` 告诉 Python："每次创建新对象时，请运行这个函数来获取默认值"。
