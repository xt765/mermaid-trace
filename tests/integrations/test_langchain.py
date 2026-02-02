import pytest
from unittest.mock import MagicMock, patch
from mermaid_trace.integrations.langchain import MermaidTraceCallbackHandler
from mermaid_trace.core.events import FlowEvent


def test_callback_handler_init():
    """Test that handler initializes correctly and checks for dependency."""
    # Test successful init when BaseCallbackHandler is NOT object (i.e. langchain-core is installed)
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler(host_name="TestHost")
        assert handler.host_name == "TestHost"
        assert handler.logger.name == "mermaid_trace.flow"


def test_callback_handler_import_error():
    """Test that handler raises ImportError if langchain-core is missing."""
    with patch("mermaid_trace.integrations.langchain.BaseCallbackHandler", new=object):
        with pytest.raises(ImportError, match="langchain-core is required"):
            MermaidTraceCallbackHandler()


def test_on_chain_events():
    """Test chain start and end events."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        # Chain Start
        handler.on_chain_start({"name": "MyChain"}, {"input": "val"})
        assert len(handler._participant_stack) == 1
        assert handler._participant_stack[0] == "MyChain"

        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert isinstance(event, FlowEvent)
        assert event.source == "LangChain"
        assert event.target == "MyChain"
        assert "Start Chain" in event.message

        # Chain End
        handler.on_chain_end({"output": "res"})
        assert len(handler._participant_stack) == 0

        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.source == "MyChain"
        assert event.target == "LangChain"
        assert event.is_return is True


def test_on_llm_events():
    """Test LLM start and end events."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        # LLM Start
        handler.on_llm_start({}, ["prompt"])
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.target == "LLM"

        # LLM End
        mock_res = MagicMock()
        mock_res.generations = [[]]
        handler.on_llm_end(mock_res)
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.source == "LLM"
        assert event.is_return is True


def test_on_tool_events():
    """Test tool start and end events."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        # Tool Start
        handler.on_tool_start({"name": "SearchTool"}, "query")
        assert handler._participant_stack[-1] == "SearchTool"

        # Tool End
        handler.on_tool_end("result")
        assert len(handler._participant_stack) == 0


def test_error_handling():
    """Test error callbacks."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        # Chain Error
        handler._participant_stack = ["FaultyChain"]
        handler.on_chain_error(ValueError("bad value"))
        assert len(handler._participant_stack) == 0

        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.is_error is True
        assert "ValueError" in event.message


def test_on_retriever_events():
    """Test retriever start and end events."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        # Retriever Start
        handler.on_retriever_start({"name": "MyRetriever"}, "search query")
        assert handler._participant_stack[-1] == "MyRetriever"
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.target == "MyRetriever"
        assert "search query" in event.message

        # Retriever End
        handler.on_retriever_end(
            [MagicMock(page_content="doc1"), MagicMock(page_content="doc2")]
        )
        assert len(handler._participant_stack) == 0
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.source == "MyRetriever"
        assert "Retrieved 2 docs" in event.message


def test_on_chat_model_start():
    """Test chat model start event."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        handler.on_chat_model_start({"name": "GPT-4"}, [[MagicMock(content="hello")]])
        assert handler._participant_stack[-1] == "GPT-4"
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.target == "GPT-4"


def test_llm_error():
    """Test LLM error event."""
    with patch(
        "mermaid_trace.integrations.langchain.BaseCallbackHandler",
        new=type("BaseCallbackHandler", (), {}),
    ):
        handler = MermaidTraceCallbackHandler()
        handler.logger = MagicMock()

        handler._participant_stack = ["LLM"]
        handler.on_llm_error(RuntimeError("LLM failed"))
        assert len(handler._participant_stack) == 0
        event = handler.logger.info.call_args[1]["extra"]["flow_event"]
        assert event.is_error is True
        assert "RuntimeError" in event.message
