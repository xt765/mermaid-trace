from mermaid_trace.core.utils import trace_class, patch_object


def test_trace_class_decorator(caplog):
    @trace_class
    class AutoTraced:
        def method_a(self):
            return "a"

        def method_b(self):
            return "b"

        def _private(self):
            pass

    obj = AutoTraced()
    obj.method_a()
    obj.method_b()
    obj._private()

    # Should trace method_a and method_b
    assert len(caplog.records) >= 4  # 2 req + 2 resp

    targets = [
        r.flow_event.action for r in caplog.records if not r.flow_event.is_return
    ]
    assert "Method A" in targets
    assert "Method B" in targets

    # _private should NOT be traced by default
    assert " Private" not in targets


def test_trace_class_with_args(caplog):
    @trace_class(capture_args=False, include_private=True)
    class ConfigTraced:
        def method(self, secret):
            pass

        def _hidden(self):
            pass

    obj = ConfigTraced()
    obj.method("secret")
    obj._hidden()

    assert len(caplog.records) >= 4

    # Check capture_args=False
    req = caplog.records[0]
    assert req.flow_event.params == ""

    # Check include_private=True
    actions = [r.flow_event.action for r in caplog.records]
    assert " Hidden" in actions


def test_patch_object(caplog):
    class ThirdParty:
        def api_call(self):
            return "data"

    lib = ThirdParty()

    # Patch it
    patch_object(lib, "api_call", action="Patched API")

    lib.api_call()

    assert len(caplog.records) >= 2
    assert caplog.records[0].flow_event.action == "Patched API"
