"""
Tests for the Data Sanitizer module.
"""

from dataclasses import dataclass
from mermaid_trace.core.sanitizer import DataMasker
from mermaid_trace.core.config import config


def test_sanitizer_basic():
    masker = DataMasker()
    # Test dictionary masking
    data = {"password": "secret123", "username": "admin", "api_key": "xyz"}
    masked = masker.mask(data)
    assert masked["password"] == "******"
    assert masked["username"] == "admin"
    assert masked["api_key"] == "******"  # "key" is in default mask list


def test_sanitizer_recursion():
    # Increase depth to test deep masking
    orig_depth = config.max_arg_depth
    config.max_arg_depth = 5
    try:
        masker = DataMasker()
        # Test nested dicts
        data = {"user": {"credentials": {"password": "secret123"}, "name": "john"}}
        masked = masker.mask(data)
        assert masked["user"]["credentials"]["password"] == "******"
        assert masked["user"]["name"] == "john"
    finally:
        config.max_arg_depth = orig_depth


def test_sanitizer_lists_tuples_sets():
    masker = DataMasker()
    # Test lists containing sensitive dicts
    data_list = [{"token": "123"}, {"id": 1}]
    masked_list = masker.mask(data_list)
    assert masked_list[0]["token"] == "******"
    assert masked_list[1]["id"] == 1

    # Test tuples
    data_tuple = ({"secret": "abc"},)
    masked_tuple = masker.mask(data_tuple)
    assert isinstance(masked_tuple, tuple)
    assert masked_tuple[0]["secret"] == "******"

    # Test sets (elements must be hashable, so no dicts usually, but maybe objects?)
    # Sets are unordered and items must be immutable. We can't mask a string inside a set
    # unless we replace the string itself, but we mask VALUES in dicts.
    # If we have a set of sensitive strings? The masker doesn't support that yet (it masks keys).
    # But it should handle sets gracefully.
    data_set = {1, 2}
    masked_set = masker.mask(data_set)
    assert masked_set == {1, 2}


def test_sanitizer_objects():
    @dataclass
    class User:
        username: str
        password: str

    masker = DataMasker()
    user = User(username="admin", password="123")

    # Masker converts objects to dicts for safe representation
    masked = masker.mask(user)
    assert isinstance(masked, dict)
    assert masked["username"] == "admin"
    assert masked["password"] == "******"


def test_sanitizer_depth_limit():
    masker = DataMasker()
    # Default depth is 1 (from config)
    # Level 0: root
    # Level 1: nested
    # Level 2: deep (should remain as is or stop recursion)

    # Note: mask(data, depth=0).
    # if depth > config.max_arg_depth (1): return data

    data = {"level1": {"level2": {"password": "123"}}}
    # level1 value is a dict (depth 1 call).
    # inside level1, we call mask(level2_dict, depth=2).
    # 2 > 1 -> returns level2_dict AS IS.

    masked = masker.mask(data)
    # So nested password should NOT be masked because it's too deep
    assert masked["level1"]["level2"]["password"] == "123"


def test_custom_patterns():
    # Save original
    orig_patterns = config.mask_patterns
    try:
        config.mask_patterns = ["custom"]
        masker = DataMasker()  # Re-init to pick up config

        data = {"custom_field": "123", "password": "456"}
        masked = masker.mask(data)
        assert masked["custom_field"] == "******"
        assert masked["password"] == "456"  # Should not be masked now
    finally:
        config.mask_patterns = orig_patterns
