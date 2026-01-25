# 文件: src/mermaid_trace/core/events.py

## 概览
本文件定义了 `FlowEvent` 数据类。它是整个系统的核心数据结构，用于在运行时代码和最终的 Mermaid 输出之间传递信息。

## 核心功能分析

### 中间表示 (IR)
`FlowEvent` 充当了日志系统和可视化系统之间的“中间语言”。
-   它捕获了所有关于一次交互的元数据：谁（Source/Target），做了什么（Action），结果如何（Message/Params/Result），何时发生（Timestamp），以及属于哪个会话（Trace ID）。
-   这种解耦设计使得我们可以轻松更换后端的存储或格式化方式（例如，未来支持 PlantUML 或 JSON 输出），而无需修改捕获逻辑。

### 字段映射
-   `source` -> Mermaid 箭头左侧
-   `target` -> Mermaid 箭头右侧
-   `is_return` -> 决定箭头是实线 `->>` 还是虚线 `-->>`
-   `is_error` -> 决定箭头是否为错误样式 `--x`

## 源代码与中文注释

```python
from dataclasses import dataclass, field
import time
from typing import Optional

@dataclass
class FlowEvent:
    """
    表示执行流中的单个交互或步骤。
    
    此数据结构充当运行时代码执行和最终 Mermaid 图表输出之间的中间表示 (IR)。
    每个实例直接对应于时序图中的一个箭头或注释。
    
    字段映射到 Mermaid 语法组件如下：
    `source` -> `target`: `message`
    
    属性:
        source (str): 
            发起操作的参与者名称（"调用者"）。
            在 Mermaid 中：箭头左侧的参与者。
            
        target (str): 
            接收操作的参与者名称（"被调用者"）。
            在 Mermaid 中：箭头右侧的参与者。
            
        action (str): 
            操作的简短、人类可读的名称（例如，函数名）。
            用于分组或过滤日志，但通常与 message 冗余。
            
        message (str): 
            显示在图表箭头上的实际文本标签。
            示例: "getUser(id=1)" 或 "Return: User(name='Alice')"。
            
        timestamp (float): 
            事件发生的 Unix 时间戳（秒）。
            如果日志是异步处理的，用于排序事件，
            尽管 Mermaid 时序图主要依赖于行顺序。
            
        trace_id (str): 
            追踪会话的唯一标识符。
            允许从单个日志文件中过滤多个并发追踪，
            以便为单独的请求生成单独的图表。
            
        is_return (bool): 
            指示这是否为响应箭头的标志。
            如果为 True，箭头在 Mermaid 中绘制为虚线 (`-->`)。
            如果为 False，它是代表调用的实线 (`->`)。
            
        is_error (bool): 
            指示是否发生异常的标志。
            如果为 True，箭头可能会以不同方式设置样式（例如，`-x`）以显示失败。
            
        error_message (Optional[str]): 
            如果 `is_error` 为 True，详细的错误文本。
            可以添加为注释或包含在箭头标签中。
            
        params (Optional[str]): 
            函数参数的字符串化表示。
            仅针对请求事件（调用开始）捕获。
            
        result (Optional[str]): 
            返回值的字符串化表示。
            仅针对返回事件（调用结束）捕获。
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
```
