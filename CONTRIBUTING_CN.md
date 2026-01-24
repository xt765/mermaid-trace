# 为 LogCapy 做贡献

首先，感谢您抽出时间来为项目做贡献！🎉

以下是为 LogCapy 及其相关包做贡献的一套指南。这些主要是指导方针，而非硬性规定。请运用您的最佳判断，并随时在 Pull Request 中对本文档提出修改建议。

## 行为准则

本项目及所有参与者均受 [LogCapy 行为准则](CODE_OF_CONDUCT.md) 的约束。参与本项目即表示您同意遵守该准则。

## 我该如何贡献？

### 报告 Bug

本节将指导您如何提交 LogCapy 的 Bug 报告。遵循这些指南有助于维护者和社区理解您的报告，重现该行为，并找到相关报告。

- **使用清晰且描述性的标题** 来标识问题。
- **尽可能详细地描述重现问题的确切步骤**。
- **提供具体示例** 来演示这些步骤。
- **描述您在执行步骤后观察到的行为**，并指出该行为具体有什么问题。
- **解释您期望看到的行为以及原因。**
- **包含截图和 GIF 动画**，展示您执行所述步骤的过程，并清楚地演示问题。

### 建议改进

本节将指导您如何提交 LogCapy 的改进建议，包括全新的功能和现有功能的微小改进。

- **使用清晰且描述性的标题** 来标识建议。
- **尽可能详细地提供建议改进的分步描述**。
- **提供具体示例** 来演示这些步骤。
- **描述当前的行为** 并 **解释您期望看到的行为以及原因**。

### Pull Requests

此处描述的流程有几个目标：

- 保持 LogCapy 的质量
- 修复对用户重要的问题
- 让社区参与致力于打造最好的 LogCapy
- 为 LogCapy 的维护者建立一个可持续的贡献审查系统

请遵循以下步骤，以便维护者考虑您的贡献：

1.  遵循 [模板](.github/PULL_REQUEST_TEMPLATE.md) 中的所有说明
2.  遵循 [风格指南](#styleguides)
3.  提交 Pull Request 后，验证所有 [状态检查](https://help.github.com/articles/about-status-checks/) 是否通过 <details><summary>如果状态检查失败怎么办？</summary>如果状态检查失败，并且您认为失败与您的更改无关，请在 Pull Request 上发表评论，解释您认为失败无关的原因。维护者将为您重新运行状态检查。如果我们得出结论认为是误报，我们将开启一个 Issue 来跟踪状态检查套件的那个问题。</details>

虽然在审查您的 Pull Request 之前必须满足上述先决条件，但在最终接受您的 Pull Request 之前，审查者可能会要求您完成额外的设计工作、测试或其他更改。

## 风格指南

### Git 提交信息

- 使用现在时态（"Add feature" 而不是 "Added feature"）
- 使用祈使语气（"Move cursor to..." 而不是 "Moves cursor to..."）
- 第一行限制在 72 个字符以内
- 在第一行之后充分引用 Issue 和 Pull Request

### Python 风格指南

- 所有 Python 代码均使用 `ruff` 进行 Lint 检查。
- 所有 Python 代码均使用 `black`（通过 `ruff`）进行格式化。
- 所有 Python 代码均使用 `mypy` 进行类型检查。

## 开发环境设置

1.  克隆仓库：
    ```bash
    git clone https://github.com/username/logcapy.git
    cd logcapy
    ```

2.  安装依赖：
    ```bash
    pip install .[all]
    pip install pytest pytest-cov ruff mypy build twine
    ```

3.  运行测试：
    ```bash
    pytest
    ```
