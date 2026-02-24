"""
FastAPI Integration.
Demonstrates:
1. Using MermaidTraceMiddleware for automatic HTTP request tracing
2. Full stack trace capture for Web errors
3. Cross-service Trace ID propagation (via headers)
4. Data Masking (sensitive fields like 'token')
5. Sampling (probability based tracing)

To run this example, install fastapi and uvicorn:
pip install fastapi uvicorn
"""

from fastapi import FastAPI, Header
from mermaid_trace import trace, configure_flow
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware
from mermaid_trace.core.config import config
import uvicorn
from typing import Dict, Any, Optional

# 1. Setup tracing
configure_flow("mermaid_diagrams/examples/fastapi_trace.mmd")

# 2. Configure global settings
# Mask sensitive fields automatically
config.mask_patterns = ["password", "token", "secret", "auth"]
# Set sampling rate (e.g. 1.0 for demo, but can be lower)
config.sample_rate = 1.0

app = FastAPI()

# 3. Add Middleware
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


@app.post("/login")
async def login(
    username: str, password: str, token: Optional[str] = None
) -> Dict[str, str]:
    # Demonstrate masking: 'password' and 'token' query params will be masked in logs
    return {"status": "ok", "token": "secret_token_123"}


@app.get("/distributed")
async def distributed_trace(
    x_trace_id: Optional[str] = Header(None),
) -> Dict[str, Optional[str]]:
    # Demonstrate trace propagation.
    # If you call this with header 'X-Trace-ID: 123', the log will use that ID.
    from mermaid_trace.core.context import LogContext

    current_tid = LogContext.current_trace_id()
    # Explicitly cast to Optional[str] to satisfy type checker, though dict handles it
    return {"received_trace_id": x_trace_id, "active_trace_id": current_tid}


if __name__ == "__main__":
    print("Starting FastAPI server on http://127.0.0.1:8001")
    print("Try visiting: http://127.0.0.1:8001/compute/5")
    print("Try visiting: http://127.0.0.1:8001/compute/-1 to see error capture")
    print("Try posting to /login?username=admin&password=123&token=abc to see masking")
    print("Try: curl -H 'X-Trace-ID: my-trace-1' http://127.0.0.1:8001/distributed")
    uvicorn.run(app, host="127.0.0.1", port=8001)
