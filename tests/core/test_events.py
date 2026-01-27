from mermaid_trace.core.events import FlowEvent


class TestEvent:
    """Test cases for the Event abstract base class."""

    def test_flowevent_implements_interface(self):
        """Test that FlowEvent has all attributes from Event interface."""
        event = FlowEvent(
            source="source",
            target="target",
            action="action",
            message="message",
            trace_id="trace_id",
        )

        # Test all attributes are present
        assert event.source == "source"
        assert event.target == "target"
        assert event.action == "action"
        assert event.message == "message"
        assert isinstance(event.timestamp, float)
        assert event.trace_id == "trace_id"

    def test_flowevent_default_values(self):
        """Test that FlowEvent uses correct default values."""
        event = FlowEvent(
            source="source",
            target="target",
            action="action",
            message="message",
            trace_id="trace_id",
        )

        assert event.is_return is False
        assert event.is_error is False
        assert event.error_message is None
        assert event.params is None
        assert event.result is None

    def test_flowevent_with_all_fields(self):
        """Test that FlowEvent works with all fields populated."""
        event = FlowEvent(
            source="source",
            target="target",
            action="action",
            message="message",
            trace_id="trace_id",
            is_return=True,
            is_error=True,
            error_message="error message",
            params="params",
            result="result",
        )

        assert event.is_return is True
        assert event.is_error is True
        assert event.error_message == "error message"
        assert event.params == "params"
        assert event.result == "result"
