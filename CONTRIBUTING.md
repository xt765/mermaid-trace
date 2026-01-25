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
    pytest
    ```

## Styleguides

### Python Styleguide

- All Python code is linted with `ruff`.
- All Python code is type-checked with `mypy`.

To run checks locally:

```bash
ruff check src tests
mypy src
```

## Pull Requests

1.  Ensure all tests pass.
2.  Add new tests for new features.
3.  Update documentation if public API changes.
4.  Write a clear description of the changes.

## Code of Conduct

Please be respectful and considerate of others. Harassment or abuse of any kind will not be tolerated.
