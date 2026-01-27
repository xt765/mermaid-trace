# 更新日志 (UPDATE_LOG)

## [2026-01-27] - 全面代码质量检查、测试验证与文档体系升级

### 代码质量与自动化检查

- **Ruff 静态分析与格式化**：
  - 运行 `ruff check .` 确保代码符合最新的编码规范，无代码质量问题。
  - 运行 `ruff format .` 对全量代码进行格式化，确保代码风格统一。
- **Mypy 类型检查**：
  - 执行 `mypy .` 验证全量代码的类型注解。
  - 确保 100% 通过严格模式（strict mode）下的类型检查，增强代码健壮性。
- **全量测试执行**：
  - 运行完整的单元测试、集成测试和端到端测试套件。
  - 112 个测试用例全部通过，测试覆盖率达到 **96.22%**，关键路径实现 100% 覆盖。

### 文档体系全面升级

- **中英文 README 同步**：
  - 更新了 `README.md` 和 `README_CN.md`，增加了关于分布式追踪（FastAPI）和 CLI 热重载功能的描述。
- **用户指南与 API 参考完善**：
  - 同步更新了 `USER_GUIDE.md` 和 `API.md` (中英文版)，确保所有 0.5.2 版本的新特性（如容器项合并、智能折叠）均有详尽说明。
- **代码注释文档（Code Comments）深度同步**：
  - 逐一核对 `docs/zh/code_comments/` 下的所有中文注释文档。
  - 确保文档中的源代码片段与 `src/mermaid_trace/` 目录下的实际代码实现完全同步。
  - 优化了 [formatter.md](file:///d:/TraeProjects/mermaid-trace/docs/zh/code_comments/src/mermaid_trace/core/formatter.md) 和 [decorators.md](file:///d:/TraeProjects/mermaid-trace/docs/zh/code_comments/src/mermaid_trace/core/decorators.md) 中的中文逻辑解释。

### 提交准备与验证

- **依赖项核对**：验证 `pyproject.toml` 中的依赖项正确无误。
- **构建验证**：确保项目构建流程正常，元数据准确。
- **版本一致性**：确认 CHANGELOG、版本号及文档描述保持高度一致。

## [2026-01-27] - 优化对象显示与文档同步

### 核心功能改进

- **对象表示简化**：
  - 优化了 `_safe_repr` 函数，现在会自动识别并简化包含内存地址的默认 Python 对象表示（如 `<__main__.Obj object at 0x...>`）。
  - 简化后的格式为 `<类名>`（如 `<AuthService>`），极大地提升了 Mermaid 时序图的可读性，并消除了因内存地址变化导致的图表差异。
- **容器项自动合并**：
  - 新增了列表（list）和元组（tuple）中连续相同项的自动合并功能。
  - 示例：`[<UserDB>, <UserDB>, <UserDB>]` 将显示为 `[<UserDB> x 3]`，显著缩减了复杂数据结构的显示长度。

### 文档系统全面更新

- **中英文文档同步**：
  - 更新了 `README.md` 和 `README_CN.md`，新增了“对象显示优化”和“容器合并”特性说明。
  - 同步更新了 `USER_GUIDE.md` (中英文版)，在“对象显示优化”章节中详细介绍了简化机制及容器合并逻辑。
- **代码注释文档系统性升级**：
  - 对 `docs/zh/code_comments/` 下的所有文档进行了系统性复核。
  - 特别更新了 [decorators.md](file:///d:/TraeProjects/mermaid-trace/docs/zh/code_comments/src/mermaid_trace/core/decorators.md)，新增了对 `FlowRepr` 类及其容器合并算法的详细中文注释。
  - 确保其中的源代码片段与最新实现完全一致。
- **交叉校对**：
  - 完成了中英文术语的统一（如：Source -> 调用方/源，Target -> 接收方/目标，Collapsing -> 折叠）。
  - 验证了所有文档中的代码示例，确保其在当前版本下可直接运行。

### 修复与优化

- 修正了 `decorators.py` 中因缺失 `List` 类型导入导致的运行时错误。
- 优化了 `MermaidFormatter` 中参与者名称清洗（Sanitize）的逻辑描述。
