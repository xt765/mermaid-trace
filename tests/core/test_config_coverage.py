import os
from unittest import mock
from mermaid_trace.core.config import MermaidConfig


def test_config_defaults():
    config = MermaidConfig()
    assert config.capture_args is True
    assert config.max_string_length == 50
    assert config.max_arg_depth == 1
    assert config.queue_size == 1000


def test_config_from_env():
    env_vars = {
        "MERMAID_TRACE_CAPTURE_ARGS": "false",
        "MERMAID_TRACE_MAX_STRING_LENGTH": "100",
        "MERMAID_TRACE_MAX_ARG_DEPTH": "5",
        "MERMAID_TRACE_QUEUE_SIZE": "500",
    }

    with mock.patch.dict(os.environ, env_vars):
        config = MermaidConfig.from_env()
        assert config.capture_args is False
        assert config.max_string_length == 100
        assert config.max_arg_depth == 5
        assert config.queue_size == 500


def test_config_from_env_defaults():
    # Test that it falls back to defaults if env vars are missing
    with mock.patch.dict(os.environ, {}, clear=True):
        config = MermaidConfig.from_env()
        assert config.capture_args is True
        assert config.max_string_length == 50
