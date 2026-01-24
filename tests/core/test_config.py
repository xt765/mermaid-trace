import pytest
from logcapy import configure, get_logger
from logcapy.backends.stdlib import StandardLogger

def test_config_defaults():
    configure(backend="stdlib")
    logger = get_logger()
    assert isinstance(logger, StandardLogger)

def test_config_invalid_backend():
    with pytest.raises(ValueError):
        configure(backend="invalid")
