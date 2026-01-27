import pytest
import asyncio
from mermaid_trace.core.utils import trace_class, patch_object


def test_trace_class_async_methods(caplog):
    @trace_class
    class AsyncTraced:
        async def async_method(self):
            return "async_result"

    async def run_test():
        obj = AsyncTraced()
        await obj.async_method()

    asyncio.run(run_test())

    assert len(caplog.records) >= 2
    actions = [r.flow_event.action for r in caplog.records]
    assert "Async Method" in actions


def test_trace_class_as_function(caplog):
    class ManualTrace:
        def method(self):
            pass

    # Apply manually
    TracedClass = trace_class(ManualTrace)
    obj = TracedClass()
    obj.method()

    assert len(caplog.records) >= 2
    actions = [r.flow_event.action for r in caplog.records]
    assert "Method" in actions


def test_trace_class_exclude(caplog):
    @trace_class(exclude=["ignored"])
    class Excluded:
        def kept(self):
            pass

        def ignored(self):
            pass

    obj = Excluded()
    obj.kept()
    obj.ignored()

    # Should trace kept, but not ignored
    # kept: 2 events (req/resp)
    # ignored: 0 events
    assert len(caplog.records) == 2
    assert "Kept" in caplog.records[0].flow_event.action


def test_trace_class_no_args_decorator(caplog):
    # Test @trace_class() instead of @trace_class
    @trace_class()
    class EmptyArgs:
        def method(self):
            pass

    obj = EmptyArgs()
    obj.method()
    assert len(caplog.records) >= 2


def test_trace_class_setattr_failure():
    # Create a class where setting attributes fails
    class NoSetAttrMeta(type):
        def __setattr__(cls, name, value):
            if name == "method":
                raise TypeError("ReadOnly")
            super().__setattr__(name, value)

    class Protected(metaclass=NoSetAttrMeta):
        def method(self):
            pass

        def other(self):
            pass

    # Should not raise exception, just skip 'method'
    trace_class(Protected)

    # Verify 'other' was traced (it became a wrapper)
    # But 'method' should remain original function (or at least no error raised)
    # Since we can't inspect the wrapper easily without calling it,
    # we just ensure no exception was raised during decoration.
    pass


def test_patch_object_success(caplog):
    class API:
        def fetch(self):
            return "data"

    api = API()
    patch_object(api, "fetch", action="FetchData")

    api.fetch()

    assert len(caplog.records) >= 2
    assert caplog.records[0].flow_event.action == "FetchData"


def test_patch_object_missing_attribute():
    class Target:
        pass

    with pytest.raises(AttributeError, match="has no attribute 'missing'"):
        patch_object(Target(), "missing")
