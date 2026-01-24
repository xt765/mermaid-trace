# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-24

### Added
- **Core**:
    - `@catch` decorator for automatic exception handling and logging.
    - `@retry` decorator for robust retry mechanisms with exponential backoff.
    - `LogContext` using `contextvars` for thread-safe and async-safe context tracking.
- **Backends**:
    - `StandardLogger` adapter for Python's built-in `logging` module.
    - `LoguruLogger` adapter for `loguru` integration.
    - JSON formatter for structured logging output.
- **Integrations**:
    - `FastAPI` middleware for Request ID and context capturing.
    - `Flask` extension for request context management.
    - `Django` middleware for request context management.
- **Documentation**:
    - Comprehensive README in English and Chinese.
    - Sphinx documentation structure.
    - Contributing guidelines.
- **CI/CD**:
    - GitHub Actions workflows for testing and PyPI publishing.

### Security
- No known security issues.
