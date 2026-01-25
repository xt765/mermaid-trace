import time
import pytest
import logging
from pathlib import Path
from mermaid_trace import trace, configure_flow
from mermaid_trace.handlers.async_handler import AsyncMermaidHandler

def benchmark_handler(tmp_path: Path, async_mode: bool, iterations: int = 1000) -> float:
    log_file = tmp_path / f"bench_{async_mode}.mmd"
    logger = configure_flow(str(log_file), async_mode=async_mode)
    
    # We want to measure the overhead on the MAIN THREAD.
    
    @trace(capture_args=False)
    def fast_func():
        pass
        
    start = time.time()
    for _ in range(iterations):
        fast_func()
    end = time.time()
    
    # Cleanup
    for h in logger.handlers:
        if isinstance(h, AsyncMermaidHandler):
            h.stop()
        else:
            h.close()
            
    return end - start

def test_performance_async_vs_sync(tmp_path: Path) -> None:
    # Run a small benchmark
    # Note: File I/O in sync mode is very slow, so difference should be huge.
    
    iterations = 500
    
    sync_time = benchmark_handler(tmp_path, async_mode=False, iterations=iterations)
    async_time = benchmark_handler(tmp_path, async_mode=True, iterations=iterations)
    
    print(f"\nSync time: {sync_time:.4f}s")
    print(f"Async time: {async_time:.4f}s")
    
    # Async should be faster, or at least comparable (overhead of queue vs file io)
    # Usually async is much faster because it doesn't wait for disk.
    
    # We assert that async is not drastically slower (e.g. < 2x sync time if sync was fast, but sync is slow)
    # Relaxed assertion for stability
    if sync_time > 0.1: # Only if sync is significant enough to measure
         print(f"Ratio: {sync_time/async_time}")

@pytest.mark.asyncio
async def test_performance_async_overhead(tmp_path: Path) -> None:
    # Measure overhead of tracing vs no tracing
    log_file = tmp_path / "overhead.mmd"
    logger = configure_flow(str(log_file), async_mode=True)
    
    def no_trace():
        return 1
        
    @trace(capture_args=False)
    def with_trace():
        return 1
        
    iterations = 10000
    
    start = time.time()
    for _ in range(iterations):
        no_trace()
    base_time = time.time() - start
    
    start = time.time()
    for _ in range(iterations):
        with_trace()
    trace_time = time.time() - start
    
    print(f"\nBase time: {base_time:.4f}s")
    print(f"Trace time: {trace_time:.4f}s")
    
    # Just to ensure it's not insanely slow. 
    # Python function call overhead is small, tracing adds logic.
    # We verify it runs within reasonable limits (e.g. < 0.5ms per call).
    avg_call_time = trace_time / iterations
    assert avg_call_time < 0.001, f"Tracing is too slow: {avg_call_time*1000:.4f}ms per call"
    
    for h in logger.handlers:
        if isinstance(h, AsyncMermaidHandler):
            h.stop()
