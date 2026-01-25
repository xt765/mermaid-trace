import asyncio
import time
import threading
from mermaid_trace import trace, configure_flow

# Configure output to a specific file
configure_flow("concurrency_trace.mmd")


@trace(source="Main", target="Worker")
def heavy_computation(x: int) -> int:
    """Simulates a blocking computation."""
    time.sleep(0.1)
    return x * x


@trace(source="Main", target="AsyncService")
async def fetch_data(delay: float) -> str:
    """Simulates an IO-bound async task."""
    await asyncio.sleep(delay)
    return f"data_{delay}"


@trace(source="Orchestrator", target="Main")
async def main() -> None:
    print("Starting concurrent tasks...")

    # 1. Threading example: Tracing across threads
    # LogContext uses thread-local storage, so each thread maintains its own context.
    threads = []
    for i in range(3):
        t = threading.Thread(target=heavy_computation, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 2. Asyncio example: Tracing async flows
    # LogContext uses contextvars, so it propagates correctly through async calls.
    await asyncio.gather(fetch_data(0.1), fetch_data(0.2), fetch_data(0.15))


if __name__ == "__main__":
    asyncio.run(main())
    print("Done. Check 'concurrency_trace.mmd' for the diagram.")
