"""
LangChain Integration Module for MermaidTrace.

This module provides a LangChain Callback Handler that allows you to automatically
generate Mermaid sequence diagrams for your LangChain chains, LLM calls, and tool usage.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
else:
    try:
        from langchain_core.callbacks import BaseCallbackHandler
        from langchain_core.outputs import LLMResult
    except ImportError:
        BaseCallbackHandler = object
        LLMResult = Any


class MermaidTraceCallbackHandler(BaseCallbackHandler):
    """
    LangChain Callback Handler that records execution flow as Mermaid sequence diagrams.

    This handler intercepts LangChain events (Chain, LLM, Tool) and logs them as
    FlowEvents, which are then processed by MermaidTrace to generate diagrams.
    """

    def __init__(self, host_name: str = "LangChain"):
        """
        Initialize the callback handler.

        Args:
            host_name (str): The name of the host participant in the diagram.
                             Defaults to "LangChain".
        """
        if BaseCallbackHandler is object:
            raise ImportError(
                "langchain-core is required to use MermaidTraceCallbackHandler. "
                "Install it with `pip install langchain-core`."
            )
        self.host_name = host_name
        self.logger = get_flow_logger()
        self._participant_stack: List[str] = []

    def _get_current_source(self) -> str:
        if self._participant_stack:
            return self._participant_stack[-1]
        return str(LogContext.get("current_participant", self.host_name))

    def on_chain_start(
        self,
        serialized: Optional[Dict[str, Any]],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""
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
        """Run when chain ends running."""
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
        """Run when LLM starts running."""
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
        """Run when Chat Model starts running."""
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
        """Run when LLM ends running."""
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
        """Run when LLM errors."""
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
        """Run when Retriever starts running."""
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

    def on_retriever_end(self, documents: List[Any], **kwargs: Any) -> Any:  # type: ignore[override]
        """Run when Retriever ends running."""
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
        """Run when tool starts running."""
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
        """Run when tool ends running."""
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
        """Run when chain errors."""
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
        """Run when tool errors."""
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
