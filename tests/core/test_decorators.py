import pytest
import asyncio
import json
from logcapy import catch, retry
from logcapy.core.context import LogContext

def test_catch_sync(caplog):
    @catch(default_return="caught", reraise=False)
    def fail():
        raise ValueError("Oops")

    assert fail() == "caught"
    
    assert "Oops" in caplog.text
    # We can also check structured fields if we want, but caplog.records has LogRecord objects
    # To verify JSON output specifically, we'd need to inspect the handler or formatter, 
    # but verifying the log message presence is enough for core logic.

@pytest.mark.asyncio
async def test_catch_async(caplog):
    @catch(default_return="caught", reraise=False)
    async def fail():
        raise ValueError("Async Oops")

    assert await fail() == "caught"
    
    assert "Async Oops" in caplog.text

def test_retry_sync(caplog):
    attempts = 0
    @retry(max_attempts=2, delay=0.01)
    def unstable():
        nonlocal attempts
        attempts += 1
        raise ValueError("Fail")

    with pytest.raises(ValueError):
        unstable()
    
    assert attempts == 2
    assert "Retry failed" in caplog.text

@pytest.mark.asyncio
async def test_retry_async(caplog):
    attempts = 0
    @retry(max_attempts=2, delay=0.01)
    async def unstable():
        nonlocal attempts
        attempts += 1
        raise ValueError("Async Fail")

    with pytest.raises(ValueError):
        await unstable()
    
    assert attempts == 2
    assert "Retry failed" in caplog.text
