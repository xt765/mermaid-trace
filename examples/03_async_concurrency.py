"""
Asynchronous flow and Concurrency.
Demonstrates:
1. Tracing async/await coroutines
2. Correct context propagation across concurrent tasks (asyncio.gather)
"""

import asyncio
from mermaid_trace import trace, configure_flow

configure_flow("mermaid_diagrams/examples/async_flow.mmd")


@trace(target="ServiceA")
async def task_a(n: int) -> int:
    await asyncio.sleep(0.1)
    return n * 2


@trace(target="ServiceB")
async def task_b(n: int) -> int:
    await asyncio.sleep(0.05)
    return n + 10


@trace(source="Client", target="Orchestrator")
async def main() -> None:
    # MermaidTrace uses ContextVars, so even if these tasks run concurrently,
    # their internal calls will correctly point back to 'Orchestrator' as the source.
    print("Running concurrent async tasks...")
    results = await asyncio.gather(task_a(5), task_b(10), task_a(20))
    print(f"Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
    print("Done. Async flow captured in 'async_flow.mmd'.")
