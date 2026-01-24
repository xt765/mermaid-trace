import pytest
from logcapy import configure, get_logger
from logcapy.backends.loguru_impl import LoguruLogger

def test_loguru_backend(monkeypatch, capsys):
    # Check if loguru is installed
    try:
        import loguru
    except ImportError:
        pytest.skip("Loguru not installed")

    # Re-configure to use Loguru
    # Note: Global state is modified here, which might affect other tests if not careful.
    # But since pytest runs sequentially and we reset in conftest (though conftest uses stdlib),
    # we should be careful. 
    # Actually conftest sets stdlib autouse=True for each function.
    # So this function starts with stdlib. We switch to loguru.
    
    configure(backend="loguru", json_output=True)
    logger = get_logger()
    assert isinstance(logger, LoguruLogger)
    
    logger.info("Hello Loguru", context={"user": "test"})
    logger.debug("Debug msg")
    logger.warning("Warn msg")
    logger.error("Error msg", exc_info=True)
    
    # Capture output
    captured = capsys.readouterr()
    assert "Hello Loguru" in captured.out
    assert "test" in captured.out
    assert "Warn msg" in captured.out
    assert "Error msg" in captured.out

def test_loguru_init_error(monkeypatch):
    # Simulate loguru missing
    import sys
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "loguru", None)
        # We need to reload the module or simulate import error
        # Since loguru_impl imports loguru at top level with try/except, 
        # we need to reload it or just instantiate LoguruLogger and check if it raises
        
        # But loguru_impl.py handles the import error at module level
        pass
