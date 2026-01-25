import unittest
import os
from mermaid_trace import trace_interaction, configure_flow

class TestFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.output_file = "test_flow.mmd"
        self.logger = configure_flow(self.output_file)

    def tearDown(self) -> None:
        # Close handlers to release file lock
        for handler in self.logger.handlers:
            handler.close()
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_trace_interaction(self) -> None:
        @trace_interaction(source="A", target="B", action="Action")
        def func() -> str:
            return "ok"
            
        func()
        
        with open(self.output_file, "r") as f:
            content = f.read()
            
        self.assertIn("sequenceDiagram", content)
        self.assertIn("A->>B: Action", content)
        self.assertIn("B-->>A: Return", content)

    def test_error_interaction(self) -> None:
        @trace_interaction(source="A", target="B", action="Fail")
        def fail() -> None:
            raise ValueError("oops")
            
        try:
            fail()
        except ValueError:
            pass
            
        with open(self.output_file, "r") as f:
            content = f.read()
            
        self.assertIn("B--xA: Error", content)
