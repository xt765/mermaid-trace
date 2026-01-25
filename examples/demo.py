import time
import asyncio
from mermaid_trace import trace_interaction, configure_flow

# Configure to output to flow.mmd
configure_flow("flow.mmd")

@trace_interaction("Client", "API", "Request Data")
def fetch_data():
    time.sleep(0.1)
    process_db()
    return "Data"

@trace_interaction("API", "Database", "Query Users")
def process_db():
    time.sleep(0.1)
    return ["User1", "User2"]

@trace_interaction("Client", "AsyncService", "Do Async Work")
async def async_work():
    await asyncio.sleep(0.1)
    return "Done"

def main():
    print("Running sync demo...")
    fetch_data()
    
    print("Running async demo...")
    asyncio.run(async_work())
    print("Check flow.mmd for results!")

if __name__ == "__main__":
    main()
