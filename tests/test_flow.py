import unittest
import os
import logging
from mermaid_trace import trace_interaction, configure_flow
from mermaid_trace.core.events import FlowEvent

class TestFlow(unittest.TestCase):
    def setUp(self):
        self.output_file = "test_flow.mmd"
        self.logger = configure_flow(self.output_file)

    def tearDown(self):
        # Close handlers to release file lock
        for handler in self.logger.handlers:
            handler.close()
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_trace_interaction(self):
        @trace_interaction("A", "B", "Action")
        def func():
            return "ok"
            
        func()
        
        with open(self.output_file, "r") as f:
            content = f.read()
            
        self.assertIn("sequenceDiagram", content)
        self.assertIn("A->>B: Action", content)
        self.assertIn("B-->>A: Return", content)

    def test_error_interaction(self):
        @trace_interaction("A", "B", "Fail")
        def fail():
            raise ValueError("oops")
            
        try:
            fail()
        except ValueError:
            pass
            
        with open(self.output_file, "r") as f:
            content = f.read()
            
        self.assertIn("B--xA: Error", content)
