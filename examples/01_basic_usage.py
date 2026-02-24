"""
Basic usage of MermaidTrace using decorators.
Demonstrates:
1. @trace on standalone functions
2. @trace on class methods
3. Context propagation (who called whom)
4. Data Masking (protect sensitive arguments)
"""

from mermaid_trace import trace, configure_flow
from mermaid_trace.core.config import config
import time
from typing import Any, Dict


# 1. Initialize the tracer. This creates 'mermaid_diagrams/examples/basic_flow.mmd'
configure_flow("mermaid_diagrams/examples/basic_flow.mmd")

# 2. Enable Data Masking
# Any argument named 'password' or key in a dict matching 'secret' will be masked.
config.mask_patterns = ["password", "secret", "token"]


class Database:
    @trace(target="DB", action="Query")
    def get_user(self, user_id: int) -> Dict[str, Any]:
        time.sleep(0.01)
        # Returning sensitive data in a dict
        return {"id": user_id, "name": "Alice", "secret_key": "xyz-123"}


class AuthService:
    def __init__(self) -> None:
        self.db = Database()

    @trace(target="AuthService", action="Login")
    def login(self, user_id: int, password: str) -> str:
        # The 'password' argument will be logged as '******' automatically
        # This call will be automatically traced as AuthService -> DB
        user = self.db.get_user(user_id)
        # The return value from DB contained 'secret_key', which will also be masked in the log
        return f"Welcome {user['name']}"


@trace(source="User", target="WebApp", action="Click Login")
def main() -> None:
    auth = AuthService()
    # This call will be traced as WebApp -> AuthService
    # We pass a real password, but it won't leak into the diagram file.
    auth.login(123, password="super_secret_password")


if __name__ == "__main__":
    print("Running basic example...")
    main()
    print("Done! Open 'basic_flow.mmd' to see the diagram.")
    print("Check the file content to verify 'password' and 'secret_key' are masked!")
