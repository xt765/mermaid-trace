"""
LangChain Integration Example for MermaidTrace.

This example demonstrates how to use `MermaidTraceCallbackHandler` to visualize
the execution flow of a LangChain application.
"""

import sys
import os

# Add src to path if running from examples folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from typing import Any, cast
from mermaid_trace.integrations import MermaidTraceCallbackHandler
from mermaid_trace.handlers.mermaid_handler import MermaidFileHandler
import logging

# 1. Setup MermaidTrace logging
logging.basicConfig(level=logging.INFO)
flow_logger = logging.getLogger("mermaid_trace.flow")
flow_logger.addHandler(
    MermaidFileHandler("mermaid_diagrams/examples/langchain_trace.mmd")
)


def demo_with_mock_langchain() -> None:
    """
    Mock behavior of a LangChain chain calling the handler.
    Used when langchain is not installed.
    """
    print("🚀 Starting LangChain Mock Trace (No langchain installed)...")

    # Initialize the handler
    handler = MermaidTraceCallbackHandler(host_name="MyApp")

    # 1. RAG Scenario: Retrieve documents
    print("--- RAG Retrieval ---")
    handler.on_retriever_start(
        serialized={"name": "VectorStoreRetriever"}, query="What is MermaidTrace?"
    )
    handler.on_retriever_end(
        documents=cast(Any, [{"page_content": "MermaidTrace is a tool..."}] * 2)
    )

    # 2. Chain execution
    print("--- Chain Start ---")
    handler.on_chain_start(
        serialized={"name": "RAG_Chain"}, inputs={"question": "What is MermaidTrace?"}
    )

    # 3. ChatModel Call
    print("--- ChatModel Call ---")
    handler.on_chat_model_start(
        serialized={"name": "GPT-4o"},
        messages=[[{"content": "Answer based on context..."}]],
    )

    # Simulate Response
    class MockLLMResult:
        def __init__(self) -> None:
            self.generations = [[{"text": "MermaidTrace is a visualization tool."}]]

    handler.on_llm_end(response=cast(Any, MockLLMResult()))

    # 4. Chain Ends
    print("--- Chain End ---")
    handler.on_chain_end(outputs={"answer": "MermaidTrace is a visualization tool."})


def demo_with_real_langchain() -> None:
    """
    Runs a real LangChain chain if dependencies are present.
    """
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
    except ImportError:
        print("❌ LangChain dependencies missing for real demo.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found. Skipping real API call.")
        print("   Run: set OPENAI_API_KEY=sk-... to try the real demo.")
        # Fallback to mock if no key
        demo_with_mock_langchain()
        return

    print("🚀 Starting REAL LangChain Trace...")

    # 1. Setup Chain
    handler = MermaidTraceCallbackHandler(host_name="LangChainApp")
    llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo")
    prompt = ChatPromptTemplate.from_template("Tell me a short joke about {topic}")
    chain = prompt | llm | StrOutputParser()

    # 2. Invoke with Handler
    print("Invoking chain...")
    result = chain.invoke({"topic": "debugging"}, config={"callbacks": [handler]})
    print(f"Result: {result}")


if __name__ == "__main__":
    # Check for LangChain availability
    try:
        import langchain_core  # noqa: F401
        import langchain_openai  # noqa: F401

        HAS_LANGCHAIN = True
    except ImportError:
        HAS_LANGCHAIN = False

    if HAS_LANGCHAIN:
        demo_with_real_langchain()
    else:
        demo_with_mock_langchain()
        print(
            "\n💡 TIP: Install 'langchain-openai' and set OPENAI_API_KEY to run the real demo!"
        )

    print(
        "\n✅ Done! Check 'mermaid_diagrams/examples/langchain_trace.mmd' for the result."
    )
