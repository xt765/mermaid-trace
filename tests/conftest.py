import pytest
import logging

@pytest.fixture(autouse=True)
def configure_caplog(caplog):
    """
    Ensure caplog captures INFO logs from mermaid_trace.
    By default caplog only captures WARNING and above.
    """
    caplog.set_level(logging.INFO, logger="mermaid_trace.flow")
