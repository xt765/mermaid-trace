import asyncio
import pytest
import time
from pathlib import Path
from mermaid_trace import trace, configure_flow
from mermaid_trace.handlers.async_handler import AsyncMermaidHandler
import logging

@pytest.mark.asyncio
async def test_concurrency_consistency(tmp_path: Path) -> None:
    log_file = tmp_path / "concurrency.mmd"
    
    # Configure global logger for this test
    # We use a unique logger name or reset handlers to avoid interference
    logger = configure_flow(str(log_file), async_mode=True)
    
    # Verify we are using async handler
    assert any(isinstance(h, AsyncMermaidHandler) for h in logger.handlers)

    @trace
    async def worker(name: str, delay: float) -> str:
        await asyncio.sleep(delay)
        return f"{name} done"

    # Launch multiple concurrent tasks
    count = 20
    tasks = [worker(f"Worker-{i}", 0.01) for i in range(count)]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == count
    assert results[0] == "Worker-0 done"

    # Give the async handler a moment to write everything
    # In a real app, atexit handles this, or explicit stop.
    # Here we can access the handler and stop it to ensure flush.
    for h in logger.handlers:
        if isinstance(h, AsyncMermaidHandler):
            h.stop()
            
    # Check file content
    content = log_file.read_text(encoding="utf-8")
    
    # We expect 2 lines per worker (Call + Return)
    # Total lines = header (2) + 2 * count
    # But since it's async, the order might vary, but all lines must be there.
    
    lines = content.strip().splitlines()
    # Filter out header
    data_lines = [l for l in lines if "Worker-" in l]
    
    assert len(data_lines) == count * 2, f"Expected {count*2} lines, got {len(data_lines)}"
    
    for i in range(count):
        assert f"Worker-{i}" in content
        assert f"Return: 'Worker-{i} done'" in content or f"Return: Worker-{i} done" in content

@pytest.mark.asyncio
async def test_concurrency_trace_ids(tmp_path: Path) -> None:
    # Test that trace IDs are unique per task context if not shared
    log_file = tmp_path / "trace_ids.mmd"
    logger = configure_flow(str(log_file), async_mode=True)
    
    # We need to capture the trace IDs used.
    # The file log doesn't output trace_id by default in the mermaid syntax unless we customized it.
    # However, we can inspect the FlowEvents if we attach a memory handler, or just trust the context isolation logic which is tested in unit tests.
    # Let's rely on the fact that if contexts were mixed up, we might see wrong targets or returns.
    
    from mermaid_trace.core.context import LogContext

    @trace
    async def get_trace_id() -> str:
        await asyncio.sleep(0.01)
        return LogContext.current_trace_id()

    # Launch tasks with explicit separate contexts to simulate separate requests
    async def run_with_context(i: int) -> str:
        # Generate a unique trace ID for this "request"
        tid = f"trace-{i}"
        async with LogContext.ascope({"trace_id": tid}):
            return await get_trace_id()

    tasks = [run_with_context(i) for i in range(5)]
    ids = await asyncio.gather(*tasks)
    
    assert len(set(ids)) == 5, f"Trace IDs should be unique: {ids}"
    assert "trace-0" in ids
    
    for h in logger.handlers:
        if isinstance(h, AsyncMermaidHandler):
            h.stop()
