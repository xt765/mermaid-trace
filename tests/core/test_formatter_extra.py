import logging
from mermaid_trace.core.formatter import MermaidFormatter
from mermaid_trace.core.events import Event, FlowEvent


class NonFlowEvent(Event):
    """Test implementation of Event abstract class"""

    def __init__(self, source: str, target: str, message: str):
        self.source = source
        self.target = target
        self.message = message
        self.timestamp = 1234567890.0
        self.trace_id = "test-trace-id"
        self.action = "test-action"

    def get_source(self) -> str:
        return self.source

    def get_target(self) -> str:
        return self.target

    def get_action(self) -> str:
        return self.action

    def get_message(self) -> str:
        return self.message

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_trace_id(self) -> str:
        return self.trace_id


def test_base_formatter_format_fallback():
    """Test that BaseFormatter.format falls back to parent method when no flow_event"""
    # This test covers line 59: fallback for standard logs
    formatter = MermaidFormatter()

    # Create a standard log record without flow_event
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    result = formatter.format(record)
    # Should return standard log format when no flow_event
    assert "Test message" in result


def test_mermaid_formatter_non_flow_event():
    """Test that MermaidFormatter handles non-FlowEvent types"""
    # This test covers line 86: fallback for non-FlowEvent types
    formatter = MermaidFormatter()

    # Create a simple Event implementation
    event = NonFlowEvent("Source", "Target", "Test message")

    result = formatter.format_event(event)
    # Should use the fallback format for non-FlowEvent
    assert result == "Source->>Target: Test message"


def test_mermaid_formatter_sanitize_digit_start():
    """Test that sanitize adds underscore to names starting with digits"""
    # This test covers line 135: handling names starting with digits
    formatter = MermaidFormatter()

    # Create a FlowEvent with source starting with a digit
    event = FlowEvent(
        source="123Service",
        target="Client",
        action="Test",
        message="Test message",
        trace_id="test-trace-id",
    )

    result = formatter.format_event(event)
    # Source should be sanitized to _123Service
    assert "_123Service" in result
    assert "->>" in result
    assert "Client" in result


def test_mermaid_formatter_sanitize_special_chars():
    """Test that sanitize removes special characters"""
    formatter = MermaidFormatter()

    event = FlowEvent(
        source="Source@Service",
        target="Client#123",
        action="Test",
        message="Test message",
        trace_id="test-trace-id",
    )

    result = formatter.format_event(event)
    # Special characters should be replaced with underscores
    assert "Source_Service" in result
    assert "Client_123" in result


def test_mermaid_formatter_error_event():
    """Test formatting of error events"""
    formatter = MermaidFormatter()

    event = FlowEvent(
        source="Client",
        target="Service",
        action="ErrorTest",
        message="Error occurred",
        trace_id="test-trace-id",
        is_return=True,
        is_error=True,
        error_message="Division by zero",
    )

    result = formatter.format_event(event)
    # Error events should include error information
    assert "Division by zero" in result
    assert "Error:" in result
    assert "--x" in result  # Error arrow
    assert "Service" in result
    assert "Client" in result
