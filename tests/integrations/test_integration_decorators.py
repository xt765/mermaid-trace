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
    with patch("inspect.getmodule") as mock_mod:
        mock_mod.return_value.__name__ = "my.package.module"
        res = _resolve_target(my_module_func, (), None)
        assert res == "module"

def test_resolve_target_primitive_first_arg() -> None:
    def func(x: Any) -> None: pass
    with patch("inspect.getmodule") as mock_mod:
        mock_mod.return_value.__name__ = "mod"
        res = _resolve_target(func, (123,), None)
        assert res == "mod"

def test_format_args_error_resilience() -> None:
    bad_obj = MagicMock()
    # Patch Repr.repr instead of reprlib.repr
    with patch("reprlib.Repr.repr", side_effect=Exception("Repr fail")):
        res = _format_args((bad_obj,), {})
        assert "<unrepresentable>" in res

def test_trace_async_error(caplog: Any) -> None:
    @trace(source="A", target="B")
    async def fail_async() -> None:
        raise ValueError("AsyncBoom")
        
    with pytest.raises(ValueError):
        asyncio.run(fail_async())
        
    assert len(caplog.records) >= 2
    err_record = caplog.records[1]
    assert err_record.flow_event.is_error is True
    assert "AsyncBoom" in err_record.flow_event.error_message

# --- New Features Tests ---

def test_capture_args_false(caplog: Any) -> None:
    @trace(capture_args=False)
    def secret_func(pwd: str) -> str:
        return "hidden"
        
    secret_func("secret")
    
    req = caplog.records[0]
    resp = caplog.records[1]
    
    assert req.flow_event.params == ""
    assert resp.flow_event.result == ""
    assert "secret" not in str(req.flow_event)
    assert "hidden" not in str(resp.flow_event)

def test_max_arg_length(caplog: Any) -> None:
    @trace(max_arg_length=5)
    def long_func(arg: str) -> str:
        return arg
        
    long_func("1234567890")
    
    req = caplog.records[0]
    # "1234567890" -> "12345..." (actually reprlib might add quotes)
    # _safe_repr uses reprlib.repr which limits length.
    # repr('1234567890') is "'1234567890'" (len 12)
    # max_len=5 -> "'123..." + "..."
    
    assert "..." in req.flow_event.params
    assert len(req.flow_event.params) < 20 # Conservative check

def test_explicit_name_alias(caplog: Any) -> None:
    @trace(name="MyAlias")
    def func(): pass
    
    func()
    assert caplog.records[0].flow_event.target == "MyAlias"

def test_explicit_action(caplog: Any) -> None:
    @trace(action="CustomAction")
    def func(): pass
    
    func()
    assert caplog.records[0].flow_event.action == "CustomAction"

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
