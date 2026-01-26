import logging
from unittest.mock import MagicMock
from mermaid_trace.core.decorators import _safe_repr, _format_args, _resolve_target


def test_safe_repr_truncation():
    """Test that _safe_repr truncates long strings correctly"""
    # This test covers line 62: truncation logic
    long_string = "x" * 100
    result = _safe_repr(long_string, max_len=10, max_depth=1)
    assert "..." in result
    assert len(result) <= 13  # 10 chars + "..." + quotes


def test_safe_repr_unrepresentable():
    """Test that _safe_repr handles unrepresentable objects"""
    # Test with a built-in object that might be unrepresentable
    # Use a more direct approach to trigger the exception handling
    import sys
    
    # Test with a recursive dictionary which might cause issues
    recursive_dict = {}
    recursive_dict["self"] = recursive_dict
    
    result = _safe_repr(recursive_dict, max_len=50, max_depth=1)
    assert "..." in result  # Should be truncated
    assert "self" in result


def test_format_args_keyword():
    """Test that _format_args correctly formats keyword arguments"""
    # This test covers lines 101-102: keyword argument formatting
    result = _format_args(
        args=(),
        kwargs={"key1": "value1", "key2": 123},
        max_arg_length=50,
        max_arg_depth=1
    )
    assert "key1='value1'" in result
    assert "key2=123" in result


def test_format_args_combined():
    """Test that _format_args handles combined positional and keyword arguments"""
    result = _format_args(
        args=("pos1", 123),
        kwargs={"key1": "value1"},
        max_arg_length=50,
        max_arg_depth=1
    )
    assert "pos1" in result
    assert "123" in result
    assert "key1='value1'" in result


def test_resolve_target_fallback():
    """Test that _resolve_target returns 'Unknown' when module cannot be determined"""
    # This test covers line 148: fallback to 'Unknown'
    # Create a function with no module
    def test_func():
        pass
    
    # Remove the module attribute to simulate the fallback case
    test_func.__module__ = None
    
    result = _resolve_target(test_func, args=(), target_override=None)
    assert result == "Unknown"


def test_resolve_target_with_target_override():
    """Test that _resolve_target respects target_override"""
    def test_func():
        pass
    
    result = _resolve_target(test_func, args=(), target_override="CustomTarget")
    assert result == "CustomTarget"


def test_safe_repr_nested_depth():
    """Test that _safe_repr handles nested structures with depth limitation"""
    nested_dict = {"level1": {"level2": {"level3": "deep"}}}
    
    # Test with depth=2, should truncate at level 2
    result = _safe_repr(nested_dict, max_len=100, max_depth=2)
    assert "level3" not in result  # Should be truncated due to depth
    
    # Test with sufficient depth, should include all levels
    result_full = _safe_repr(nested_dict, max_len=100, max_depth=3)
    assert "level3" in result_full
