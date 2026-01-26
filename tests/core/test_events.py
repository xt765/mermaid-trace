import pytest
from mermaid_trace.core.events import Event, FlowEvent


class TestEvent:
    """Test cases for the Event abstract base class."""

    def test_event_is_abstract(self):
        """Test that Event is an abstract base class."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            Event()  # type: ignore[abstract]

    def test_flowevent_inherits_event(self):
        """Test that FlowEvent inherits from Event."""
        assert issubclass(FlowEvent, Event)

    def test_flowevent_implements_all_abstract_methods(self):
        """Test that FlowEvent implements all abstract methods from Event."""
        event = FlowEvent(
            source="source",
            target="target",
            action="action",
            message="message",
            trace_id="trace_id",
        )

        # Test all abstract methods are implemented
        assert event.get_source() == "source"
        assert event.get_target() == "target"
        assert event.get_action() == "action"
        assert event.get_message() == "message"
        assert isinstance(event.get_timestamp(), float)
        assert event.get_trace_id() == "trace_id"

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
