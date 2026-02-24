import pytest
import asyncio
from mermaid_trace.core.context import LogContext


def test_context_set_get() -> None:
    LogContext.set("key1", "value1")
    assert LogContext.get("key1") == "value1"
    assert LogContext.get("missing") is None
    assert LogContext.get("missing", "default") == "default"


def test_context_update() -> None:
    LogContext.set("k1", "v1")
    LogContext.update({"k2": "v2", "k3": "v3"})
    assert LogContext.get("k1") == "v1"
    assert LogContext.get("k2") == "v2"
    assert LogContext.get("k3") == "v3"


def test_context_scope() -> None:
    LogContext.set("global", "g")

    with LogContext.scope({"local": "l", "global": "overridden"}):
        assert LogContext.get("local") == "l"
        assert LogContext.get("global") == "overridden"

    assert LogContext.get("local") is None
    assert LogContext.get("global") == "g"


@pytest.mark.asyncio
async def test_context_ascope() -> None:
    LogContext.set("global", "g")

    async with LogContext.ascope({"local": "async_l"}):
        assert LogContext.get("local") == "async_l"
        await asyncio.sleep(0.01)
        assert LogContext.get("global") == "g"

    assert LogContext.get("local") is None


def test_trace_id_generation() -> None:
    # Ensure fresh context
    token = LogContext.set_all({})

    tid1 = LogContext.current_trace_id()
    assert tid1 is not None
    assert isinstance(tid1, str)
    assert len(tid1) > 0

    # Should persist in same context
    assert LogContext.current_trace_id() == tid1

    LogContext.reset(token)


def test_participant_helpers() -> None:
    assert LogContext.current_participant() == "Unknown"
    LogContext.set_participant("ServiceA")
    assert LogContext.current_participant() == "ServiceA"


def test_sampling_helpers() -> None:
    # Default is True
    assert LogContext.is_sampled() is True

    LogContext.set_sampled(False)
    assert LogContext.is_sampled() is False

    LogContext.set_sampled(True)
    assert LogContext.is_sampled() is True


def test_manual_trace_id() -> None:
    LogContext.set_trace_id("custom-id")
    assert LogContext.current_trace_id() == "custom-id"
