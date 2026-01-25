import pytest
from mermaid_trace import trace, configure_flow
from typing import Any, Generator
import logging


@pytest.fixture
def flow_logger(tmp_path: Any) -> Generator[logging.Logger, None, None]:
    f = tmp_path / "basic_flow.mmd"
    logger = configure_flow(str(f))
    yield logger
    for h in logger.handlers:
        h.close()


def test_trace_interaction(flow_logger: logging.Logger, tmp_path: Any) -> None:
    output_file = tmp_path / "basic_flow.mmd"

    @trace(source="A", target="B", action="Action")
    def func() -> str:
        return "ok"

    func()

    content = output_file.read_text(encoding="utf-8")

    assert "sequenceDiagram" in content
    assert "A->>B: Action" in content
    assert "B-->>A: Return" in content


def test_error_interaction(flow_logger: logging.Logger, tmp_path: Any) -> None:
    output_file = tmp_path / "basic_flow.mmd"

    @trace(source="A", target="B", action="Fail")
    def fail() -> None:
        raise ValueError("oops")

    with pytest.raises(ValueError):
        fail()

    content = output_file.read_text(encoding="utf-8")

    assert "B--xA: Error" in content
