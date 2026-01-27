# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.3] - 2026-01-27

### Added
- **Log Rotation**: Introduced `RotatingMermaidFileHandler` and `TimedRotatingMermaidFileHandler` to handle long-running systems by automatically splitting `.mmd` files based on size or time.
- **Overwrite Support**: Added `overwrite` parameter to `configure_flow` to allow clearing the diagram file on application restart.

### Improved
- **Documentation**: Comprehensive update of English and Chinese documentation, including User Guide, API Reference, and detailed source code annotations.
- **Examples**: Added a new example `08-log-rotation.py` demonstrating production-ready log rotation configurations.

## [0.5.2] - 2026-01-27

### Added
- **List/Tuple Item Grouping**: Consecutive identical items in lists and tuples are now automatically grouped (e.g., `['a', 'a', 'a']` -> `['a' x 3]`), significantly reducing visual noise in diagrams when dealing with large collections of similar objects.

### Improved
- **Test Coverage**: Increased test coverage to **96.22%** by adding comprehensive test cases for edge cases in CLI, decorators, and handlers.
- **Robustness**: Improved CLI error handling and live reload stability by fixing mock handling and ensuring proper cleanup.
- **Documentation**: Synchronized all documentation across languages and updated comprehensive Chinese source code annotations for all modules.

## [0.5.0] - 2026-01-27

### Added
- **Intelligent Collapsing**: Repetitive high-frequency calls are now automatically collapsed into a single arrow with a counter (e.g., `func (x10)`), preventing diagram bloat.
- **Auto-Instrumentation**: Added `@trace_class` decorator to automatically trace all public methods in a class.
- **Third-Party Patching**: Added `patch_object` utility to trace methods in external libraries (e.g., `requests.get`) without modifying their source.
- **Global Configuration**: Introduced `MermaidConfig` system allowing global control over parameter capture, string limits, and recursion depth via code or environment variables.
- **Full Stack Trace Capture**: Exceptions now capture the complete Python traceback, displayed as a Note in the Mermaid diagram for easier debugging.

### Changed
- **`configure_flow` API**: Updated to support `level`, `config_overrides`, and `queue_size` for more flexible initialization.
- **Enhanced FastAPI Integration**: The middleware now captures and logs full stack traces for unhandled exceptions.

### Improved
- **Documentation**: Added comprehensive Chinese source code annotations for all modules.
- **Test Coverage**: Maintained >93% coverage with new tests for collapsing and configuration logic.

## [0.4.2] - 2026-01-27

### Fixed
- **Lazy Loading**: Fixed `MermaidFileHandler` to respect `delay=True`. File is now only created when the first log event is emitted, preventing empty files from being created unnecessarily.
- **Naming Collisions**: Fixed `MermaidFormatter._sanitize` to handle naming collisions robustly (e.g., `User A` vs `User-A`) by ensuring unique Mermaid IDs.

### Improved
- **Code Cleanup**: Removed redundant getter methods in `Event` and `FlowEvent` in favor of Pythonic attribute access.
- **Handler SRP**: Decoupled Mermaid header generation from `MermaidFileHandler` by moving logic to `MermaidFormatter.get_header()`.

## [0.4.1] - 2026-01-26

### Added
- **Abstract Event Model**: Introduced `Event` abstract base class and `BaseFormatter` interface for better extensibility and support for multiple output formats.
- **Enhanced Async Handler**: Added queue size limit (`queue_size=1000`) with drop policy to prevent memory overflow in high-traffic scenarios.
- **Improved Exception Handling**: Enhanced exception logging to include full stack traces and error details.

### Fixed
- **Context Loss Issue**: Fixed `LogContext._get_store()` method to properly initialize `contextvar` when no context exists, preventing subsequent `LookupError` exceptions.
- **Concurrency Safety**: Added thread locks in `MermaidFileHandler._write_header()` to prevent race conditions when writing file headers with `delay=True`.

### Improved
- **Architecture Design**: Decoupled components by introducing abstract interfaces, reducing tight coupling between `FlowEvent` and Mermaid-specific formatting.
- **Test Coverage**: Increased test coverage to 90.17% by adding comprehensive test cases for the new abstract classes.
- **Code Maintainability**: Added detailed English annotations to all code files, improving readability and developer experience.

## [0.4.0] - 2026-01-26

### Added
- **Async Mode**: Introduced `async_mode=True` in `configure_flow` to offload log writing to a background thread, eliminating I/O blocking in the main application loop.
- **Data Privacy**: Added `capture_args=False` to `@trace` to prevent sensitive arguments from being logged.
- **Argument Truncation**: Added `max_arg_length` and `max_arg_depth` to `@trace` to control the size of logged data structures.
- **Explicit Naming**: Added `name` (or `target` alias) parameter to `@trace` for explicitly setting the participant name, overriding automatic inference.
- **Flexible Configuration**: Updated `configure_flow` to accept a list of custom handlers and an `append` flag, allowing better integration with existing logging setups.

### Improved
- **Test Coverage**: Achieved >90% test coverage with a comprehensive new test suite covering unit, integration, and concurrency scenarios.
- **PyPI Compliance**: Switched to dynamic versioning via `hatch-vcs` and improved package metadata and artifact inclusion.

## [0.3.1] - 2026-01-26

### Fixed
- **CI/CD**: Resolved test coverage reporting issues in GitHub Actions by standardizing on editable installs (`pip install -e .[dev]`) across all workflows.
- **CI/CD**: Aligned coverage configuration in `pyproject.toml` to correctly target the source directory (`src/mermaid_trace`).
- **Docs**: Fixed badge links in README to use consistent style and valid sources.
- **Compatibility**: Officially added support for Python 3.13 and 3.14 in project classifiers and CI workflows.

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
