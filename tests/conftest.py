import pytest
import logging
from logcapy import configure
from logcapy.core.context import LogContext

@pytest.fixture(autouse=True)
def setup_logcapy():
    configure(backend="stdlib", json_output=True)
    LogContext.clear()
    yield
    LogContext.clear()
