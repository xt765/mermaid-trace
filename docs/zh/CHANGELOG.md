# 更新日志 (Changelog)

本项目的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵守 [Semantic Versioning](https://semver.org/lang/zh-CN/)（语义化版本控制）。

## [0.2.0] - 2026-01-26

### 重大转型：可视化优先
MermaidTrace 已从通用的日志包装器转型为专门的 **执行流可视化工具**。目标是直接从运行中的 Python 代码生成 Mermaid 时序图。

### 新增
- **`@trace` 装饰器**：自动记录函数调用为时序交互。支持捕获参数和返回值。
- **上下文推断**：使用 `contextvars` 自动检测 `source`（源）参与者，无需手动连线即可实现嵌套调用可视化。
- **Mermaid 处理器**：专门的日志处理器，实时写入 `.mmd` 文件。
- **CLI 工具**：添加了 `mermaid-trace serve <file.mmd>` 命令，可在浏览器中预览生成的图表。
- **FastAPI 中间件**：`MermaidTraceMiddleware`，用于零配置 HTTP 请求追踪。
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
