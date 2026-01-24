# 更新日志

本项目的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵守 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [0.1.0] - 2026-01-24

### 新增
- **核心功能**:
    - `@catch` 装饰器，用于自动异常处理和日志记录。
    - `@retry` 装饰器，提供带有指数退避的健壮重试机制。
    - `LogContext` 使用 `contextvars` 实现线程安全和异步安全的上下文追踪。
- **后端适配**:
    - `StandardLogger` 适配器，用于集成 Python 内置的 `logging` 模块。
    - `LoguruLogger` 适配器，用于集成 `loguru`。
    - JSON 格式化器，用于结构化日志输出。
- **集成**:
    - `FastAPI` 中间件，用于 Request ID 和上下文捕获。
    - `Flask` 扩展，用于请求上下文管理。
    - `Django` 中间件，用于请求上下文管理。
- **文档**:
    - 完整的中英文 README。
    - Sphinx 文档结构。
    - 贡献指南。
- **CI/CD**:
    - 用于测试和 PyPI 发布的 GitHub Actions 工作流。

### 安全
- 无已知安全问题。
