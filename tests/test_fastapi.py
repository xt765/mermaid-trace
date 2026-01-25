import pytest
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware

@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(MermaidTraceMiddleware, app_name="TestApp")
    
    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"message": "ok"}
        
    return app

@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)

def test_fastapi_middleware_logs(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Test that the middleware correctly logs request and response events.
    """
    caplog.set_level(logging.INFO)
    
    response = client.get("/test")
    assert response.status_code == 200
    
    # Filter logs that have flow_event attached
    mermaid_logs = [r for r in caplog.records if getattr(r, 'flow_event', None)]
    
    assert len(mermaid_logs) >= 2, "Should have at least Request and Response logs"
    
    # Check Request Log
    req_log = mermaid_logs[0]
    # Use getattr to avoid mypy errors since flow_event is dynamically added
    req_event = getattr(req_log, 'flow_event')
    assert req_event.source == "Client"
    assert req_event.target == "TestApp"
    assert "GET /test" in req_event.action
    
    # Check Response Log
    resp_log = mermaid_logs[1]
    resp_event = getattr(resp_log, 'flow_event')
    assert resp_event.source == "TestApp"
    assert resp_event.target == "Client"
    assert resp_event.is_return is True
    assert "200" in resp_event.result
