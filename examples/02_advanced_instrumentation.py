"""
Advanced instrumentation techniques.
Demonstrates:
1. @trace_class: Automatically instrument all methods in a class
2. patch_object: Instrument third-party library methods without modifying their source
"""

from mermaid_trace import trace_class, patch_object, configure_flow
import requests  # type: ignore # Make sure requests is installed: pip install requests


# 1. Setup
configure_flow("mermaid_diagrams/examples/instrumentation_demo.mmd")


# 2. @trace_class example
# All methods (except private ones) will be automatically traced
@trace_class(target="PaymentProcessor")
class PaymentProcessor:
    def validate_card(self, card_no: str) -> bool:
        return True

    def charge(self, amount: float) -> str:
        return f"Charged ${amount}"


# 3. patch_object example
# We can trace third-party libraries like 'requests'
# This solves the "gap" in diagrams when calling external services
# Correct usage: target and other kwargs are passed to the underlying trace decorator
patch_object(requests, "get", target="ExternalAPI", action="HTTP GET")


def run_demo() -> None:
    proc = PaymentProcessor()
    proc.validate_card("1234-5678")

    print("Calling external API (patched)...")
    # This call to requests.get will now appear in the Mermaid diagram!
    try:
        requests.get("https://api.github.com", timeout=1)
    except Exception:
        pass

    proc.charge(99.9)


if __name__ == "__main__":
    run_demo()
    print("Check 'instrumentation_demo.mmd' for the auto-instrumented flow.")
