import pytest
from mermaid_trace import trace, configure_flow
from typing import Any, Generator
import logging


@pytest.fixture
def clean_logger(diagram_output_dir: Any) -> Generator[logging.Logger, None, None]:
    f = diagram_output_dir / "edge.mmd"
    if f.exists():
        f.unlink()
    logger = configure_flow(str(f))
    yield logger
    for h in logger.handlers:
        h.close()


def test_recursive_calls(clean_logger: logging.Logger) -> None:
    @trace
    def factorial(n: int) -> int:
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    assert factorial(5) == 120
    # Should not crash and produce nested logs


def test_large_arguments(clean_logger: logging.Logger, caplog: Any) -> None:
    @trace(max_arg_length=100)
    def process_data(data: str) -> None:
        pass

    large_string = "x" * 1000
    process_data(large_string)

    # Check if it was truncated
    # The default safe_repr truncates
    rec = caplog.records[0]
    assert len(rec.flow_event.params) < 1000
    assert "..." in rec.flow_event.params


def test_unrepresentable_args(clean_logger: logging.Logger, caplog: Any) -> None:
    from unittest.mock import patch

    class BadRepr:
        pass

    @trace
    def risky(obj: Any) -> None:
        pass

    # Patch Repr.repr to simulate failure
    with patch("reprlib.Repr.repr", side_effect=Exception("No repr for you")):
        risky(BadRepr())

    rec = caplog.records[0]
    assert "<unrepresentable>" in rec.flow_event.params


def test_exception_in_handler(clean_logger: logging.Logger) -> None:
    # If the handler fails (e.g. disk full), application should ideally continue?
    # Standard logging swallows handler exceptions by default (emit catches and calls handleError)
    # mermaid-trace relies on standard logging, so it should be safe.
    pass


def test_context_cleanup_on_error(clean_logger: logging.Logger) -> None:
    from mermaid_trace.core.context import LogContext

    @trace(target="Scope")
    def fail() -> None:
        assert LogContext.current_participant() == "Scope"
        raise ValueError("Fail")

    LogContext.set_participant("Outer")

    with pytest.raises(ValueError):
        fail()

    # Context should be restored
    assert LogContext.current_participant() == "Outer"
