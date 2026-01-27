# 文件: src/mermaid_trace/integrations/fastapi.py

## 概览
`fastapi.py` 模块提供了将 MermaidTrace 集成到 FastAPI 应用中的中间件。它是 HTTP 请求与时序图生成逻辑之间的桥梁，负责自动捕获请求生命周期中的所有关键交互。

## 核心功能分析

### 1. 自动请求追踪
`MermaidTraceMiddleware` 拦截每一个进入 FastAPI 的 HTTP 请求。
- **请求捕获**: 记录 `Client -> API` 的调用，包含 HTTP 方法和路径。
- **响应捕获**: 记录 `API -> Client` 的返回，包含状态码和处理耗时。
- **异常捕获**: 如果请求处理过程中发生未捕获异常，中间件会记录一个错误事件（显示为带叉的虚线 `API --x Client`），并附带堆栈信息。

### 2. 追踪上下文管理
中间件利用 `LogContext.ascope` 为每个请求初始化一个独立的异步上下文。
- **Trace ID**: 自动生成或从 Header (`X-Trace-ID`) 中提取。该 ID 会贯穿该请求触发的所有内部函数调用。
- **Participant**: 设置当前服务的参与者名称（默认为 "FastAPI"）。

### 3. 分布式追踪支持
支持跨服务的追踪传递：
- **`X-Source`**: 允许调用方声明自己的身份。如果 A 服务调用 B 服务并带上 `X-Source: ServiceA`，B 服务的图表将显示 `ServiceA -> ServiceB` 而不是 `Client -> ServiceB`。
- **`X-Trace-ID`**: 允许跨服务关联同一个追踪 ID。

### 4. 条件依赖处理
该模块使用了条件导入技巧，使得即使环境中没有安装 FastAPI，项目其他部分依然可以正常运行，只有在真正实例化中间件时才会抛出错误。

## 源代码与中文注释

```python
"""
MermaidTrace 的 FastAPI 集成模块。

本模块提供必要的中间件，将 MermaidTrace 与 FastAPI 应用程序集成。
"""

from typing import Any, TYPE_CHECKING
import time
import uuid
import traceback

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

# ----------------------------------------------------------------------
# 条件导入：支持可选的 FastAPI 依赖
# ----------------------------------------------------------------------
if TYPE_CHECKING:
    # 仅用于静态类型检查
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
else:
    try:
        from fastapi import Request, Response
        from starlette.middleware.base import (
            BaseHTTPMiddleware,
            RequestResponseEndpoint,
        )
    except ImportError:
        # 如果未安装 FastAPI/Starlette，则使用占位符，防止导入报错
        BaseHTTPMiddleware = object  # type: ignore
        Request = Any
        Response = Any
        RequestResponseEndpoint = Any


class MermaidTraceMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件：将 HTTP 请求追踪为时序图中的交互。
    """

    def __init__(self, app: Any, app_name: str = "FastAPI"):
        """
        初始化中间件。
        
        参数:
            app: FastAPI 应用实例。
            app_name: 在图中显示的当前服务名称（如 "UserAPI"）。
        """
        if BaseHTTPMiddleware is object:
            raise ImportError(
                "使用 MermaidTraceMiddleware 需要安装 FastAPI/Starlette"
            )

        super().__init__(app)
        self.app_name = app_name

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        核心调度方法：拦截并追踪请求。
        """
        # 1. 提取元数据：支持分布式追踪 Header
        # X-Source: 谁在调用我？（默认 "Client"）
        source = request.headers.get("X-Source", "Client")
        
        # X-Trace-ID: 关联现有追踪，或生成新 ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        
        # 动作描述：例如 "GET /users"
        action = f"{request.method} {request.url.path}"
        
        logger = get_flow_logger()

        # 2. 记录请求进入事件 (Source -> App)
        req_event = FlowEvent(
            source=source,
            target=self.app_name,
            action=action,
            message=action,
            # 将查询参数记录在备注中
            params=f"query={request.query_params}" if request.query_params else None,
            trace_id=trace_id,
        )
        logger.info(
            f"{source}->{self.app_name}: {action}", extra={"flow_event": req_event}
        )

        # 3. 设置异步上下文并处理请求
        # 内部调用的 @trace 函数将自动继承此 trace_id 和 participant 身份
        async with LogContext.ascope(
            {"participant": self.app_name, "trace_id": trace_id}
        ):
            start_time = time.time()
            try:
                # 执行后续中间件和路由处理器
                response = await call_next(request)

                # 4. 记录成功返回事件 (App -> Source)
                duration = (time.time() - start_time) * 1000
                resp_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message="Return",
                    is_return=True,
                    result=f"{response.status_code} ({duration:.1f}ms)",
                    trace_id=trace_id,
                )
                logger.info(
                    f"{self.app_name}->{source}: Return",
                    extra={"flow_event": resp_event},
                )
                return response

            except Exception as e:
                # 5. 记录错误返回事件 (App --x Source)
                stack_trace = "".join(
                    traceback.format_exception(type(e), e, e.__traceback__)
                )
                err_event = FlowEvent(
                    source=self.app_name,
                    target=source,
                    action=action,
                    message=str(e),
                    is_return=True,
                    is_error=True,
                    error_message=str(e),
                    stack_trace=stack_trace,
                    trace_id=trace_id,
                )
                logger.error(
                    f"{self.app_name}-x{source}: Error", extra={"flow_event": err_event}
                )

                # 重新抛出异常，交给 FastAPI 标准错误处理
                raise
```