import pytest
import logging
from pathlib import Path
from typing import Any


@pytest.fixture(autouse=True)
def configure_caplog(caplog: Any) -> None:
    """
    Ensure caplog captures INFO logs from mermaid_trace.
    By default caplog only captures WARNING and above.
    """
    caplog.set_level(logging.INFO, logger="mermaid_trace.flow")


@pytest.fixture
def diagram_output_dir(request: Any) -> Path:
    """
    Returns a directory in mermaid_diagrams/tests corresponding to the test file.
    """
    # Get the relative path of the test file from the tests/ directory
    test_file = Path(request.fspath)
    try:
        rel_path = test_file.relative_to(Path(__file__).parent)
    except ValueError:
        rel_path = Path(test_file.name)

    # Create the output directory: mermaid_diagrams/tests/<subdir>/<test_file_name_without_test_>
    parts = list(rel_path.parts)
    # Remove 'test_' prefix and '.py' extension from the last part
    parts[-1] = parts[-1].replace("test_", "").replace(".py", "")

    output_dir = (
        Path(__file__).parent.parent / "mermaid_diagrams" / "tests" / Path(*parts)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
