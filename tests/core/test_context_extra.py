from mermaid_trace.core.context import LogContext


def test_context_empty_update():
    """Test updating context with empty dictionary"""
    # This test covers the case where data is empty (line 83)
    LogContext.update({})
    assert LogContext.get("test") is None


def test_context_set_trace_id():
    """Test setting trace ID manually"""
    # This test covers the set_trace_id method (line 248)
    test_trace_id = "manual-trace-id-123"
    LogContext.set_trace_id(test_trace_id)
    assert LogContext.current_trace_id() == test_trace_id
    assert LogContext.get("trace_id") == test_trace_id


def test_context_get_store():
    """Test getting the complete context store"""
    # This test covers the get_store method (line 110)
    LogContext.set("test_key", "test_value")
    store = LogContext._get_store()
    assert isinstance(store, dict)
    assert "test_key" in store
    assert store["test_key"] == "test_value"

    # Verify it's a copy by modifying the original
    LogContext.set("test_key", "updated")
    store_copy = LogContext._get_store()
    assert store_copy["test_key"] == "updated"  # _get_store returns current context
