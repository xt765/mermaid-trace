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
def log_file(diagram_output_dir: Path) -> Path:
    f = diagram_output_dir / "test_flow.mmd"
    if f.exists():
        f.unlink()
    return f


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
    # Formatter must be set for header to be written correctly now
    handler.setFormatter(MermaidFormatter())

    # Since we moved to lazy header writing, the file should be empty initially
    # (created by FileHandler open(), but no content written)
    assert log_file.exists()
    assert log_file.stat().st_size == 0

    # Emit a record to trigger header writing
    logger = logging.getLogger("test_creation")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    event = FlowEvent("A", "B", "Action", "Message", "trace1")
    logger.info("msg", extra={"flow_event": event})

    handler.close()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "sequenceDiagram" in content
    assert "title Test Flow" in content
    assert "A->>B: Message" in content


def test_mermaid_file_handler_emit(logger: logging.Logger, log_file: Path) -> None:
    event = FlowEvent("A", "B", "Call", "Msg", "1")
    logger.info("msg", extra={"flow_event": event})

    # Force flush/close to ensure write
    for h in logger.handlers:
        h.close()

    content = log_file.read_text(encoding="utf-8")
    assert "sequenceDiagram" in content  # Header should be there
    assert "A->>B: Msg" in content


def test_mermaid_file_handler_append_mode(diagram_output_dir: Path) -> None:
    log_file = diagram_output_dir / "append.mmd"
    if log_file.exists():
        log_file.unlink()
    log_file.write_text("sequenceDiagram\n    title Old\n", encoding="utf-8")

    handler = MermaidFileHandler(str(log_file), mode="a")
    handler.setFormatter(MermaidFormatter())

    # Emit to trigger check
    logger = logging.getLogger("test_append")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    event = FlowEvent("A", "B", "Action", "Message", "trace1")
    logger.info("msg", extra={"flow_event": event})

    handler.close()

    content = log_file.read_text(encoding="utf-8")
    # Should NOT add another header because file was not empty
    assert content.count("sequenceDiagram") == 1
    assert "A->>B: Message" in content


def test_mermaid_file_handler_delay(diagram_output_dir: Path) -> None:
    log_file = diagram_output_dir / "delay.mmd"
    if log_file.exists():
        log_file.unlink()
    handler = MermaidFileHandler(str(log_file), delay=True)
    handler.setFormatter(MermaidFormatter())

    # File should NOT exist yet
    assert not log_file.exists()

    # Emit triggers creation
    logger = logging.getLogger("test_delay")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    event = FlowEvent("A", "B", "Action", "Message", "trace1")
    logger.info("msg", extra={"flow_event": event})

    handler.close()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "sequenceDiagram" in content
    assert "A->>B: Message" in content


def test_async_mermaid_handler(diagram_output_dir: Path) -> None:
    log_file = diagram_output_dir / "async_flow.mmd"
    if log_file.exists():
        log_file.unlink()
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


def test_async_handler_stop_flushes(diagram_output_dir: Path) -> None:
    log_file = diagram_output_dir / "flush_flow.mmd"
    if log_file.exists():
        log_file.unlink()
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

    # Stop immediately, should flush queue and formatter buffers
    async_handler.stop()

    content = log_file.read_text(encoding="utf-8")
    # With intelligent collapsing, 100 repetitive calls are merged into one line
    # The message comes from the first event in the buffer
    assert "S->>T: Msg0 (x100)" in content
