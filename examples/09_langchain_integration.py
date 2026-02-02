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
    Since we don't want to require langchain-core to run this example,
    we mock the behavior of a LangChain chain calling the handler.
    """
    print("🚀 Starting LangChain Mock Trace...")

    # Initialize the handler
    handler = MermaidTraceCallbackHandler(host_name="MyApp")

    # 1. RAG Scenario: Retrieve documents
    print("--- RAG Retrieval ---")
    handler.on_retriever_start(
        serialized={"name": "VectorStoreRetriever"}, query="What is MermaidTrace?"
    )
    handler.on_retriever_end(
        documents=[{"page_content": "MermaidTrace is a tool..."}] * 2
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

    print(
        "\n✅ Done! Check 'mermaid_diagrams/examples/langchain_trace.mmd' for the result."
    )


if __name__ == "__main__":
    demo_with_mock_langchain()

    # Instructions for real LangChain usage:
    """
    # To use with real LangChain:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    handler = MermaidTraceCallbackHandler()
    llm = ChatOpenAI()
    prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
    chain = prompt | llm
    
    # Just pass the handler to the invoke method
    chain.invoke({"topic": "bears"}, config={"callbacks": [handler]})
    """
