from mermaid_trace import trace, configure_flow

# Configure output
configure_flow("error_trace.mmd")


class Database:
    @trace(target="Database")
    def connect(self) -> bool:
        # Simulate success
        return True

    @trace(target="Database")
    def query(self, sql: str) -> list[str]:
        if "syntax error" in sql:
            # Raising an exception will be captured by the @trace decorator
            # and rendered as an error return (x--).
            raise ValueError("Invalid SQL Syntax")
        return ["row1", "row2"]


class Service:
    def __init__(self) -> None:
        self.db = Database()

    @trace(source="Client", target="Service")
    def process_request(self, query_str: str) -> list[str]:
        self.db.connect()
        try:
            # If the called method raises an exception, it bubbles up here.
            # The diagram will show Service -> Database (Request) and Database --x Service (Error).
            return self.db.query(query_str)
        except ValueError as e:
            # We catch the error here, so the 'process_request' itself will return successfully (or return empty list).
            # The diagram will show Service -->> Client (Return).
            print(f"Caught error: {e}")
            return []


if __name__ == "__main__":
    svc = Service()

    print("Scenario 1: Success Flow")
    svc.process_request("SELECT * FROM users")

    print("\nScenario 2: Error Handling Flow")
    # This triggers the exception in Database.query
    svc.process_request("SELECT * FROM users WHERE syntax error")

    print("Done. Check 'error_trace.mmd' for the diagram.")
