from unittest.mock import patch
from mermaid_trace.core.decorators import FlowRepr, _safe_repr


def test_flow_repr_grouping():
    repr_obj = FlowRepr()
    # Test grouping in list
    # 'a' becomes "'a'" via repr()
    data = ["a", "a", "a", "b", "c", "c"]
    result = repr_obj.repr_list(data, 1)
    # Expected: ["'a'" x 3, 'b', "'c'" x 2]
    # Note: reprlib puts spaces around elements? No, usually ", ".
    # The grouping logic adds " x N".
    # So "'a'" becomes "'a' x 3".
    assert result == "['a' x 3, 'b', 'c' x 2]"

    # Test grouping in tuple
    data_tuple = ("a", "a", "b")
    result_tuple = repr_obj.repr_tuple(data_tuple, 1)
    assert result_tuple == "('a' x 2, 'b')"

    # Test empty list
    assert repr_obj.repr_list([], 1) == "[]"
    # Test empty tuple
    assert repr_obj.repr_tuple((), 1) == "()"
    # Test single item tuple
    assert repr_obj.repr_tuple(("a",), 1) == "('a',)"


def test_flow_repr_max_items():
    repr_obj = FlowRepr()
    repr_obj.maxlist = 2
    repr_obj.maxtuple = 2

    data = ["a", "a", "a", "a"]
    result = repr_obj.repr_list(data, 1)
    # The result depends on implementation but should contain "..."
    assert "..." in result

    data_tuple = ("a", "a", "a", "a")
    result_tuple = repr_obj.repr_tuple(data_tuple, 1)
    assert "..." in result_tuple


def test_safe_repr_truncation():
    # Test truncation logic in _safe_repr
    long_str = "a" * 1000
    # Use a case where reprlib doesn't truncate but the final length check does
    # Or just check that it is truncated.
    result = _safe_repr(long_str, max_len=10)
    assert len(result) <= 13
    # reprlib might return "'aa...aaa'" or similar.
    # The final check in _safe_repr only adds ... if len(r) > final_max_len.
    assert "..." in result


def test_group_items_empty():
    """Test _group_items with empty list."""
    repr_obj = FlowRepr()
    result = repr_obj._group_items([])
    assert result == []


def test_safe_repr_truncation_exact():
    """Test _safe_repr truncation when length exceeds limit."""
    # To hit line 211, we need r to be longer than final_max_len.
    # We can mock a_repr.repr to return something long.
    with patch("mermaid_trace.core.decorators.FlowRepr.repr") as mock_repr:
        mock_repr.return_value = "a" * 20
        result = _safe_repr("some obj", max_len=10)
        assert len(result) == 13  # 10 + "..."
        assert result.endswith("...")


def test_safe_repr_exception():
    class BuggyRepr:
        def __repr__(self):
            raise ValueError("Buggy")

    result = _safe_repr(BuggyRepr())
    assert result == "<unrepresentable>"


def test_flow_repr_default_obj():
    class MyObj:
        pass

    obj = MyObj()
    # Default repr would be something like <test_decorators_coverage.test_flow_repr_default_obj.<locals>.MyObj object at 0x...>
    repr_obj = FlowRepr()
    result = repr_obj.repr1(obj, 1)
    assert result == "<MyObj>"

    # Test another case: <MyObj at 0x...>
    class AnotherObj:
        def __repr__(self):
            return f"<AnotherObj at {hex(id(self))}>"

    obj2 = AnotherObj()
    result2 = repr_obj.repr1(obj2, 1)
    assert result2 == "<AnotherObj>"
