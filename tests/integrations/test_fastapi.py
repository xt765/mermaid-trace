import pytest
from logcapy.integrations.fastapi import LogCapyMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import httpx

# Define app
def homepage(request):
    return JSONResponse({"hello": "world"})

def error_page(request):
    raise ValueError("Boom")

app = Starlette(routes=[
    Route("/", homepage),
    Route("/error", error_page),
])
app.add_middleware(LogCapyMiddleware)

@pytest.fixture
async def client():
    # Use AsyncClient for robust ASGI testing
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_fastapi_middleware_success(client, caplog):
    response = await client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Check logs
    assert "GET /" in caplog.text

@pytest.mark.asyncio
async def test_fastapi_middleware_error(client, caplog):
    with pytest.raises(ValueError):
        await client.get("/error")
        
    assert "Boom" in caplog.text
    assert "Unhandled exception" in caplog.text
