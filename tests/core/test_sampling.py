"""
Tests for Sampling Logic in Decorators and Context.
"""

from unittest.mock import patch
from mermaid_trace import trace
from mermaid_trace.core.config import config
from mermaid_trace.core.context import LogContext
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware


# 1. Test Decorator Sampling
def test_decorator_sampling(caplog):
    # Setup
    caplog.clear()

    @trace
    def sampled_func():
        return "ok"

    # Case 1: Sample Rate = 0.0 (Never sample)
    with patch.object(config, "sample_rate", 0.0):
        # Reset trace_id to ensure new root span logic triggers
        token = LogContext.set_all({})
        try:
            sampled_func()
            records = [r for r in caplog.records if hasattr(r, "flow_event")]
            assert len(records) == 0
            # Verify context was set correctly even if not logged
            # But context is scoped, so it's gone after func returns.
            # We can check inside the function if we modify it, but let's trust logic for now.
        finally:
            LogContext.reset(token)

    # Case 2: Sample Rate = 1.0 (Always sample)
    caplog.clear()
    with patch.object(config, "sample_rate", 1.0):
        token = LogContext.set_all({})
        try:
            sampled_func()
            records = [r for r in caplog.records if hasattr(r, "flow_event")]
            assert len(records) == 2  # Call + Return
            assert records[0].flow_event.action == "Sampled Func"
        finally:
            LogContext.reset(token)


def test_decorator_sampling_inheritance(caplog):
    # Test that child calls inherit parent's sampling decision
    caplog.clear()

    @trace
    def child():
        return "child"

    @trace
    def parent():
        return child()

    # Force parent to NOT sample
    # We simulate this by setting sample_rate=0.0
    with patch.object(config, "sample_rate", 0.0):
        token = LogContext.set_all({})
        try:
            parent()
            records = [r for r in caplog.records if hasattr(r, "flow_event")]
            assert len(records) == 0  # Neither parent nor child logged
        finally:
            LogContext.reset(token)


# 2. Test FastAPI Middleware Sampling
def test_middleware_sampling(caplog):
    app = FastAPI()
    app.add_middleware(MermaidTraceMiddleware, app_name="SampleApp")

    @app.get("/")
    def root():
        return {"msg": "ok"}

    client = TestClient(app)

    # Case 1: Sample Rate = 0.0
    caplog.clear()
    with patch.object(config, "sample_rate", 0.0):
        client.get("/")
        records = [r for r in caplog.records if hasattr(r, "flow_event")]
        assert len(records) == 0

    # Case 2: Sample Rate = 1.0
    caplog.clear()
    with patch.object(config, "sample_rate", 1.0):
        client.get("/")
        records = [r for r in caplog.records if hasattr(r, "flow_event")]
        assert len(records) >= 2  # Request + Response
