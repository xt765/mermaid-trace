# 更新日志 (UPDATE_LOG)

## [0.7.0] - 2026-02-24 - CLI 重构、Web 预览增强与生态扩展

### 核心架构升级
- **CLI 统一重构**: 
  - 彻底重写了命令行接口，废弃了基于 `http.server` 的简易实现，统一使用基于 FastAPI 的增强型服务器。
  - 移除了 `--master` 参数，现在 `mermaid-trace serve` 默认开启全功能 Web 预览（支持热重载、缩放、平移）。
  - 支持单文件模式：`mermaid-trace serve file.mmd` 也能享受完整的 Web UI 体验。
- **Mermaid 渲染修复**: 
  - 修复了 Python 对象表示（如 `<User>`）包含特殊字符导致 Mermaid 语法解析错误的问题。
  - 实现了 HTML 实体转义机制，确保 `<`、`>` 等字符在图表中正确显示。

### 生态集成与示例
- **LangChain 集成增强**: 
  - 优化了 `examples/09_langchain_integration.py`，支持在未安装 LangChain 环境下的 Mock 运行模式，方便用户体验。
  - 修复了类型检查问题，确保集成代码的健壮性。
- **新增高级示例**:
  - `10_distributed_trace_simulation.py`: 演示了如何在分布式系统中传递 Trace Context。
  - `11_custom_masking.py`: 展示了如何自定义数据脱敏逻辑（如递归脱敏）。
  - `12_config_from_file.py`: 演示了从 JSON 文件加载配置。

### 文档与规范
- **中英文文档同步**: 更新了 `README` 和 `USER_GUIDE`，反映了 CLI 的最新用法。
- **代码注释**: 全面更新了 `cli.py` 和 `server.py` 的中文代码注释，详细解释了服务器实现原理。
- **依赖管理**: 在 `pyproject.toml` 中新增了 `server` extras，方便用户一键安装服务器依赖 (`pip install mermaid-trace[server]`)。

## [2026-02-02] - QA 强化与文档精化 (Refinement)

### 代码质量强化
- **Mypy 类型安全修复**: 
    - 修复了 `MermaidTraceCallbackHandler.on_retriever_end` 的方法签名，将其与 LangChain 核心库的 `Sequence[Document]` 类型对齐，解决了 Liskov 替换原则违规错误。
    - 在 `examples/09_langchain_integration.py` 中引入 `cast(Any, ...)`，确保在无 `langchain-core` 环境下的示例代码也能通过类型检查。
- **自动化检查**: 再次运行全量 Ruff 格式化与 Mypy 静态分析，确保代码库 100% 符合规范。
- **全量测试**: 执行 122 个测试用例，全部通过，整体覆盖率稳定在 90% 以上。

### 文档同步精化
- **代码注释同步**: 同步更新了 `docs/zh/code_comments/` 和 `docs/en/code_comments/` 下关于 LangChain 集成的源代码注释文档，确保文档中的示例代码与最新实现（包括 `TYPE_CHECKING` 块和方法签名）完全一致。
- **中英文对齐**: 确保所有新增的类型定义和逻辑说明在中英文文档中保持同步。

## [2026-02-02] - 增强型 Web 预览 (Master 模式) 与 UI 优化
- **基于 FastAPI 的增强服务器**: 实现了 `run_server` 函数，利用 FastAPI 搭建高性能 Web 预览后端。
- **SSE 实时通信**: 引入 Server-Sent Events (SSE) 机制，实现 `.mmd` 文件更新时的前端零延迟自动刷新。
- **交互式渲染引擎**: 
  - 集成 `mermaid.js` 异步渲染逻辑，提升大型图表的加载性能。
  - 引入 `svg-pan-zoom` 库，支持图表的自由缩放和平移操作，极大改善了复杂流程的可视化体验。
- **智能目录管理**: 
  - 侧边栏支持实时展示工作目录下的所有 `.mmd` 文件。
  - 支持在不重启服务器的情况下，点击侧边栏动态切换预览不同的图表。
- **CLI 深度集成**: 扩展了 `mermaid-trace serve` 命令，新增 `--master` 标志位，支持一键开启增强预览模式。

### UI/UX 改进
- **布局重构**: 采用 Flex 布局彻底重构了预览界面的容器结构，修复了在某些分辨率下垂直方向显示不全的问题。
- **自动适应**: 移除了 SVG 的固定宽高限制，确保图表能够根据容器大小自适应调整。

### 代码质量与文档同步
- **测试用例更新**: 适配了 CLI 的 `master` 参数变化，确保 `test_cli_main` 和 `test_cli_main_master` 覆盖所有入口场景。
- **文档全量更新**:
  - 创建了 `server.md` (中/英) 代码注释文档，详细记录了增强服务器的实现原理。
  - 更新了 `cli.md` (中/英) 文档，同步了 Master 模式的命令行参数说明。
  - 同步更新了 `README.md` 和 `README_CN.md` 中的使用示例。

## [2026-02-02] - LangChain 集成、全面 QA 检查与文档同步

### LangChain 框架集成与关键问题修复
- **回调处理器实现**: 实现了 `MermaidTraceCallbackHandler`，支持 LangChain 全生命周期事件捕获。
- **日志记录协议对齐**: 修复了 `MermaidTraceCallbackHandler` 缺失 `extra={"flow_event": event}` 参数的问题，确保所有 LangChain 事件能正确被 `MermaidFileHandler` 捕获并生成 Mermaid 语法。
- **空文件问题修复**: 解决了在 LangChain 集成下生成的 `.mmd` 文件内容为空的严重问题。
- **多组件支持**: 深度集成 Chain、LLM、ChatModel、Tool 和 Retriever（检索器），可自动可视化 RAG 流程和 Agent 决策路径。
- **嵌套调用追踪**: 引入内部参与者栈（Participant Stack）机制，确保在深层嵌套调用下，Mermaid 时序图的返回箭头（`-->>`）能够精准指向发起方。
- **健壮性优化**: 采用条件导入机制，确保 `langchain-core` 为可选依赖，不影响核心库的独立使用。

### 代码质量与测试验证
- **全量 QA 检查**:
    - **Ruff**: 通过全量代码静态检查与格式化，无规范错误。
    - **Mypy**: 修复了 `langchain.py` 中的类型注解错误及可选依赖导致的导入识别问题，实现 100% 类型安全。
- **测试驱动开发**:
    - **测试用例适配**: 同步更新了 `test_langchain.py` 中的测试逻辑，适配新的日志记录协议（通过 `call_args[1]["extra"]["flow_event"]` 访问事件）。
    - 新增 9 个针对 LangChain 集成的单元测试，覆盖正常流程、嵌套调用及异常场景。
    - 执行全量测试套件（共 121 个用例），全部成功通过。
    - **测试覆盖率**: 整体覆盖率达到 **93.34%**，关键逻辑实现全覆盖。

### 文档体系全量同步
- **核心文档更新**:
    - 更新 `README.md` 和 `README_CN.md`，新增 LangChain 集成快速入门示例。
    - 完善 `USER_GUIDE.md` (中/英)，新增 LangChain 章节，详细说明 RAG 追踪、Agent 追踪及参与者栈原理。
    - 完善 `API.md` (中/英)，新增 `MermaidTraceCallbackHandler` 的详细参数与事件说明。
- **源代码注释同步**:
    - 全面更新 `docs/zh/code_comments/src/mermaid_trace/integrations/langchain.md`，确保其中的源代码片段与最新实现完全一致，并提供详尽的中文逻辑解释。

## [2026-01-27] - 最终验证与提交准备

### 代码质量与测试验证
- **Ruff/Mypy 检查**: 再次运行 `ruff check .` 和 `mypy .`，确保全量代码 100% 符合规范且类型安全。
- **全量测试通过**: 执行全部 112 个测试用例，所有测试均成功通过，测试覆盖率维持在 94.63% 以上。

### 文档体系同步与增强
- **中英文 README 同步**: 统一了 `README.md` 和 `README_CN.md` 的文档结构，增加了“代码注释文档”导航表，方便开发者快速查阅。
- **文档一致性校验**: 确保 `USER_GUIDE.md` 和 `API.md` 在中英文版本中内容完全一致，并与最新的 v0.5.3 版本代码功能（如 `overwrite` 参数和日志轮转）匹配。
- **代码注释文档覆盖**: 验证 `docs/zh/code_comments/` 目录完整覆盖了所有核心模块、处理器及集成代码，注释内容详尽且准确。

### 交付准备
- **构建环境确认**: 确认项目结构符合 Python 打包标准，`pyproject.toml` 配置正确。
- **示例代码验证**: 验证所有示例代码（特别是 `08-log-rotation.py`）可正常运行。

## [2026-01-27] - 代码质量深度优化与文档全量同步

### 代码质量与规范化修复

- **Ruff/Mypy 错误修复**：
  - 修复了全量代码中的 Ruff 静态检查错误和 Mypy 类型注解错误。
  - 特别针对 `decorators.py` 中的 `PLR0913` (函数参数过多) 错误进行了重构，引入了 `_TraceConfig` 和 `_TraceMetadata` 数据类进行参数解耦。
  - 在 `configure_flow` 和部分日志处理器构造函数中添加了 `# noqa: PLR0913` 注释，以在保持 API 稳定性的同时通过质量检查。
- **Mypy 兼容性增强**：
  - 在 `mermaid_handler.py` 中使用 `getattr` 动态调用方法，解决了混入类 (Mixin) 模式下的类型识别问题。
  - 完善了示例代码 `08-log-rotation.py` 中的函数类型注解。

### 文档体系全量更新与对齐

- **文档一致性修正**：
  - 全面修正了中英文文档中 `configure_flow` 的 `overwrite` 参数默认值。将错误的 `False` 统一修正为与源码一致的 `True`。
  - 受影响文件包括：`README.md`、`README_CN.md`、`API.md` (中/英)、`USER_GUIDE.md` (中/英)。
- **代码注释文档 (Code Comments) 同步**：
  - 全面刷新了 `docs/zh/code_comments/` 目录下的所有中文注释文档。
  - 特别更新了 [decorators.md](file:///d:/TraeProjects/mermaid-trace/docs/zh/code_comments/src/mermaid_trace/core/decorators.md)，增加了对新引入的数据类（`_TraceConfig`, `_TraceMetadata`）的解释，并同步了最新的函数签名。
  - 确保所有注释文档中的代码片段与 `src/` 目录下的实际实现 100% 匹配。

### 验证与测试

- **全量测试通过**：
  - 运行了全部 112 个单元测试和集成测试，所有用例均成功执行。
  - 验证测试覆盖率保持在 **95%** 以上的高水平。
- **质量指标确认**：
  - 确认代码复杂度（C901）和代码重复率（Pylint 评分 10.0/10）均符合项目质量标准。

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
