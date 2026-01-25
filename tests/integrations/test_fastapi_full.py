import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware
from mermaid_trace.core.context import LogContext
from unittest.mock import patch, MagicMock

app = FastAPI()
app.add_middleware(MermaidTraceMiddleware, app_name="TestAPI")

@app.get("/ok")
async def ok_endpoint():
    # Verify context is set
    assert LogContext.current_participant() == "TestAPI"
    assert LogContext.current_trace_id() is not None
    return {"status": "ok"}

@app.get("/error")
async def error_endpoint():
    raise ValueError("Test Error")

client = TestClient(app)

def test_fastapi_ok(caplog):
    resp = client.get("/ok", headers={"X-Source": "TestClient"})
    assert resp.status_code == 200
    
    # Check logs
    records = [r for r in caplog.records if hasattr(r, 'flow_event')]
    assert len(records) >= 2
    
    req = records[0].flow_event
    assert req.source == "TestClient"
    assert req.target == "TestAPI"
    assert "GET /ok" in req.action
    
    resp_evt = records[1].flow_event
    assert resp_evt.is_return is True
    assert "200" in resp_evt.result

def test_fastapi_trace_id_propagation(caplog):
    tid = "custom-trace-id-123"
    client.get("/ok", headers={"X-Trace-ID": tid})
    
    records = [r for r in caplog.records if hasattr(r, 'flow_event')]
    assert records[0].flow_event.trace_id == tid

def test_fastapi_error(caplog):
    with pytest.raises(ValueError):
        client.get("/error")
        
    records = [r for r in caplog.records if hasattr(r, 'flow_event')]
    err_evt = records[1].flow_event
    assert err_evt.is_error is True
    assert "Test Error" in err_evt.error_message

def test_fastapi_missing_dependency():
    # Simulate BaseHTTPMiddleware not being available (e.g. starlette not installed)
    # We need to reload the module or patch the class before init
    with patch("mermaid_trace.integrations.fastapi.BaseHTTPMiddleware", object):
        with pytest.raises(ImportError, match="FastAPI/Starlette is required"):
            MermaidTraceMiddleware(MagicMock())
