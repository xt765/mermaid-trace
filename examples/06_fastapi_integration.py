"""
FastAPI Integration.
Demonstrates:
1. Using MermaidTraceMiddleware for automatic HTTP request tracing
2. Full stack trace capture for Web errors
3. Cross-service Trace ID propagation (via headers)

To run this example, install fastapi and uvicorn:
pip install fastapi uvicorn
"""

from fastapi import FastAPI
from mermaid_trace import trace, configure_flow
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware
import uvicorn
from typing import Dict, Any

# 1. Setup tracing
configure_flow("mermaid_diagrams/examples/fastapi_trace.mmd")

app = FastAPI()

# 2. Add Middleware
# This will automatically trace all incoming requests
app.add_middleware(MermaidTraceMiddleware, app_name="MyFastAPI")


@trace(target="LogicLayer")
def calculate_something(x: int) -> int:
    if x < 0:
        raise ValueError("Negative input not allowed")
    return x * 100


@app.get("/compute/{val}")
async def compute(val: int) -> Dict[str, Any]:
    # This internal call will correctly show MyFastAPI -> LogicLayer in the diagram
    result = calculate_something(val)
    return {"result": result}


if __name__ == "__main__":
    print("Starting FastAPI server on http://127.0.0.1:8001")
    print("Try visiting: http://127.0.0.1:8001/compute/5")
    print("Then visit: http://127.0.0.1:8001/compute/-1 to see error capture")
    uvicorn.run(app, host="127.0.0.1", port=8001)
