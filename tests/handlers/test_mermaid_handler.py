import logging
from pathlib import Path
from mermaid_trace.handlers.mermaid_handler import MermaidFileHandler
from mermaid_trace.core.events import FlowEvent

def test_handler_creation(tmp_path: Path) -> None:
    log_file = tmp_path / "flow.mmd"
    handler = MermaidFileHandler(str(log_file), title="Test Flow")
    
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "sequenceDiagram" in content
    assert "title Test Flow" in content
    handler.close()

def test_handler_emit(tmp_path: Path) -> None:
    log_file = tmp_path / "flow.mmd"
    handler = MermaidFileHandler(str(log_file))
    
    # Manually attach a formatter since we test handler isolation
    from mermaid_trace.core.formatter import MermaidFormatter
    handler.setFormatter(MermaidFormatter())
    
    event = FlowEvent("A", "B", "Call", "Msg", "1")
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", None, None)
    record.flow_event = event
    
    handler.emit(record)
    handler.close()
    
    content = log_file.read_text(encoding="utf-8")
    assert "A->>B: Msg" in content

def test_handler_delay(tmp_path: Path) -> None:
    log_file = tmp_path / "delayed.mmd"
    # delay=True
    handler = MermaidFileHandler(str(log_file), delay=True)
    
    # File might exist but empty or not created depending on implementation details of FileHandler
    # But standard FileHandler with delay=True doesn't open until emit.
    # However, our MermaidHandler constructor calls _write_header which might trigger open if not careful.
    # Let's verify our implementation behavior.
    
    if log_file.exists():
        # If it exists, it should at least have the header
        assert "sequenceDiagram" in log_file.read_text(encoding="utf-8")
    
    handler.close()

def test_handler_append_mode(tmp_path: Path) -> None:
    log_file = tmp_path / "append.mmd"
    # Create initial file
    log_file.write_text("sequenceDiagram\n    title Old\n", encoding="utf-8")
    
    handler = MermaidFileHandler(str(log_file), mode='a')
    # Should NOT write header again if file exists and has content
    handler.close()
    
    content = log_file.read_text(encoding="utf-8")
    assert content.count("sequenceDiagram") == 1
