# LogCapy 功能扩展计划：参数捕获、CLI 预览与 FastAPI 集成

## 1. 阶段一：数据捕获增强 (显示参数与返回值)

**目标**：让时序图不仅仅显示“发生了什么”，还能显示“数据是什么”（例如参数和返回值）。

*   **修改 `FlowEvent` 模型**：
    *   增加 `params` (str) 和 `result` (str) 字段。
*   **升级 `@trace` 装饰器**：
    *   在函数调用前，捕获 `args` 和 `kwargs`，将其转换为字符串（支持截断，防止日志过大）。
    *   在函数返回后，捕获返回值。
*   **优化 Mermaid 输出**：
    *   请求线：显示 `Action(param1=val1, ...)`。
    *   返回线：显示 `Return: result_value`。

## 2. 阶段二：Web 预览 CLI (`logcapy serve`)

**目标**：提供一个开箱即用的命令，无需安装 IDE 插件即可在浏览器中查看实时更新的时序图。

*   **创建 CLI 模块 (`src/logcapy/cli.py`)**：
    *   基于 `http.server` 实现一个轻量级静态服务器。
    *   提供 HTML 模板，通过 CDN 引入 Mermaid.js 库。
    *   实现自动刷新逻辑（可选 MVP：手动刷新）。
*   **注册命令**：
    *   在 `pyproject.toml` 中添加 `[project.scripts]`，注册 `logcapy` 命令。
*   **使用方式**：
    *   用户运行 `logcapy serve flow.mmd`，浏览器自动打开 `http://localhost:8000` 查看图表。

## 3. 阶段三：FastAPI 集成支持

**目标**：为 FastAPI 应用提供“零配置”的请求追踪能力。

*   **新建集成模块 (`src/logcapy/integrations/fastapi.py`)**：
    *   实现 `LogCapyMiddleware`。
*   **中间件逻辑**：
    *   自动拦截所有 HTTP 请求。
    *   **Source**: 默认为 `Client` 或从 `User-Agent`/`X-Source` 头读取。
    *   **Target**: 默认为 `FastAPI` 或应用 Title。
    *   **Action**: 使用 `request.method + request.url.path` (例如 `GET /users/1`)。
    *   **Context**: 自动初始化 `LogContext`，确保后续 Service 层的调用能正确串联。

## 执行顺序

我们将按照 **阶段一 -> 阶段二 -> 阶段三** 的顺序执行，每完成一个阶段都会进行验证。
