# 更新日志 (Changelog)

本项目的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵守 [Semantic Versioning](https://semver.org/lang/zh-CN/)（语义化版本控制）。

## [0.4.0] - 2026-01-26

### 新增
- **异步模式**: 在 `configure_flow` 中引入了 `async_mode=True`，将日志写入操作卸载到后台线程，消除了主应用程序循环中的 I/O 阻塞。
- **数据隐私**: 为 `@trace` 添加了 `capture_args=False`，以防止敏感参数被记录。
- **参数截断**: 为 `@trace` 添加了 `max_arg_length` 和 `max_arg_depth`，以控制记录的数据结构的大小。
- **显式命名**: 为 `@trace` 添加了 `name`（或 `target` 别名）参数，用于显式设置参与者名称，覆盖自动推断。
- **灵活配置**: 更新了 `configure_flow` 以接受自定义 Handler 列表和 `append` 标志，允许更好地与现有日志设置集成。

### 改进
- **测试覆盖率**: 实现了 >90% 的测试覆盖率，拥有覆盖单元、集成和并发场景的全面新测试套件。
- **PyPI 合规性**: 切换到通过 `hatch-vcs` 进行动态版本控制，并改进了包元数据和工件包含。

## [0.3.1] - 2026-01-26

### 修复
- **CI/CD**: 通过在所有工作流中统一使用可编辑安装 (`pip install -e .[dev]`)，解决了 GitHub Actions 中的测试覆盖率报告问题。
- **CI/CD**: 调整了 `pyproject.toml` 中的覆盖率配置，以正确指向源代码目录 (`src/mermaid_trace`)。
- **文档**: 修复了 README 中的徽章链接，使用了统一的样式和有效的来源。
- **兼容性**: 在项目分类器和 CI 工作流中正式添加了对 Python 3.13 和 3.14 的支持。

## [0.3.0] - 2026-01-26

### 新增
- **类型安全**：代码库全面覆盖类型注解（100% Mypy 覆盖率）。添加了 `watchdog` stubs 并修复了装饰器中的泛型类型。
- **稳健性**：增强了 `cli` 错误处理，修复了 `demo.py` 中的语法问题。
- **文档**：为核心模块（`Context`、`Events`、`Decorators`、`Handler`）添加了全面的英文 docstrings。

### 修复
- 修复了所有 linter 错误（Ruff），包括裸异常捕获和重定义。
- 解决了 `trace_interaction` 装饰器返回类型不稳定的问题。
- 修复了 README.md 和 README_CN.md 中的无效用法示例。

## [0.2.1] - 2026-01-26

### 改进
- **性能**：完全重构 `MermaidFileHandler`，使用标准缓冲和文件锁定，解决了高吞吐量场景下的严重 I/O 阻塞问题。
- **并发**：在 `LogContext` 和 `FlowEvent` 中引入 `Trace ID` 支持，以便在并发执行环境中正确跟踪和关联日志。
- **测试**：添加了覆盖率超过 90% 的全面测试套件，包括核心模块的单元测试以及 FastAPI 和 CLI 的集成测试。
- **文档**：更新了 API 参考和用户指南，以反映新的并发功能和 Trace ID 用法。

### 修复
- 修复了 `@trace` 无法在不带括号的情况下使用的问题。
- 修复了 `FastAPI` 中间件与新事件结构的兼容性。
- 修复了 CLI `serve` 命令以正确处理文件读取错误和依赖项缺失。

## [0.2.0] - 2026-01-26

### 重大转型：可视化优先
MermaidTrace 已从通用的日志包装器转型为专门的 **执行流可视化工具**。目标是直接从运行中的 Python 代码生成 Mermaid 时序图。

### 新增
- **`@trace` 装饰器**：自动记录函数调用为时序交互。支持捕获参数和返回值。
- **上下文推断**：使用 `contextvars` 自动检测 `source`（源）参与者，无需手动连线即可实现嵌套调用可视化。
- **Mermaid 处理器**：专门的日志处理器，实时写入 `.mmd` 文件。
- **CLI 工具**：添加了 `mermaid-trace serve <file.mmd>` 命令，可在浏览器中预览生成的图表。
- **FastAPI 中间件**：`MermaidTraceMiddleware` for zero-config HTTP request tracing.
- **数据捕获**：支持在图表中捕获并显示函数参数和返回值。

### 移除
- **旧版后端**：移除了通用的 `StandardLogger` 和 `LoguruLogger` 包装器。
- **旧版集成**：移除了旧的 Flask/Django 集成（由专注于流程可视化的中间件取代）。
- **JSON 格式化器**：移除，改为 Mermaid 格式输出。

### 变更
- **包元数据**：更新了 `pyproject.toml` 的关键字、描述和分类器以反映新重心。

## [0.1.0] - 2026-01-24

### 新增
- 旧版日志包装器的初始版本（现已被 v0.2.0 取代）。
