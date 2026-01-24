import pytest
from unittest.mock import MagicMock
from logcapy.integrations.django import LogCapyMiddleware
from logcapy.core.context import LogContext

from unittest.mock import MagicMock, ANY

def test_django_middleware_success(caplog):
    get_response = MagicMock()
    get_response.return_value = {"status": 200}
    # Mock HttpResponse behavior as a dict for simplicity or better mock
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.__setitem__ = MagicMock()
    get_response.return_value = response_mock
    
    middleware = LogCapyMiddleware(get_response)
    
    request = MagicMock()
    request.META = {"HTTP_USER_AGENT": "test-agent"}
    request.method = "GET"
    request.path = "/"
    request.headers = {}
    
    response = middleware(request)
    
    assert response == response_mock
    response_mock.__setitem__.assert_called_with("X-Request-ID", ANY)
    
    assert "GET /" in caplog.text
    assert LogContext.get("user_agent") == "test-agent"

def test_django_middleware_error(caplog):
    get_response = MagicMock()
    get_response.side_effect = ValueError("Django Boom")
    
    middleware = LogCapyMiddleware(get_response)
    
    request = MagicMock()
    request.META = {}
    request.method = "GET"
    request.path = "/error"
    request.headers = {}
    
    with pytest.raises(ValueError):
        middleware(request)
        
    assert "Django Boom" in caplog.text
    assert "Unhandled exception" in caplog.text
