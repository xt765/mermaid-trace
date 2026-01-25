import asyncio
import time
import os
from mermaid_trace.core.decorators import trace
from mermaid_trace import configure_flow

# Configure to a specific file for testing
TEST_FILE = "concurrency_test.mmd"
if os.path.exists(TEST_FILE):
    os.remove(TEST_FILE)
    
configure_flow(TEST_FILE)

@trace
async def worker(name: str, delay: float):
    await asyncio.sleep(delay)
    return f"{name} done"

async def main():
    print("Starting concurrency test...")
    start_time = time.time()
    
    # Launch multiple concurrent tasks
    tasks = [
        worker(f"Worker-{i}", 0.1) 
        for i in range(10)
    ]
    
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    print(f"Tasks completed in {duration:.4f}s")
    
    # Check file content for interleaving (basic check)
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Log file size: {len(content)} bytes")
        # In a perfect world without interleaving issues confusing the diagram, 
        # or performance issues, this should be fast.
        # The current implementation opens/closes file on every write, which is slow.

if __name__ == "__main__":
    asyncio.run(main())
