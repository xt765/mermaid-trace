from mermaid_trace import configure_flow
from mermaid_trace.core.config import config
from mermaid_trace.core.decorators import trace
from pathlib import Path


def test_configure_flow_overrides(diagram_output_dir: Path) -> None:
    # Save original config
    original_capture = config.capture_args
    original_len = config.max_string_length

    try:
        # Override config via configure_flow
        configure_flow(
            str(diagram_output_dir / "dummy.mmd"),
            config_overrides={"capture_args": False, "max_string_length": 999},
        )

        assert config.capture_args is False
        assert config.max_string_length == 999

    finally:
        # Restore config
        config.capture_args = original_capture
        config.max_string_length = original_len


def test_decorator_uses_config(caplog):
    # Save original config
    original_capture = config.capture_args

    try:
        # Set global config to NOT capture args
        config.capture_args = False

        @trace
        def my_func(arg):
            return arg

        my_func("secret")

        # Check logs
        assert len(caplog.records) >= 2
        req = caplog.records[0]
        # Should be empty because capture_args is False globally
        assert req.flow_event.params == ""

    finally:
        config.capture_args = original_capture


def test_decorator_override_precedence(caplog):
    # Save original config
    original_capture = config.capture_args

    try:
        # Set global config to False
        config.capture_args = False

        # But decorator explicitly says True
        @trace(capture_args=True)
        def my_func(arg):
            return arg

        my_func("visible")

        # Check logs
        req = caplog.records[0]
        # Should NOT be empty because decorator override takes precedence
        assert "visible" in req.flow_event.params

    finally:
        config.capture_args = original_capture
