# MermaidTrace v0.6.2 发布：统一预览体验与分布式追踪支持

**日期**: 2026-02-24  
**作者**: 玄同765

我们很高兴地宣布 MermaidTrace v0.6.2 正式发布！本次更新主要集中在统一命令行工具体验、增强 Web 预览功能以及扩展高级应用场景。

## 🚀 核心亮点

### 1. 统一的 CLI 预览体验

在之前的版本中，我们提供了基础的 `http.server` 预览和基于 FastAPI 的 `--master` 模式预览。这种区分不仅增加了用户的学习成本，也导致了功能体验的不一致。

在 v0.6.2 中，我们彻底重构了 CLI：

- **单一入口**：现在只需运行 `mermaid-trace serve`，无论目标是单个文件还是目录，都会默认启动增强型 Web 服务器。
- **全功能体验**：即使只预览一个简单的脚本输出，也能享受到**实时热重载**、**交互式缩放/平移**以及**美观的 UI**。
- **智能降级**：如果未安装 `fastapi` 和 `uvicorn`，CLI 会给出清晰的安装提示（`pip install mermaid-trace[server]`）。

```bash
# 预览单个文件（实时刷新）
mermaid-trace serve my_trace.mmd

# 预览项目目录（文件浏览器）
mermaid-trace serve .
```

### 2. 分布式追踪模拟

随着微服务架构的普及，跨服务的调用追踪变得至关重要。我们在 `examples/10_distributed_trace_simulation.py` 中新增了一个完整的分布式追踪示例，演示了如何：

- 在服务间传递 Trace ID。
- 使用 `MermaidTrace` 记录跨服务的调用链路。
- 生成包含多个服务的统一时序图。

### 3. LangChain 集成增强

我们优化了 `LangChain` 集成模块，使其更加健壮和易用：

- **Mock 模式**：即使没有安装 `langchain` 库，用户也可以运行示例代码体验集成效果。
- **类型安全**：修复了与 `langchain-core` 的类型兼容性问题，通过了严格的 Mypy 检查。

### 4. 渲染引擎修复

针对 Python 对象表示中可能包含特殊字符（如 `<User object at 0x...>` 中的 `<` 和 `>`）导致 Mermaid 语法解析错误的问题，我们引入了自动 HTML 实体转义机制。现在的图表渲染更加稳定，不再受特殊字符干扰。

## 📚 下一步计划

我们将继续探索更多高级场景，包括：

- **性能分析视图**：在时序图中集成函数执行耗时热力图。
- **更丰富的框架支持**：计划增加对 Django 和 Flask 的原生支持。

感谢所有社区贡献者的支持！欢迎在 GitHub 上提交 Issue 或 PR。

---

*立即升级体验：*
```bash
pip install -U mermaid-trace[server]
```
