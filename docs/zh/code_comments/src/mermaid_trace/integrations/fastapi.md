# 文件: src/mermaid_trace/integrations/fastapi.py

## 概览
本文件实现了 `MermaidTraceMiddleware`，这是一个用于 FastAPI/Starlette 应用的中间件。它能够自动拦截所有 HTTP 请求，将其转换为 Mermaid 时序图中的交互。

## 核心功能分析

### 请求生命周期追踪
中间件覆盖了完整的请求-响应周期：
1.  **请求拦截**: 在处理任何业务逻辑之前，拦截 HTTP 请求。
2.  **源识别**: 尝试从 HTTP Header (`X-Source`) 获取调用者名称，如果未提供则默认为 "Client"。
3.  **Trace ID 管理**: 检查 `X-Trace-ID`，如果存在则沿用（分布式追踪），否则生成新的 ID。
4.  **上下文初始化**: 使用 `LogContext.ascope` 初始化当前请求的上下文。这确保了该请求后续的所有代码（包括路由处理函数、依赖注入、其他中间件）都能共享同一个 `Trace ID` 和 `Participant` 信息。
5.  **执行与计时**: 调用 `call_next(request)` 执行实际业务逻辑，并计算耗时。
6.  **响应/错误记录**: 记录成功的响应（带状态码和耗时）或捕获异常并记录错误。

### 异常处理注意事项
FastAPI 有自己的异常处理机制（Exception Handlers）。如果应用中定义了全局异常处理器，异常可能在到达此中间件之前就被捕获并转换为普通的 JSON 响应（例如 500 Internal Server Error）。在这种情况下，MermaidTrace 会将其记录为正常的“返回”箭头（带 500 状态码），而不是“错误”箭头（`-x`）。只有未被捕获的异常才会触发错误日志。

## 源代码与中文注释

```python
from typing import Any, TYPE_CHECKING
import time
import uuid

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
else:
    try:
        from fastapi import Request, Response
        from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    except ImportError:
        # 处理 FastAPI/Starlette 未安装的情况。
        # 我们定义虚拟类型以防止导入时的 NameError，
        # 但实例化将在 __init__ 中显式失败。
        BaseHTTPMiddleware = object  # type: ignore[misc,assignment]
        Request = Any  # type: ignore[assignment]
        Response = Any  # type: ignore[assignment]
        RequestResponseEndpoint = Any  # type: ignore[assignment]

class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件，用于将 HTTP 请求作为时序图中的交互进行追踪。
    
    此中间件充当追踪 Web 请求的入口点。它：
    1. 识别客户端（Source）。
    2. 记录传入请求。
    3. 为请求生命周期初始化 `LogContext`。
    4. 记录响应或错误。
    """
    def __init__(self, app: Any, app_name: str = "FastAPI"):
        """
        初始化中间件。
        
        参数:
            app: FastAPI 应用程序实例。
            app_name: 图表中显示的服务名称（例如 "UserAPI"）。
        """
        if BaseHTTPMiddleware is object: # type: ignore[comparison-overlap]
             raise ImportError("FastAPI/Starlette is required to use MermaidTraceMiddleware")
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        拦截传入请求。
        
        参数:
            request (Request): 传入的 HTTP 请求。
            call_next (Callable): 调用下一个中间件或端点的函数。
            
        返回:
            Response: HTTP 响应。
        """
        # 1. 确定来源（客户端）
        # 尝试从 Header 获取特定 ID（用于分布式追踪），
        # 否则回退到 "Client"。
        source = request.headers.get("X-Source", "Client")
        
        # 确定 Trace ID
        # 检查 X-Trace-ID Header 或生成新的 UUID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        
        # 2. 确定动作
        # 格式: "METHOD /path" (例如 "GET /users")
        action = f"{request.method} {request.url.path}"
        
        logger = get_flow_logger()
        
        # 3. 记录请求 (Source -> App)
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            params=f"query={request.query_params}" if request.query_params else None,
            trace_id=trace_id
        )
        logger.info(f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event})
        
        # 4. 设置上下文并处理请求
        # 我们将当前参与者设置为应用程序名称。
        # `ascope` 确保此上下文适用于在 `call_next` 内运行的所有代码。
        # 这包括路由处理程序、依赖项以及在此之后调用的其他中间件。
        async with LogContext.ascope({"participant": self.app_name, "trace_id": trace_id}):
            start_time = time.time()
            try:
                # 将控制权传递给应用程序
                # 这执行实际的路由逻辑
                response = await call_next(request)
                
                # 5. 记录响应 (App -> Source)
                # 计算响应标签的执行持续时间
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)",
                    trace_id=trace_id
                )
                logger.info(f"{self.app_name}->{source}: Return", extra={"flow_event": resp_event})
                return response
                
            except Exception as e:
                # 6. 记录错误 (App --x Source)
                # 这捕获了冒泡到中间件的未处理异常
                # 注意: FastAPI 的 ExceptionHandlers 可能会在此之前捕获它。
                # 如果是这样，你可能会看到一个带有 500 状态的成功返回。
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e),
                    trace_id=trace_id
                )
                logger.error(f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event})
                raise
```
