import logging
from mermaid_trace.core.formatter import MermaidFormatter
from mermaid_trace.core.events import FlowEvent


def test_formatter_collapsed_event():
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="A",
        target="B",
        action="Loop",
        message="Repeated",
        trace_id="1",
        collapsed=True,
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event

    formatter.format(record)
    line = formatter.flush()
    assert "note right of A: ( Sampled / Collapsed Interaction )" in line
    assert "A->>B: Repeated" in line


def test_formatter_error_with_stack_trace():
    formatter = MermaidFormatter()
    stack_trace = "Traceback (most recent call last):\n  File 'x.py', line 1, in <module>\n    error()"
    event = FlowEvent(
        source="A",
        target="B",
        action="Err",
        message="Oops",
        trace_id="1",
        is_error=True,
        error_message="Bang!",
        stack_trace=stack_trace,
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event

    formatter.format(record)
    line = formatter.flush()
    # Check for note syntax
    assert "note right of B:" in line
    # Check for partial stack trace content (escaped)
    assert "Traceback" in line
    assert "<br/>" in line  # Newlines should be escaped


def test_formatter_sanitize_empty():
    formatter = MermaidFormatter()
    # A name that becomes empty after sanitization (empty string)
    event = FlowEvent(
        source="", target="!!!", action="Call", message="Msg", trace_id="1"
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event

    formatter.format(record)
    line = formatter.flush()
    # Should fallback to "Unknown"
    assert "Unknown" in line


def test_formatter_header():
    formatter = MermaidFormatter()
    header = formatter.get_header("My Title")
    assert "sequenceDiagram" in header
    assert "title My Title" in header
    assert "autonumber" in header


def test_formatter_sanitize_collision():
    formatter = MermaidFormatter()
    # Force collision
    # "User" -> "User"

    # Same name should map to SAME ID
    id1 = formatter._sanitize("User")
    id2 = formatter._sanitize("User")
    assert id1 == id2 == "User"

    # Different name that sanitizes to same string
    # "User" vs "User@" (User@ -> User_) -> "User_" != "User" so no collision there.

    # We need a case where sanitization produces an existing ID.
    # 1. Register "User"
    # 2. Register "User" (same original name) -> returns "User"
    # 3. Register "User_1" (different original name, but maybe we can force conflict)

    # Let's try:
    # 1. "Service" -> "Service"
    # 2. "Service_1" -> "Service_1"
    # 3. "Service" (again) -> "Service"

    # To test collision logic:
    # 1. "Test" -> "Test"
    # 2. "Test" -> "Test" (cache hit)
    # 3. "Test_1" -> "Test_1"
    # 4. Now we need a name that sanitizes to "Test" but IS NOT "Test".
    # e.g. "Test@" -> "Test_" (not "Test")

    # How about this:
    # 1. "A" -> "A"
    # 2. "A_1" -> "A_1"
    # 3. Now we have "A" and "A_1" used.
    # 4. We introduce a name that sanitizes to "A".
    # e.g. if we have logic that strips something? No, it replaces with _.

    # Wait, the logic is:
    # clean_name = re.sub(..., "_", name)
    # if clean_name in used_ids: ...

    # So:
    # 1. "Foo" -> "Foo"
    # 2. "Foo" (again) -> returns "Foo" (cache)
    # 3. "Foo_1" -> "Foo_1" (if "Foo_1" passed in directly)

    # Now if we pass "Foo" again, it returns cached "Foo".

    # What if we pass a name that is NOT "Foo" but sanitizes to "Foo"?
    # e.g. "Foo." -> "Foo_"

    # Let's try to construct a collision.
    # 1. "Bar" -> "Bar"
    # 2. "Bar_1" -> "Bar_1" (We register this explicitly)
    # 3. Now we pass a name that sanitizes to "Bar".
    #    Since "Bar" is used, it should try "Bar_1".
    #    Since "Bar_1" is ALSO used, it should try "Bar_2".

    # But wait, if I pass "Bar" again, it uses the cached map.
    # I need a NEW name that sanitizes to "Bar".
    # But "Bar" contains only valid chars.

    # Ah, the sanitize function does NOT strip chars, it replaces with _.

    # Example:
    # 1. "A" -> "A"
    # 2. "A_1" -> "A_1"
    # 3. We need something that sanitizes to "A".
    #    Impossible if "A" is valid.

    # Example 2:
    # 1. "A.B" -> "A_B"
    # 2. "A_B" -> "A_B" (This would be a collision if "A.B" wasn't cached)

    # Let's do:
    # 1. Register "A_B" (explicitly)
    # 2. Register "A.B" (sanitizes to "A_B")
    # -> Should collide and become "A_B_1"

    id1 = formatter._sanitize("A_B")
    assert id1 == "A_B"

    id2 = formatter._sanitize("A.B")
    assert id2 == "A_B_1"

    # Further collision
    # Register "A_B_2" explicitly
    formatter._sanitize("A_B_2")

    # Now "A-B" -> sanitizes to "A_B"
    # "A_B" used? Yes.
    # "A_B_1" used? Yes (from A.B).
    # "A_B_2" used? Yes.
    # Should become "A_B_3"
    id3 = formatter._sanitize("A-B")
    assert id3 == "A_B_3"


def test_formatter_long_stack_trace_truncation():
    formatter = MermaidFormatter()
    long_stack = "a" * 500
    event = FlowEvent(
        source="A",
        target="B",
        action="E",
        message="M",
        trace_id="1",
        is_error=True,
        error_message="E",
        stack_trace=long_stack,
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event

    formatter.format(record)
    line = formatter.flush()
    assert len(line) < 600  # Should be truncated
    assert "..." in line


def test_formatter_return_empty_result():
    formatter = MermaidFormatter()
    event = FlowEvent(
        source="A",
        target="B",
        action="Call",
        message="Ret",
        trace_id="1",
        is_return=True,
        result=None,
    )
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event

    formatter.format(record)
    line = formatter.flush()
    # Should be just "Return" without value
    assert "Return" in line
    assert "Return:" not in line
