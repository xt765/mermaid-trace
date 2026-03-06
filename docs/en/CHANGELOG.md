# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2026-03-06

### Changed
- **Dependencies**: FastAPI and Uvicorn are now required dependencies instead of optional. Users no longer need to install `mermaid-trace[server]` separately.
- **CLI Improvements**: Enhanced help messages with detailed descriptions, examples, and feature highlights (all in English).
- **Removed Legacy**: Completely removed the deprecated `--master` flag for cleaner CLI interface.

### Added
- **Offline Support**: Web preview server now uses local static resources (Tailwind CSS, Mermaid.js, svg-pan-zoom) instead of external CDN dependencies. The preview works completely offline without network connectivity.
- **Version Command**: Added `mermaid-trace version` command to display the installed version.
- **Browser Control**: Added `--no-browser` flag to prevent automatic browser opening when starting the server.

### Fixed
- **Installation Experience**: Resolved user confusion about needing to install optional dependencies separately. Now `pip install mermaid-trace` provides all features out of the box.

## [0.7.0] - 2026-02-24

### Added
- **Unified CLI**: Refactored the CLI to provide a unified experience. `mermaid-trace serve` now defaults to the enhanced Web preview server (Master mode) with hot-reload, pan/zoom, and directory browsing.
- **Single File Preview**: Added support for previewing single `.mmd` files with full Web UI capabilities.
- **Distributed Tracing Simulation**: Added `examples/10_distributed_trace_simulation.py` to demonstrate Trace Context propagation.
- **Custom Masking**: Added `examples/11_custom_masking.py` for advanced data sanitization.
- **Data Privacy**: Introduced `DataMasker` to automatically sanitize sensitive fields (e.g., `password`, `token`) in function arguments, return values, and dictionaries. Configurable via `config.mask_patterns`.
- **Sampling Strategy**: Added `config.sample_rate` to control the percentage of traces recorded, reducing overhead in high-throughput production environments.
- **Distributed Tracing**: Enhanced `FastAPI` middleware to support **W3C Trace Context**, **B3**, and custom `X-Trace-ID` headers, enabling cross-service trace propagation.
- **Context Management**: Added `is_sampled` state to `LogContext` to efficiently propagate sampling decisions across async call chains.

### Improved
- **Mermaid Rendering**: Fixed syntax errors caused by special characters (e.g., `<` , `>`) in Python object representations by implementing HTML entity escaping.
- **LangChain Integration**: Enhanced robustness of `examples/09_langchain_integration.py` to support mock execution without installed dependencies.
- **Test Suite**: Comprehensive update of the test suite, achieving **>90% coverage** with new tests for sanitization, sampling, and distributed tracing scenarios.
- **Documentation**: Updated READMEs and examples to showcase data masking, sampling features, and the new CLI usage.

### Fixed
- **Type Safety**: Resolved Mypy errors in `LogContext`, `server.py` and example scripts.

## [0.6.1] - 2026-02-02

### Fixed
- **Mypy Type Safety**: Fixed method signature for `MermaidTraceCallbackHandler.on_retriever_end` to align with `Sequence[Document]` from LangChain core, resolving Liskov Substitution Principle violations.
- **Example Code**: Improved type casting in the LangChain integration example for better compatibility in environments without optional dependencies.

### Improved
- **Documentation Sync**: Fully updated source code comments and documentation to reflect the latest API changes.

## [0.6.0] - 2026-02-02

### Added
- **Enhanced Web Preview (Master Mode)**: Introduced a brand-new FastAPI-powered Web preview interface.
  - **Interactive Rendering**: Integrated `mermaid.js` for real-time rendering with `svg-pan-zoom` support for zooming and panning.
  - **Real-time Sync**: Implemented Server-Sent Events (SSE) to automatically refresh diagrams when `.mmd` files change.
  - **Directory Browsing**: Built-in sidebar to browse and switch between all Mermaid files in the workspace.
  - **CLI Integration**: Simply launch with `mermaid-trace serve . --master`.

### Improved
- **Layout Optimization**: Refactored CSS Flex layout to fix vertical display issues for large diagrams.
- **Documentation**: Synchronized Master mode documentation and code comments across English and Chinese.

## [0.5.4] - 2026-02-02

### Added
- **LangChain Integration**: Full support for tracing LangChain applications.
  - **Callback Handler**: Implemented `MermaidTraceCallbackHandler` to capture lifecycle events for Chains, LLMs, ChatModels, Tools, and Retrievers.
  - **Participant Stack**: Introduced an internal participant stack to correctly track nested calls and return arrows (`-->>`) in complex RAG and Agent workflows.
  - **Robust Integration**: Used conditional imports to ensure `langchain-core` remains an optional dependency.

### Fixed
- **Empty File Issue**: Resolved a critical bug where `.mmd` files remained empty when using LangChain integration.
- **Protocol Alignment**: Fixed missing `flow_event` extra parameters in the callback handler to ensure correct event capturing by `MermaidFileHandler`.

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
