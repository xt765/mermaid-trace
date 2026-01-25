# 贡献指南

首先，感谢您抽出时间为 MermaidTrace 做出贡献！🎉

以下是为 MermaidTrace 及其相关包做贡献的一套指南。这些大多是建议而非硬性规定。请运用您的最佳判断，并随时通过 Pull Request 建议更改本文档。

## 开发环境设置

1.  **克隆仓库**：
    ```bash
    git clone https://github.com/xt765/mermaid-trace.git
    cd mermaid-trace
    ```

2.  **创建虚拟环境**（推荐）：
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **安装依赖**：
    ```bash
    # 以可编辑模式安装包及其开发依赖
    pip install -e .[dev]
    ```

4.  **运行测试**：
    ```bash
    pytest
    ```

## 代码风格指南

### Python 风格指南

- 所有 Python 代码均使用 `ruff` 进行 lint 检查。
- 所有 Python 代码均使用 `mypy` 进行类型检查。

要在本地运行检查：

```bash
ruff check src tests
mypy src
```

## Pull Request 流程

1.  确保所有测试通过。
2.  为新功能添加新的测试。
3.  如果公共 API 发生变化，请更新文档。
4.  编写清晰的变更描述。

## 行为准则

请尊重并体谅他人。我们将不容忍任何形式的骚扰或滥用。
