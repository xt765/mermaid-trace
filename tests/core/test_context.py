import pytest
from logcapy.core.context import LogContext
import asyncio

def test_context_set_get():
    LogContext.set("key", "value")
    assert LogContext.get("key") == "value"
    assert LogContext.get("missing") is None

def test_context_isolation():
    LogContext.set("key", "main")
    
    async def task(val):
        LogContext.set("key", val)
        await asyncio.sleep(0.01)
        return LogContext.get("key")
        
    async def run():
        results = await asyncio.gather(task("task1"), task("task2"))
        return results

    results = asyncio.run(run())
    assert results == ["task1", "task2"]
    assert LogContext.get("key") == "main"
