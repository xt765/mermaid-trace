# Contributing to MermaidTrace

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to MermaidTrace and its packages. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Development Setup

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/xt765/mermaid-trace.git
    cd mermaid-trace
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    # Install package in editable mode with dev dependencies
    pip install -e .[dev]
    ```

4.  **Run tests**:
    ```bash
    # Run all tests
    pytest

    # Run tests across multiple Python versions (requires tox)
    pip install tox
    tox
    ```

## Styleguides

### Python Styleguide

- All Python code is linted with `ruff`.
- All Python code is type-checked with `mypy`.
- We use `hatch` for build management and `hatch-vcs` for dynamic versioning.

To run checks locally:

```bash
# Using tox (recommended)
tox -e lint

# Or manually
ruff check src tests
mypy src/mermaid_trace
```

## Pull Requests

1.  Ensure all tests pass.
2.  Add new tests for new features.
3.  Update documentation if public API changes.
4.  Write a clear description of the changes.

## Code of Conduct

Please be respectful and considerate of others. Harassment or abuse of any kind will not be tolerated.
