"""
Diagram management: Intelligent Collapsing.
Demonstrates:
1. Automatic collapsing of repetitive calls in loops
2. Preventing diagram explosion while maintaining flow visibility
"""

from mermaid_trace import trace, configure_flow

# Enable intelligent collapsing (usually on by default in future versions,
# but here we ensure it's set up)
configure_flow("mermaid_diagrams/examples/collapsed_flow.mmd")


@trace(target="Worker")
def process_item(i: int) -> int:
    return i * 10


@trace(source="Manager", target="Processor")
def run_loop() -> None:
    # Calling the same function 100 times would normally create 100 arrows.
    # MermaidTrace detects this high-frequency call and collapses it.
    print("Processing 50 items in a loop...")
    for i in range(50):
        process_item(i)


if __name__ == "__main__":
    run_loop()
    print("Check 'collapsed_flow.mmd'. Notice how the loop is represented cleanly.")
