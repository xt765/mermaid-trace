import pytest
import asyncio
from mermaid_trace.core.decorators import trace, _resolve_target, _format_args
from unittest.mock import MagicMock, patch
from typing import Any

# --- Sync Tests ---

def test_trace_sync_basic(caplog: Any) -> None:
    @trace(source="User", target="System")
    def my_func(x: int) -> int:
        return x + 1
        
    res = my_func(1)
    assert res == 2
    
    # Verify logs
    assert len(caplog.records) >= 2
    req = caplog.records[0]
    resp = caplog.records[1]
    
    assert req.flow_event.source == "User"
    assert req.flow_event.target == "System"
    # Current implementation captures args as values in params string
    assert "1" in req.flow_event.params
    
    assert resp.flow_event.is_return is True
    assert resp.flow_event.result == "2"

def test_trace_sync_error(caplog: Any) -> None:
    @trace(source="A", target="B")
    def fail() -> None:
        raise ValueError("Boom")
        
    with pytest.raises(ValueError):
        fail()
        
    assert len(caplog.records) >= 2
    err_record = caplog.records[1]
    assert err_record.flow_event.is_error is True
    assert "Boom" in err_record.flow_event.error_message

def test_trace_method_inference(caplog: Any) -> None:
    class Service:
        @trace
        def run(self) -> None:
            pass
            
    s = Service()
    s.run()
    
    req = caplog.records[0]
    assert req.flow_event.target == "Service"

def test_resolve_target_class_method() -> None:
    class MyClass:
        pass
    
    # 1. Instance -> Class Name
    instance = MyClass()
    res = _resolve_target(lambda: None, (instance,), None)
    assert res == "MyClass"
    
    # 2. Class Type -> Class Name (e.g. @classmethod)
    res = _resolve_target(lambda: None, (MyClass,), None)
    assert res == "MyClass"

def test_resolve_target_module_fallback() -> None:
    def my_module_func() -> None: pass
    # When no args, should fallback to module name
    # We mock inspect.getmodule to return something
    with patch("inspect.getmodule") as mock_mod:
        mock_mod.return_value.__name__ = "my.package.module"
        res = _resolve_target(my_module_func, (), None)
        assert res == "module"

def test_resolve_target_primitive_first_arg() -> None:
    # If first arg is primitive, it shouldn't be treated as 'self'
    def func(x: Any) -> None: pass
    with patch("inspect.getmodule") as mock_mod:
        mock_mod.return_value.__name__ = "mod"
        res = _resolve_target(func, (123,), None)
        assert res == "mod"

def test_format_args_error_resilience() -> None:
    # Test that if repr raises, we don't crash
    bad_obj = MagicMock()
    # Need to patch reprlib.repr because _safe_repr uses it
    with patch("reprlib.repr", side_effect=Exception("Repr fail")):
        res = _format_args((bad_obj,), {})
        assert "<unrepresentable>" in res

# --- Async Tests ---

@pytest.mark.asyncio
async def test_trace_async_basic(caplog: Any) -> None:
    @trace(source="Client", target="AsyncSvc")
    async def run_async(v: int) -> int:
        await asyncio.sleep(0.01)
        return v * 2
        
    res = await run_async(5)
    assert res == 10
    
    assert len(caplog.records) >= 2
    req = caplog.records[0]
    assert req.flow_event.target == "AsyncSvc"
    resp = caplog.records[1]
    assert resp.flow_event.result == "10"
