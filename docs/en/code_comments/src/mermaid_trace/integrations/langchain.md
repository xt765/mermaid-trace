# File: src/mermaid_trace/integrations/langchain.py

## Overview
The `langchain.py` module provides a Callback Handler for integrating MermaidTrace into the LangChain framework. It allows developers to automatically visualize the execution flow of Large Language Model (LLM) chains, Agent tool calls, and Retrieval-Augmented Generation (RAG) processes as Mermaid sequence diagrams.

## Core Functionality Analysis

### 1. Automatic Flow Tracing
`MermaidTraceCallbackHandler` implements LangChain's `BaseCallbackHandler` interface, capturing the following key events:
- **Chain Start & End**: Records the hierarchy of chain calls.
- **LLM/ChatModel Start & End**: Records model requests and generated responses.
- **Retriever Start & End**: Records knowledge retrieval actions in RAG flows.
- **Tool Start & End**: Records external tool calls by Agents.

### 2. Participant Stack Management
To accurately draw "return arrows" (`-->>`) in the sequence diagram, the handler maintains an internal participant stack.
- **Nesting Support**: When a Chain calls an LLM, the stack ensures the LLM's return arrow points back to the correct Chain.
- **Automatic Inference**: Combined with `LogContext`, it automatically identifies the caller (Source) and the target (Target).

### 3. RAG Scenario Optimization
For RAG flows, it specifically handles retriever inputs and outputs:
- **Retrieval Content Display**: Summarizes the number of retrieved documents or content snippets in the diagram's messages.

### 4. Conditional Dependency Handling
Similar to the FastAPI integration, this module uses conditional imports. Even if `langchain-core` is not installed, other parts of the project can still be loaded normally. Dependency checks are performed only when the LangChain integration is actually instantiated.

## Source Code with Comments

```python
"""
LangChain Integration Module for MermaidTrace.

This module provides a callback handler to capture and visualize LangChain execution flows.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from ..core.events import FlowEvent
from ..core.context import LogContext
from ..core.decorators import get_flow_logger

# ----------------------------------------------------------------------
# Conditional Imports: Support optional LangChain dependency
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
    LangChain Callback Handler: Converts execution steps into sequence diagrams.
    """

    def __init__(self, host_name: str = "LangChainApp"):
        """
        Initialize the handler.

        Args:
            host_name: The name of the host application in the diagram (e.g., "MyAI").
        """
        self.host_name = host_name
        self.logger = get_flow_logger()
        # Participant stack to track nested calls
        self._participant_stack: List[str] = []

    def _get_current_source(self) -> str:
        """Get the current caller (source)"""
        if self._participant_stack:
            return self._participant_stack[-1]
        return str(LogContext.get("current_participant", self.host_name))

    def on_chain_start(
        self, serialized: Optional[Dict[str, Any]], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Triggered when a Chain starts"""
        target = (serialized.get("name") if serialized else None) or kwargs.get("name") or "Chain"
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
        """Triggered when a Chain ends"""
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
        """Triggered when LLM starts generating"""
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
        """Triggered when Chat Model starts"""
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
        """Triggered when LLM ends generating"""
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
        """Triggered when LLM errors"""
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
        """Triggered when Retriever starts"""
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
        """Triggered when a Retriever ends"""
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
        """Triggered when a Tool starts"""
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
        """Triggered when a Tool ends"""
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
        """Triggered when a Chain errors"""
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
        """Triggered when a Tool errors"""
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

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """Triggered when a Tool ends"""
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
        self.logger.info(event)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Triggered when a Chain errors"""
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
        self.logger.info(event)

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        """Triggered when a Tool errors"""
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
        self.logger.info(event)
```
