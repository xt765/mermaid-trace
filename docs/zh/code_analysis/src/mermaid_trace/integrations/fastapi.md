# src/mermaid_trace/integrations/fastapi.py 代码分析

## 文件概览 (File Overview)
这个文件提供了与 [FastAPI](https://fastapi.tiangolo.com/) 框架的集成。
它实现了一个中间件 (`MermaidTraceMiddleware`)。只要把这个中间件加到你的 FastAPI 应用里，所有的 HTTP 请求都会自动被记录到序列图中。

## 核心概念 (Key Concepts)

*   **Middleware (中间件)**: 介于服务器和应用程序处理逻辑之间的软件层。它可以在请求到达具体 API 之前拦截它，也可以在响应返回给客户端之前修改它。
*   **Optional Dependency (可选依赖)**: 并不是所有用 `mermaid-trace` 的人都用 FastAPI。所以我们在文件开头用了 `try-except` 块来导入 FastAPI。如果用户没安装 FastAPI，这个模块也不会报错，除非他们尝试使用这个中间件。

## 代码详解 (Code Walkthrough)

```python
try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
except ImportError:
    # 处理未安装 FastAPI/Starlette 的情况。
    # 我们定义虚拟类型以防止导入时出现 NameError，
    # 但实例化将在 __init__ 中显式失败。
    BaseHTTPMiddleware = object # type: ignore
    Request = Any # type: ignore
    Response = Any # type: ignore
    RequestResponseEndpoint = Any # type: ignore

from typing import Any, Callable, Awaitable
from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger
import time

class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件，将 HTTP 请求作为交互跟踪在序列图中。
    
    此中间件充当跟踪 Web 请求的入口点。它：
    1. 识别客户端 (Source)。
    2. 记录传入请求。
    3. 初始化请求生命周期的 `LogContext`。
    4. 记录响应或错误。
    """
    def __init__(self, app: Any, app_name: str = "FastAPI"):
        """
        初始化中间件。
        
        Args:
            app: FastAPI 应用程序实例。
            app_name: 此服务在图表中显示的名称 (例如 "UserAPI")。
        """
        if BaseHTTPMiddleware is object: # type: ignore
             raise ImportError("FastAPI/Starlette is required to use MermaidTraceMiddleware")
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        拦截传入请求。
        
        Args:
            request (Request): 传入的 HTTP 请求。
            call_next (Callable): 调用下一个中间件或端点的函数。
            
        Returns:
            Response: HTTP 响应。
        """
        # 1. 确定来源 (客户端)
        # 尝试从标头获取特定 ID (用于分布式跟踪)，
        # 否则回退到 "Client"。
        source = request.headers.get("X-Source", "Client")
        
        # 2. 确定动作
        # 格式："METHOD /path" (例如 "GET /users")
        action = f"{request.method} {request.url.path}"
        
        logger = get_flow_logger()
        
        # 3. 记录请求 (Source -> App)
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            params=f"query={request.query_params}" if request.query_params else None
        )
        logger.info(f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event})
        
        # 4. 设置上下文并处理请求
        # 我们将当前参与者设置为应用程序名称。
        # `ascope` 确保此上下文应用于 `call_next` 内运行的所有代码。
        async with LogContext.ascope({"participant": self.app_name}):
            start_time = time.time()
            try:
                # 将控制权传递给应用程序
                response = await call_next(request)
                
                # 5. 记录响应 (App -> Source)
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)"
                )
                logger.info(f"{self.app_name}->{source}: Return", extra={"flow_event": resp_event})
                return response
                
            except Exception as e:
                # 6. 记录错误 (App --x Source)
                # 这捕获冒泡到中间件的未处理异常
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e)
                )
                logger.error(f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event})
                raise
```

## 新手指南 (Beginner's Guide)

*   **`dispatch` 函数的作用是什么？**
    在 `BaseHTTPMiddleware` 中，`dispatch` 是必须要重写的方法。它是处理请求的核心逻辑。所有的请求都会先流经这里，然后你调用 `call_next(request)` 把它传给下一个处理环节。当你 `await call_next(request)` 返回时，意味着请求已经处理完毕，你可以处理响应了。

*   **为什么要在中间件里设置 `LogContext`？**
    这是最关键的一步。HTTP 请求是整个调用链的起点。我们在中间件里用 `LogContext.ascope` 设置了上下文，那么在这个请求处理过程中调用的所有被 `@trace` 装饰的函数，都能自动知道"我现在属于哪个请求"，从而画出连贯的图表。

*   **分布式追踪 (X-Source)**
    代码里检查了 `X-Source` 请求头。如果你的系统是微服务架构，服务 A 调用 服务 B，服务 A 可以在请求头里加上 `X-Source: ServiceA`。这样服务 B 生成的图表就会显示 `ServiceA -> ServiceB`，而不是默认的 `Client -> ServiceB`。
