"""
Error handling and Stack trace capture.
Demonstrates:
1. Automatic detection of exceptions
2. Rendering of error arrows (--)x in Mermaid
3. Displaying stack traces as Notes in the diagram
"""

from mermaid_trace import trace, configure_flow

configure_flow("mermaid_diagrams/examples/error_handling.mmd")


@trace(target="Validator")
def validate(data: str) -> bool:
    if not data:
        raise ValueError("Data cannot be empty!")
    return True


@trace(target="Processor")
def process(data: str) -> None:
    # This will fail
    validate(data)


@trace(source="User", target="App")
def main() -> None:
    print("Triggering an error...")
    try:
        process("")
    except ValueError as e:
        print(f"Caught expected error: {e}")


if __name__ == "__main__":
    main()
    print("The error and its stack trace are now in 'error_handling.mmd'.")
