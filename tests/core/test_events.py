from mermaid_trace.core.events import FlowEvent
import time

def test_flow_event_defaults() -> None:
    event = FlowEvent(
        source="A", target="B", action="Call", message="Msg", trace_id="123"
    )
    assert event.source == "A"
    assert event.target == "B"
    assert event.is_return is False
    assert event.is_error is False
    assert isinstance(event.timestamp, float)
    assert event.timestamp <= time.time()

def test_flow_event_error() -> None:
    event = FlowEvent(
        source="A", target="B", action="Call", message="Error", trace_id="123",
        is_error=True, error_message="Something went wrong"
    )
    assert event.is_error is True
    assert event.error_message == "Something went wrong"
