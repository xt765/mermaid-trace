# 配置模块 (config.py)

`config.py` 模块为 MermaidTrace 库提供了一个集中的配置系统。它允许用户全局控制库的行为，例如参数捕获、字符串截断限制以及异步队列大小。

## 核心功能

- **集中配置**: 使用 `MermaidConfig` 数据类管理所有全局设置。
- **环境变量支持**: 支持通过环境变量动态加载配置。
- **行为控制**: 控制是否捕获函数参数、限制字符串长度以防止日志文件过大。

## 关键设计

### 1. MermaidConfig 数据类

使用 `dataclasses.dataclass` 定义配置结构，提供默认值。

| 属性 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `capture_args` | `bool` | `True` | 是否捕获函数参数和返回值。出于性能或隐私考虑，可设置为 `False`。 |
| `max_string_length` | `int` | `50` | 对象字符串表示的最大长度。防止日志文件中出现超长字符串。 |
| `max_arg_depth` | `int` | `1` | 嵌套对象（如列表/字典）的最大递归深度。 |
| `queue_size` | `int` | `1000` | 异步队列的大小。 |

### 2. 环境变量加载

`from_env` 类方法允许从系统环境变量中提取配置，方便在不同环境（开发、生产）中灵活调整。

```python
@classmethod
def from_env(cls) -> "MermaidConfig":
    return cls(
        capture_args=os.getenv("MERMAID_TRACE_CAPTURE_ARGS", "true").lower() == "true",
        max_string_length=int(os.getenv("MERMAID_TRACE_MAX_STRING_LENGTH", "50")),
        max_arg_depth=int(os.getenv("MERMAID_TRACE_MAX_ARG_DEPTH", "1")),
        queue_size=int(os.getenv("MERMAID_TRACE_QUEUE_SIZE", "1000")),
    )
```

## 源码分析与注释

```python
@dataclass
class MermaidConfig:
    """
    Mermaid Trace 的全局配置设置。
    """

    # 是否捕获参数和返回值
    capture_args: bool = True
    
    # 字符串截断长度，防止日志爆炸
    max_string_length: int = 50
    
    # 嵌套对象解析深度
    max_arg_depth: int = 1
    
    # 异步处理器队列大小
    queue_size: int = 1000

    @classmethod
    def from_env(cls) -> "MermaidConfig":
        """
        从环境变量加载配置。
        支持：
        MERMAID_TRACE_CAPTURE_ARGS
        MERMAID_TRACE_MAX_STRING_LENGTH
        MERMAID_TRACE_MAX_ARG_DEPTH
        MERMAID_TRACE_QUEUE_SIZE
        """
        return cls(
            capture_args=os.getenv("MERMAID_TRACE_CAPTURE_ARGS", "true").lower() == "true",
            max_string_length=int(os.getenv("MERMAID_TRACE_MAX_STRING_LENGTH", "50")),
            max_arg_depth=int(os.getenv("MERMAID_TRACE_MAX_ARG_DEPTH", "1")),
            queue_size=int(os.getenv("MERMAID_TRACE_QUEUE_SIZE", "1000")),
        )

# 全局配置单例实例
config = MermaidConfig()
```
