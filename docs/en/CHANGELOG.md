# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
