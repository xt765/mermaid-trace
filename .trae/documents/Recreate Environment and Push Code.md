我将按照以下步骤重新配置环境并推送代码：

1. **重建虚拟环境**：

   * 删除现有的 `.venv` 目录（如果存在），以确保环境纯净。

   * 使用 `python -m venv .venv` 创建新的虚拟环境。

2. **安装项目依赖**：

   * 使用虚拟环境中的 pip 安装项目的开发依赖：`.venv\Scripts\pip install -e .[dev]`。

   * 运行 `pip list` 验证安装是否成功。

3. **配置 Git 并推送代码**：

   * 验证 Git 配置（远程仓库 `origin` 已设置为 `https://github.com/xt765/mermaid-trace.git`）。

   * 添加所有文件到暂存区：`git add .`

   * 提交更改：`git commit -m "Initial commit with virtual environment setup"`

   * 按要求强制推送到 `main` 分支：`git push -u origin main --force`（这将覆盖远程仓库的历史记录）。

4. **最终验证**：

   * 确认远程仓库的状态。

