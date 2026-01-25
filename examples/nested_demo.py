from mermaid_trace import trace, configure_flow, LogContext
import time

# Configure output
configure_flow("nested_flow.mmd")

# Simulate a class-based service
class PaymentService:
    @trace(action="Process Payment")
    def process(self, amount):
        print(f"Processing ${amount}")
        self.check_fraud(amount)
        Database().save("Payment", amount)
        return "Success"

    @trace(action="Fraud Check")
    def check_fraud(self, amount):
        # Nested call within same service
        return True

class Database:
    @trace(action="Insert Record")
    def save(self, table, data):
        time.sleep(0.01)
        return "Saved"

# Entry point
@trace(source="Client", target="API", action="Start Request")
def main():
    # Set initial context manually if needed, or let the first decorator handle it
    # Here, 'main' sets source=Client, target=API.
    # So inside main, current participant is 'API'.
    
    svc = PaymentService()
    # When svc.process is called:
    # source = API (from context)
    # target = PaymentService (inferred from class)
    svc.process(100)

if __name__ == "__main__":
    main()
