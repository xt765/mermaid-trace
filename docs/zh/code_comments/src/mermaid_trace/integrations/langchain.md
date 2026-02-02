# 文件: src/mermaid_trace/integrations/langchain.py

## 概览

`langchain.py` 模块提供了将 MermaidTrace 集成到 LangChain 框架中的回调处理器（Callback Handler）。它允许开发者将大语言模型（LLM）的执行链、Agent 插件调用、以及 RAG（检索增强生成）流程自动可视化为 Mermaid 时序图。

## 核心功能分析

### 1. 自动流程追踪

`MermaidTraceCallbackHandler` 实现了 LangChain 的 `BaseCallbackHandler` 接口，能够捕获以下关键事件：

- **Chain (链) 开始与结束**: 记录链的调用层次。
- **LLM/ChatModel 开始与结束**: 记录模型请求及生成的响应。
- **Retriever (检索器) 开始与结束**: 记录 RAG 流程中的知识检索动作。
- **Tool (工具) 开始与结束**: 记录 Agent 调用外部工具的过程。

### 2. 参与者栈管理 (Participant Stack)

为了在时序图中准确地绘制“返回箭头”（`-->>`），该处理器内部维护了一个参与者栈。

- **嵌套支持**: 当 Chain 调用 LLM 时，栈能确保 LLM 的返回箭头指向正确的 Chain。
- **自动推断**: 结合 `LogContext`，它能自动识别当前调用的发起者（Source）和目标（Target）。

### 3. RAG 场景优化

针对 RAG 流程，专门处理了检索器的输入输出：

- **检索内容展示**: 在图表的消息中摘要显示检索到的文档数量或内容片段。

### 4. 条件依赖处理

与 FastAPI 集成类似，该模块采用条件导入。即使环境中没有安装 `langchain-core`，项目其他部分也能正常加载，只有在实际使用 LangChain 相关功能时才会检查依赖。

## 源代码与中文注释

```python
"""
MermaidTrace 的 LangChain 集成模块。

本模块提供回调处理器，用于捕获和可视化 LangChain 执行流。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

# ----------------------------------------------------------------------
# 条件导入：支持可选的 LangChain 依赖
# ----------------------------------------------------------------------
if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.documents import Document
else:
    try:
        from langchain_core.callbacks import BaseCallbackHandler
        from langchain_core.outputs import LLMResult
        from langchain_core.agents import AgentAction, AgentFinish
        from langchain_core.documents import Document
    except ImportError:
        BaseCallbackHandler = object
        LLMResult = Any
        AgentAction = Any
        AgentFinish = Any
        Document = Any

class MermaidTraceCallbackHandler(BaseCallbackHandler):
    """
    LangChain 回调处理器：将执行步骤转换为时序图。
    """

    def __init__(self, host_name: str = "LangChain"):
        """
        初始化处理器。

        参数:
            host_name: 在图中显示的宿主应用名称（如 "MyAI"）。
        """
        self.host_name = host_name
        self.logger = get_flow_logger()
        # 用于跟踪嵌套调用的参与者栈
        self._participant_stack: List[str] = []

    def _get_current_source(self) -> str:
        """获取当前调用的发起者"""
        if self._participant_stack:
            return self._participant_stack[-1]
        return str(LogContext.get("current_participant", self.host_name))

    def on_chain_start(
        self, serialized: Optional[Dict[str, Any]], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """当 Chain 开始执行时触发"""
        target = (
            (serialized.get("name") if serialized else None)
            or kwargs.get("name")
            or "Chain"
        )
        source = self._get_current_source()
      
        event = FlowEvent(
            source=source,
            target=target,
            action="Run Chain",
            message=f"Start Chain: {target}",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            params=str(inputs),
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )
        self._participant_stack.append(target)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """当 Chain 执行结束时触发"""
        if not self._participant_stack:
            return
          
        target = self._participant_stack.pop()
        source = self._get_current_source()
      
        event = FlowEvent(
            source=target,
            target=source,
            action="Finish Chain",
            message="Chain Complete",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            result=str(outputs),
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )

    def on_llm_start(
        self, serialized: Optional[Dict[str, Any]], prompts: List[str], **kwargs: Any
    ) -> None:
        """当 LLM 开始生成时触发"""
        target = (serialized.get("name") if serialized else None) or "LLM"
        source = self._get_current_source()
      
        event = FlowEvent(
            source=source,
            target=target,
            action="Prompt",
            message="LLM Request",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            params=str(prompts),
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )
        self._participant_stack.append(target)

    def on_chat_model_start(
        self,
        serialized: Optional[Dict[str, Any]],
        messages: List[List[Any]],
        **kwargs: Any,
    ) -> None:
        """当 Chat Model 开始执行时触发"""
        target = (serialized.get("name") if serialized else None) or "ChatModel"
        source = self._get_current_source()

        event = FlowEvent(
            source=source,
            target=target,
            action="Chat",
            message="ChatModel Request",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            params=str(messages),
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )
        self._participant_stack.append(target)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """当 LLM 生成结束时触发"""
        if not self._participant_stack:
            return
          
        source = self._participant_stack.pop()
        target = self._get_current_source()
      
        event = FlowEvent(
            source=source,
            target=target,
            action="Response",
            message="LLM/Chat Completion",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            result=str(response.generations),
            is_return=True,
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """当 LLM 发生错误时触发"""
        if not self._participant_stack:
            return
        target = self._participant_stack.pop()
        source = self._get_current_source()
        event = FlowEvent(
            source=target,
            target=source,
            action="Error",
            message=f"LLM Error: {type(error).__name__}",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            is_error=True,
            error_message=str(error),
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )

    def on_retriever_start(
        self,
        serialized: Optional[Dict[str, Any]],
        query: str,
        **kwargs: Any,
    ) -> None:
        """当 Retriever 开始执行时触发"""
        target = (serialized.get("name") if serialized else None) or "Retriever"
        source = self._get_current_source()

        event = FlowEvent(
            source=source,
            target=target,
            action="Retrieve",
            message=f"Query: {query[:50]}...",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            params=query,
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )
        self._participant_stack.append(target)

    def on_retriever_end(
        self,
        documents: Sequence[Document],
        *,
        run_id: Any = None,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> Any:
        """当 Retriever 执行结束时触发"""
        if not self._participant_stack:
            return

        target = self._participant_stack.pop()
        source = self._get_current_source()

        event = FlowEvent(
            source=target,
            target=source,
            action="Documents",
            message=f"Retrieved {len(documents)} docs",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            result=f"Count: {len(documents)}",
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )

    def on_tool_start(
        self, serialized: Optional[Dict[str, Any]], input_str: str, **kwargs: Any
    ) -> None:
        """当工具开始执行时触发"""
        target = (serialized.get("name") if serialized else None) or "Tool"
        source = self._get_current_source()

        event = FlowEvent(
            source=source,
            target=target,
            action="Call Tool",
            message=f"Tool: {target}",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            params=input_str,
        )
        self.logger.info(
            f"{source} -> {target}: {event.action}", extra={"flow_event": event}
        )
        self._participant_stack.append(target)

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """当工具执行结束时触发"""
        if not self._participant_stack:
            return

        target = self._participant_stack.pop()
        source = self._get_current_source()

        event = FlowEvent(
            source=target,
            target=source,
            action="Finish Tool",
            message="Tool Complete",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            result=str(output),
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """当 Chain 发生错误时触发"""
        if not self._participant_stack:
            return
        target = self._participant_stack.pop()
        source = self._get_current_source()
        event = FlowEvent(
            source=target,
            target=source,
            action="Error",
            message=f"Chain Error: {type(error).__name__}",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            is_error=True,
            error_message=str(error),
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """当工具发生错误时触发"""
        if not self._participant_stack:
            return
        target = self._participant_stack.pop()
        source = self._get_current_source()
        event = FlowEvent(
            source=target,
            target=source,
            action="Error",
            message=f"Tool Error: {type(error).__name__}",
            trace_id=LogContext.get("trace_id", str(uuid.uuid4())),
            is_error=True,
            error_message=str(error),
            is_return=True,
        )
        self.logger.info(
            f"{target} -> {source}: {event.action}", extra={"flow_event": event}
        )
```
