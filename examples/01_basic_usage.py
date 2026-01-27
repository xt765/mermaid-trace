"""
Basic usage of MermaidTrace using decorators.
Demonstrates:
1. @trace on standalone functions
2. @trace on class methods
3. Context propagation (who called whom)
"""

from mermaid_trace import trace, configure_flow
import time
from typing import Any, Dict


# 1. Initialize the tracer. This creates 'mermaid_diagrams/examples/basic_flow.mmd'
configure_flow("mermaid_diagrams/examples/basic_flow.mmd")


class Database:
    @trace(target="DB", action="Query")
    def get_user(self, user_id: int) -> Dict[str, Any]:
        time.sleep(0.01)
        return {"id": user_id, "name": "Alice"}


class AuthService:
    def __init__(self) -> None:
        self.db = Database()

    @trace(target="AuthService", action="Login")
    def login(self, user_id: int) -> str:
        # This call will be automatically traced as AuthService -> DB
        user = self.db.get_user(user_id)
        return f"Welcome {user['name']}"


@trace(source="User", target="WebApp", action="Click Login")
def main() -> None:
    auth = AuthService()
    # This call will be traced as WebApp -> AuthService
    auth.login(123)


if __name__ == "__main__":
    print("Running basic example...")
    main()
    print("Done! Open 'basic_flow.mmd' to see the diagram.")
