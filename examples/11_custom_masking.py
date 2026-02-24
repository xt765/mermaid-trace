"""
Advanced Data Masking.
Demonstrates:
1. Handling complex, deeply nested data structures.
2. Configuring sensitive patterns to mask different types of PII.
3. How MermaidTrace automatically sanitizes arguments before logging.
"""

from typing import Dict, Any
from mermaid_trace import trace, configure_flow
from mermaid_trace.core.config import config

# Configure output
configure_flow("mermaid_diagrams/examples/advanced_masking.mmd")

# 1. CONFIGURE SENSITIVE PATTERNS
# MermaidTrace uses simple string matching on dictionary keys.
# Any key containing these substrings will have its value replaced with '******'.
config.mask_patterns = [
    "password",
    "token",
    "secret",
    "ssn",  # Social Security Number
    "cc_num",  # Credit Card Number
    "api_key",
]

# 2. OPTIONAL: Customize the replacement string
config.mask_value = "<REDACTED>"

# 3. OPTIONAL: Control recursion depth to prevent infinite loops or huge logs
config.max_arg_depth = 3


@trace(source="Client", target="PaymentSystem", action="Process Payment")
def process_payment(user_data: Dict[str, Any]) -> Dict[str, str]:
    # user_data contains highly sensitive info
    print("Processing payment...")
    validate_user(user_data)
    return {"status": "success", "transaction_id": "tx_999"}


@trace(target="Validator")
def validate_user(data: Dict[str, Any]) -> bool:
    # Just a dummy check
    return True


def run_demo() -> None:
    # A complex, nested structure simulating a real-world payload
    sensitive_payload = {
        "user_id": 101,
        "name": "John Doe",
        "contact": {"email": "john@example.com", "phone": "+1-555-0199"},
        "billing": {
            "address": "123 Main St",
            # SENSITIVE: This key matches "cc_num" pattern
            "cc_num": "4111-2222-3333-4444",
            # SENSITIVE: Matches "ssn"
            "ssn": "999-00-1234",
            "meta": {
                # deeply nested sensitive data
                "api_key_backup": "sk-12345abcdef"
            },
        },
        "history": [
            {"date": "2023-01-01", "amount": 100},
            # This list item itself isn't masked, but keys inside it would be if they matched
            {"date": "2023-02-01", "secret_note": "hidden"},
        ],
    }

    print("Sending payload with sensitive data...")
    # The diagram will show the structure, but values for 'cc_num', 'ssn', etc. will be <REDACTED>
    process_payment(sensitive_payload)


if __name__ == "__main__":
    run_demo()
    print("Done! Check 'mermaid_diagrams/examples/advanced_masking.mmd'.")
    print(
        "Verify that 'cc_num', 'ssn', and 'api_key_backup' are replaced with <REDACTED>."
    )
