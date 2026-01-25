import time
import asyncio
from mermaid_trace import trace_interaction, configure_flow

# Configure to output to flow.mmd
configure_flow("flow.mmd")


@trace_interaction(source="Client", target="API", action="Request Data")
def fetch_data() -> str:
    time.sleep(0.1)
    process_db()
    return "Data"


@trace_interaction(source="API", target="Database", action="Query Users")
def process_db() -> list[str]:
    time.sleep(0.1)
    return ["User1", "User2"]


@trace_interaction(source="Client", target="AsyncService", action="Do Async Work")
async def async_work() -> str:
    await asyncio.sleep(0.1)
    return "Done"


def main() -> None:
    print("Running sync demo...")
    fetch_data()

    print("Running async demo...")
    asyncio.run(async_work())
    print("Check flow.mmd for results!")


if __name__ == "__main__":
    main()
