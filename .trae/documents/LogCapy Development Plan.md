# LogCapy Development Plan

I have designed a comprehensive architecture for `LogCapy`, a Python library integrating robust exception handling with structured logging.

## Phase 1: Project Scaffolding & Configuration
1.  **Initialize Project Structure**: Create the directory layout strictly following the architecture design (src-layout).
2.  **Configuration**: Create `pyproject.toml` using `hatchling` as the build backend, defining dependencies (optional `loguru`, `fastapi`, etc.), and configuring tools (`ruff`, `mypy`, `pytest`).
3.  **Git Setup**: Initialize git, create `.gitignore` and `LICENSE`.

## Phase 2: Core Implementation
1.  **Context Management**: Implement `src/logcapy/core/context.py` using `contextvars` to handle thread-safe and async-safe context (e.g., Request IDs).
2.  **Logging Backends**:
    *   Define `LoggerBackend` protocol in `src/logcapy/backends/base.py`.
    *   Implement `StandardLogger` (stdlib logging) with JSON formatting support.
    *   Implement `LoguruLogger` (optional adapter).
3.  **Configuration System**: Implement `src/logcapy/config.py` to manage global settings and backend selection.

## Phase 3: Decorators & Exception Handling
1.  **Smart Decorators**: Implement `src/logcapy/core/decorators.py` containing:
    *   `@catch`: Automatically captures exceptions, extracts context (args, stack trace), and logs them. Supports async/sync detection.
    *   `@retry`: Implements retry logic with exponential backoff.
2.  **Context Managers**: Ensure the logic in decorators is reusable as context managers (`with logcapy.catch():`).

## Phase 4: Framework Integrations
1.  **FastAPI/Starlette**: Implement `LogCapyMiddleware` to automatically capture Request ID, User Agent, and handle unhandled exceptions.
2.  **Flask**: Implement a Flask extension for similar functionality.
3.  **Django**: Implement a Django Middleware.

## Phase 5: Testing & CI/CD
1.  **Test Suite**: Write comprehensive tests using `pytest` and `pytest-asyncio` covering:
    *   Unit tests for decorators (sync/async).
    *   Integration tests for logging backends.
    *   Middleware tests using `TestClient`.
2.  **CI/CD**: Create `.github/workflows/ci.yml` for automated testing, linting, and type checking.

## Phase 6: Documentation & Release
1.  **Documentation**: Initialize Sphinx docs in `docs/` with API references and usage examples.
2.  **Build**: Verify the package build process.

I will start by executing Phase 1 and 2.