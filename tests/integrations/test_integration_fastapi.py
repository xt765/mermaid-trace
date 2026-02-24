import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware
from mermaid_trace import trace
from typing import Any, Optional

# Define app outside to ensure clean state
app = FastAPI()
app.add_middleware(MermaidTraceMiddleware, app_name="TestAPI")


@app.get("/sync-ok")
def sync_endpoint() -> dict[str, str]:
    # Test sync endpoint support
    return {"mode": "sync"}


@app.get("/async-ok")
async def async_endpoint() -> dict[str, str]:
    return {"mode": "async"}


@app.post("/items/{item_id}")
async def create_item(item_id: int, q: Optional[str] = None) -> dict[str, Any]:
    return {"item_id": item_id, "q": q}


@app.get("/nested")
async def nested_call() -> str:
    return await service_call()


@trace(target="Service", action="DoWork")
async def service_call() -> str:
    return "done"


client = TestClient(app)


def test_sync_endpoint(caplog: Any) -> None:
    caplog.clear()
    resp = client.get("/sync-ok", headers={"X-Source": "SyncClient"})
    assert resp.status_code == 200

    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert len(records) >= 2
    assert records[0].flow_event.action == "GET /sync-ok"
    assert records[0].flow_event.source == "SyncClient"


def test_async_endpoint(caplog: Any) -> None:
    caplog.clear()
    resp = client.get("/async-ok")
    assert resp.status_code == 200

    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert len(records) >= 2
    assert records[0].flow_event.action == "GET /async-ok"


def test_nested_tracing(caplog: Any) -> None:
    # Tests that middleware context propagates to inner @trace calls
    caplog.clear()
    resp = client.get("/nested")
    assert resp.status_code == 200

    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    # Expect:
    # 1. Client -> TestAPI (Middleware Request)
    # 2. TestAPI -> Service (Inner Call)
    # 3. Service -> TestAPI (Inner Return)
    # 4. TestAPI -> Client (Middleware Return)

    assert len(records) >= 4

    req_mid = records[0].flow_event
    req_inner = records[1].flow_event
    # resp_inner = records[2].flow_event  # Unused
    # resp_mid = records[3].flow_event    # Unused

    assert req_mid.target == "TestAPI"

    # Context propagation check: Source of inner call should be the App (TestAPI)
    assert req_inner.source == "TestAPI"
    assert req_inner.target == "Service"

    # Trace ID should be consistent
    assert req_mid.trace_id == req_inner.trace_id


def test_query_params_logging(caplog: Any) -> None:
    caplog.clear()
    client.post("/items/42?q=search")

    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    req = records[0].flow_event
    # Middleware captures query params in params field
    # Format is "query={'key': 'value'}"
    assert "'q': 'search'" in req.params


def test_trace_id_header(caplog: Any) -> None:
    # Test X-Trace-ID
    caplog.clear()
    tid = "custom-trace-1"
    client.get("/async-ok", headers={"X-Trace-ID": tid})
    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert records[0].flow_event.trace_id == tid

    # Test traceparent (W3C)
    caplog.clear()
    # version-traceid-parentid-flags
    w3c_tid = "4bf92f3577b34da6a3ce929d0e0e4736"
    traceparent = f"00-{w3c_tid}-00f067aa0ba902b7-01"
    client.get("/async-ok", headers={"traceparent": traceparent})
    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert records[0].flow_event.trace_id == w3c_tid

    # Test b3 single header
    caplog.clear()
    b3_tid = "80f198ee56343ba864fe8b2a57d3eff7"
    b3_header = f"{b3_tid}-e457b5a2e4d86bd1-1"
    client.get("/async-ok", headers={"b3": b3_header})
    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert records[0].flow_event.trace_id == b3_tid

    # Test b3 separate headers
    caplog.clear()
    b3_tid_sep = "a0f198ee56343ba864fe8b2a57d3eff8"
    client.get("/async-ok", headers={"X-B3-TraceId": b3_tid_sep})
    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    assert records[0].flow_event.trace_id == b3_tid_sep


def test_fastapi_error(caplog: Any) -> None:
    caplog.clear()

    @app.get("/error")
    def error_endpoint() -> None:
        raise ValueError("Test Error")

    with pytest.raises(ValueError):
        client.get("/error")

    records = [r for r in caplog.records if hasattr(r, "flow_event")]
    # 0: Request, 1: Error
    assert len(records) >= 2
    assert records[1].flow_event.is_error is True
    assert "Test Error" in records[1].flow_event.error_message


def test_fastapi_file_output(diagram_output_dir: Any) -> None:
    # Integration test for file output with Middleware
    log_file = diagram_output_dir / "api_flow.mmd"
    from mermaid_trace import configure_flow

    logger = configure_flow(str(log_file))

    # Re-create app or just use client (which uses global logger)
    # The middleware gets logger via get_flow_logger(), which returns the configured logger.

    try:
        client.get("/sync-ok", headers={"X-Source": "SyncClient"})

        for h in logger.handlers:
            h.flush()

        # Check file
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "SyncClient->>TestAPI: GET /sync-ok" in content
        assert "TestAPI-->>SyncClient: Return" in content
    finally:
        for h in logger.handlers:
            h.flush()
            h.close()
