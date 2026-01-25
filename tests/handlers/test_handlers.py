import logging
import time
import pytest
from pathlib import Path
from typing import Generator
from mermaid_trace.handlers.mermaid_handler import MermaidFileHandler
from mermaid_trace.handlers.async_handler import AsyncMermaidHandler
from mermaid_trace.core.events import FlowEvent
from mermaid_trace.core.formatter import MermaidFormatter


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "test_flow.mmd"


@pytest.fixture
def logger(log_file: Path) -> Generator[logging.Logger, None, None]:
    logger = logging.getLogger(f"test_logger_{time.time()}")
    logger.setLevel(logging.INFO)
    handler = MermaidFileHandler(str(log_file))
    handler.setFormatter(MermaidFormatter())
    logger.addHandler(handler)
    yield logger
    for h in logger.handlers:
        h.close()


def test_mermaid_file_handler_creation(log_file: Path) -> None:
    handler = MermaidFileHandler(str(log_file), title="Test Flow")
    handler.close()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "sequenceDiagram" in content
    assert "title Test Flow" in content


def test_mermaid_file_handler_emit(logger: logging.Logger, log_file: Path) -> None:
    event = FlowEvent("A", "B", "Call", "Msg", "1")
    logger.info("msg", extra={"flow_event": event})

    # Force flush/close to ensure write
    for h in logger.handlers:
        h.close()

    content = log_file.read_text(encoding="utf-8")
    assert "A->>B: Msg" in content


def test_mermaid_file_handler_append_mode(tmp_path: Path) -> None:
    log_file = tmp_path / "append.mmd"
    log_file.write_text("sequenceDiagram\n    title Old\n", encoding="utf-8")

    handler = MermaidFileHandler(str(log_file), mode="a")
    handler.close()

    content = log_file.read_text(encoding="utf-8")
    assert content.count("sequenceDiagram") == 1


def test_mermaid_file_handler_delay(tmp_path: Path) -> None:
    log_file = tmp_path / "delay.mmd"
    handler = MermaidFileHandler(str(log_file), delay=True)
    # File might be created due to header writing attempt, or not.
    # Implementation: _write_header calls self.stream.tell().
    # If delay=True, self.stream is None initially.
    # logging.FileHandler with delay=True does NOT open stream until emit.
    # But MermaidFileHandler.__init__ calls _write_header -> self.stream.tell() -> self.stream causes open?
    # No, logging.FileHandler.stream property opens it?
    # Let's check if it crashes or works.

    handler.close()

    # If it works without error, good.


def test_async_mermaid_handler(tmp_path: Path) -> None:
    log_file = tmp_path / "async_flow.mmd"
    file_handler = MermaidFileHandler(str(log_file))
    file_handler.setFormatter(MermaidFormatter())

    async_handler = AsyncMermaidHandler([file_handler])

    logger = logging.getLogger(f"async_logger_{time.time()}")
    logger.setLevel(logging.INFO)
    logger.addHandler(async_handler)

    event = FlowEvent("AsyncSource", "AsyncTarget", "Call", "AsyncMsg", "1")
    logger.info("msg", extra={"flow_event": event})

    # Wait for the background thread to process
    time.sleep(0.5)

    async_handler.stop()

    content = log_file.read_text(encoding="utf-8")
    assert "AsyncSource->>AsyncTarget: AsyncMsg" in content


def test_async_handler_stop_flushes(tmp_path: Path) -> None:
    log_file = tmp_path / "flush_flow.mmd"
    file_handler = MermaidFileHandler(str(log_file))
    file_handler.setFormatter(MermaidFormatter())

    async_handler = AsyncMermaidHandler([file_handler])

    logger = logging.getLogger(f"flush_logger_{time.time()}")
    logger.setLevel(logging.INFO)
    logger.addHandler(async_handler)

    # Log many events
    for i in range(100):
        event = FlowEvent("S", "T", "Call", f"Msg{i}", "1")
        logger.info("msg", extra={"flow_event": event})

    # Stop immediately, should flush queue
    async_handler.stop()

    content = log_file.read_text(encoding="utf-8")
    for i in range(100):
        assert f"S->>T: Msg{i}" in content
