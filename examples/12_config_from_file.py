"""
Configuration from File.
Demonstrates:
1. Loading MermaidTrace configuration from an external JSON file.
2. Dynamically updating global settings at runtime.
3. Decoupling configuration from code (ideal for different environments: dev/prod).
"""

import json
import os
from typing import Dict, Any
from mermaid_trace import trace, configure_flow
from mermaid_trace.core.config import config

# 1. SETUP: Ensure we output to a known location
configure_flow("mermaid_diagrams/examples/config_loaded.mmd")


def load_config_from_file(filepath: str) -> None:
    """
    Reads a JSON file and updates the global `mermaid_trace.config`.
    """
    if not os.path.exists(filepath):
        print(f"Config file not found: {filepath}")
        return

    print(f"Loading configuration from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # 2. UPDATE CONFIG: Iterate and set attributes on the config object
    # This is safe because config is a singleton instance.
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)
            print(f"  -> Set config.{key} = {value}")
        else:
            print(f"  -> Warning: Unknown config key '{key}', skipping.")


@trace(source="App", target="ConfigLoader")
def initialize_app() -> None:
    # Load settings before doing work
    config_path = os.path.join(os.path.dirname(__file__), "trace_config.json")
    load_config_from_file(config_path)


@trace(target="Service")
def do_work(secret_data: Dict[str, str]) -> str:
    # If config loaded correctly, 'password' key should be masked with [HIDDEN_FROM_FILE]
    return "Work Done"


def main() -> None:
    # Initial state
    print(f"Initial mask value: {config.mask_value}")

    # Run initialization (traced)
    initialize_app()

    # Verify state change
    print(f"Updated mask value: {config.mask_value}")

    # Test trace with new config
    do_work({"username": "admin", "password": "super_secret_password"})


if __name__ == "__main__":
    main()
    print("Done! Check 'mermaid_diagrams/examples/config_loaded.mmd'.")
    print(
        "Verify that sensitive data is masked using the value from JSON: [HIDDEN_FROM_FILE]."
    )
