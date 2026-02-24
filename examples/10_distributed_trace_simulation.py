"""
Distributed Tracing Simulation.
Demonstrates:
1. Simulating a microservices architecture (Service A calling Service B).
2. Propagating the Trace ID across service boundaries (e.g., via HTTP headers).
3. Linking distributed logs into a single coherent Mermaid diagram.
"""

import time
import uuid
from typing import Dict, Any
from mermaid_trace import trace, configure_flow
from mermaid_trace.core.context import LogContext

# Setup tracing to a single file to see the full picture
configure_flow("mermaid_diagrams/examples/distributed_trace.mmd")


# --- Simulated Network Layer ---


class NetworkClient:
    """
    Simulates an HTTP client that automatically injects the current Trace ID header.
    """

    @trace(source="ServiceA", target="Network", action="HTTP POST")
    def post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Get current trace ID
        current_trace_id = LogContext.current_trace_id()

        # 2. Inject into headers (simulation)
        headers = {"X-Trace-ID": current_trace_id}
        print(f"[Network] Sending request to {url} with Trace ID: {current_trace_id}")

        # 3. Simulate network call to Service B
        if url == "http://service-b/api/process":
            return service_b_entrypoint(headers, data)
        return {"error": "404 Not Found"}


# --- Service B (The Called Service) ---


@trace(source="Network", target="ServiceB", action="Handle Request")
def service_b_entrypoint(
    headers: Dict[str, str], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulates the entry point (e.g., FastAPI middleware) of Service B.
    It extracts the Trace ID and restores the context.
    """
    # 1. Extract Trace ID from headers
    incoming_trace_id = headers.get("X-Trace-ID")

    if incoming_trace_id:
        # 2. RESTORE CONTEXT: Important!
        # This links Service B's actions to the original trace started in Service A.
        LogContext.set_trace_id(incoming_trace_id)
        print(f"[ServiceB] Resumed context with Trace ID: {incoming_trace_id}")
    else:
        # Fallback: Start a new trace if no ID provided
        new_id = str(uuid.uuid4())
        LogContext.set_trace_id(new_id)
        print(f"[ServiceB] No Trace ID found, started new: {new_id}")

    # 3. Call internal business logic
    return process_data(payload)


@trace(target="ServiceB.Logic")
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    time.sleep(0.1)
    return {"status": "processed", "result": f"Processed {data['item']}"}


# --- Service A (The Caller Service) ---


@trace(source="Client", target="ServiceA", action="Start Job")
def run_job() -> None:
    client = NetworkClient()

    print("[ServiceA] Starting job...")
    item = {"item": "Order-123", "amount": 99.9}

    # This call will propagate the trace ID internally via our simulated client
    response = client.post("http://service-b/api/process", item)

    print(f"[ServiceA] Got response: {response}")


if __name__ == "__main__":
    print("Simulating distributed tracing between Service A and Service B...")
    run_job()
    print("\nCheck 'mermaid_diagrams/examples/distributed_trace.mmd'.")
    print("You should see a continuous flow from Client -> ServiceA -> ServiceB.")
