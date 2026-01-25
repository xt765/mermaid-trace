import logging
from mermaid_trace.core.formatter import MermaidFormatter
from mermaid_trace.core.events import FlowEvent

def test_formatter_basic() -> None:
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="Client", target="Server", action="GET", message="GET /", trace_id="1"
    )
    # Mock LogRecord
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    line = formatter.format(record)
    assert line == "Client->>Server: GET /"

def test_formatter_sanitize() -> None:
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="My Client", target="My.Server-1", action="Call", message="Msg", trace_id="1"
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    line = formatter.format(record)
    # Spaces -> _, Dots -> _, Hyphens -> _ (via regex \W -> _)
    assert "My_Client->>My_Server_1" in line

def test_formatter_return() -> None:
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="Server", target="Client", action="GET", message="Return", 
        trace_id="1", is_return=True, result="200 OK"
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    line = formatter.format(record)
    assert line == "Server-->>Client: Return: 200 OK"

def test_formatter_error() -> None:
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="Server", target="Client", action="GET", message="Err", 
        trace_id="1", is_error=True, error_message="ValueError"
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    line = formatter.format(record)
    assert line == "Server--xClient: Error: ValueError"

def test_formatter_escape() -> None:
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="A", target="B", action="Call", message="Line1\nLine2", trace_id="1"
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    line = formatter.format(record)
    assert "Line1<br/>Line2" in line
