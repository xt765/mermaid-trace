# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-01-26

### Fixed
- **CI/CD**: Resolved test coverage reporting issues in GitHub Actions by standardizing on editable installs (`pip install -e .[dev]`) across all workflows.
- **CI/CD**: Aligned coverage configuration in `pyproject.toml` to correctly target the source directory (`src/mermaid_trace`).
- **Docs**: Fixed badge links in README to use consistent style and valid sources.

## [0.3.0] - 2026-01-26

### Added
- **Type Safety**: Full type annotations across the codebase (100% Mypy coverage). Added `watchdog` stubs and fixed generic types in decorators.
- **Robustness**: Enhanced `cli` error handling and fixed syntax issues in `demo.py`.
- **Documentation**: Added comprehensive English docstrings to core modules (`Context`, `Events`, `Decorators`, `Handler`).

### Fixed
- Fixed all linter errors (Ruff) including bare exceptions and redefinitions.
- Resolved type instability in `trace_interaction` decorator return types.
- Fixed invalid usage examples in README.md and README_CN.md.

## [0.2.1] - 2026-01-26

### Improved
- **Performance**: Completely refactored `MermaidFileHandler` to use standard buffering and file locking, resolving severe I/O blocking issues in high-throughput scenarios.
- **Concurrency**: Introduced `Trace ID` support in `LogContext` and `FlowEvent` to correctly track and correlate logs in concurrent execution environments.
- **Testing**: Added a comprehensive test suite with over 90% code coverage, including unit tests for core modules and integration tests for FastAPI and CLI.
- **Documentation**: Updated API Reference and User Guide to reflect new concurrency features and Trace ID usage.

### Fixed
- Fixed a bug where `@trace` could not be used without parentheses.
- Fixed `FastAPI` middleware compatibility with new event structure.
- Fixed CLI `serve` command to properly handle file read errors and missing dependencies.

## [0.2.0] - 2026-01-26

### Major Pivot: Visualization First
MermaidTrace has pivoted from a general-purpose logging wrapper to a specialized **Execution Flow Visualizer**. The goal is to generate Mermaid Sequence Diagrams directly from running Python code.

### Added
- **`@trace` Decorator**: Automatically logs function calls as sequence interactions. Supports capturing arguments and return values.
- **Context Inference**: Automatic detection of `source` participants using `contextvars`, enabling nested call visualization without manual wiring.
- **Mermaid Handler**: A specialized logging handler that writes `.mmd` files in real-time.
- **CLI Tool**: Added `mermaid-trace serve <file.mmd>` command to preview generated diagrams in the browser.
- **FastAPI Middleware**: `MermaidTraceMiddleware` for zero-config HTTP request tracing.
- **Data Capture**: Support for capturing and displaying function arguments and return values in diagrams.

### Removed
- **Legacy Backends**: Removed generic `StandardLogger` and `LoguruLogger` wrappers.
- **Legacy Integrations**: Removed old Flask/Django integrations (replaced by flow-focused middleware).
- **JSON Formatter**: Removed in favor of Mermaid format output.

### Changed
- **Package Metadata**: Updated `pyproject.toml` keywords, description, and classifiers to reflect the new focus.

## [0.1.0] - 2026-01-24

### Added
- Initial release of the legacy logging wrapper (now superseded by v0.2.0).
