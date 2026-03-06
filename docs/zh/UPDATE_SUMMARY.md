# MermaidTrace 更新摘要

## [v0.7.1] - 2026-03-06 - 依赖管理优化与离线支持

### 交付物状态清单

| 类别 | 交付项 | 状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **依赖管理** | FastAPI/Uvicorn | ✅ 必需依赖 | 从可选依赖变为必需依赖，简化安装流程 |
| **CLI 功能** | version 命令 | ✅ 新增 | 显示版本信息 |
| **CLI 功能** | --no-browser 选项 | ✅ 新增 | 控制浏览器自动打开行为 |
| **CLI 功能** | --master 标志 | ✅ 移除 | 完全移除已废弃的参数 |
| **离线支持** | 本地静态资源 | ✅ 实现 | Tailwind CSS、Mermaid.js、svg-pan-zoom 打包到本地 |
| **代码质量** | Ruff 检查 | ✅ 通过 | 全量代码符合规范 |
| **测试** | 单元/集成测试 | ✅ 通过 | 131 个测试用例全部成功 |
| **文档** | 中英文文档集 | ✅ 更新 | 所有文档同步更新到 v0.7.1 |

### 核心技术亮点

- **依赖管理优化**: 用户不再需要安装 `[server]` extras，直接 `pip install mermaid-trace` 即可使用所有功能。
- **完全离线支持**: Web 预览服务器使用本地静态资源，无需网络连接即可使用。
- **CLI 增强**: 帮助信息更详细，新增实用功能（version 命令、--no-browser 选项）。
- **代码简化**: 移除了优雅降级逻辑和 Mock 类，代码更简洁。

### 安装方式变更

**之前**:
```bash
pip install mermaid-trace          # 基础安装，无法使用 serve
pip install mermaid-trace[server]  # 完整安装
```

**现在**:
```bash
pip install mermaid-trace  # 安装后即可使用所有功能
```

---

## [v0.7.0] - 2026-02-24 - CLI 重构、Web 预览增强与生态扩展

### 交付物状态清单

| 类别 | 交付项 | 状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **代码质量** | Ruff 检查 | ✅ 通过 | 运行 `ruff check` 和 `ruff format`，全量代码符合规范 |
| **类型安全** | Mypy 检查 | ✅ 通过 | 修复了 `langchain.py` 及其可选依赖的类型识别问题 |
| **功能验证** | 单元/集成测试 | ✅ 通过 | 共 121 个测试用例全部成功，整体覆盖率 93.34% |
| **框架集成** | LangChain 支持 | ✅ 新增 | 完整实现 `MermaidTraceCallbackHandler`，支持 RAG 与 Agent 追踪 |
| **文档** | 中英文文档集 | ✅ 更新 | README, USER_GUIDE, API 同步完成，新增 LangChain 章节 |
| **文档** | 源代码中文注释 | ✅ 更新 | docs/zh/code_comments 完整覆盖 LangChain 模块，逻辑说明详尽 |

### 核心技术亮点
- **LangChain 回调体系深度集成**: 通过实现 `BaseCallbackHandler`，实现了对 LangChain 生态（Chain, LLM, Tool, Retriever）的无缝追踪，是目前社区中少有的能直接生成 Mermaid 时序图的工具。
- **参与者栈（Participant Stack）机制**: 创新性地解决了 LangChain 内部组件深层嵌套调用时的 Mermaid 语义对齐问题，确保返回箭头（Return Arrows）的逻辑准确性。
- **可选依赖架构**: 采用条件导入技术，保证了项目在未安装 `langchain-core` 的环境下的正常运行，实现了真正的插件化集成。

---

## [v0.6.0] - 2026-02-02 - QA 强化与文档精化

### 交付物状态清单

| 类别 | 交付项 | 状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **代码质量** | Ruff 检查 | ✅ 通过 | 运行 `ruff check` 和 `ruff format`，全量代码符合规范 |
| **类型安全** | Mypy 检查 | ✅ 通过 | 修复了 `MermaidTraceCallbackHandler.on_retriever_end` 的方法签名 |
| **功能验证** | 单元/集成测试 | ✅ 通过 | 共 122 个测试用例全部成功，整体覆盖率 90% 以上 |
| **文档** | 中英文文档集 | ✅ 更新 | 同步更新了 LangChain 集成的源代码注释文档 |

### 核心技术亮点
- **类型安全修复**: 修复了与 LangChain 核心库的类型对齐问题，解决了 Liskov 替换原则违规错误。
- **Mock 运行模式**: 优化了示例代码，支持在未安装 LangChain 环境下的 Mock 运行模式。
