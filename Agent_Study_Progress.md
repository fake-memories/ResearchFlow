# ResearchFlow 学习档案

## 项目目标

通过持续学习和开发 ResearchFlow，积累 Python 与 AI Agent 开发实践，为 AI Agent 开发实习做准备。

## 当前阶段

Day 1：项目初始化、环境配置与第一个 LLM 问答示例。

## Day 1 记录

- 日期：2026-10-13
- Day：1
- 目标：建立 ResearchFlow 的基础目录、Python 入口和学习档案，并实现第一个简单的 LLM 问答示例。
- 内容：待按实际学习情况填写。
- 成果：基础目录及文件已创建；Conda 环境和项目依赖已配置；第一个 LLM 问答示例已实现，离线测试和真实调用均通过。
- 问题：待填写。
- 总结：待填写。
- 下一步：按实际学习情况补充本日记录，并填写下一次学习目标。

### 初始化事项

- [x] 创建 `app/`、`tests/` 和 `docs/` 目录。
- [x] 创建简单入口 `app/main.py`。
- [x] 创建 `README.md` 和 `Agent_Study_Progress.md`。
- [x] 创建 `requirements.txt`，包含 `openai`、`python-dotenv`、`requests`。
- [x] 创建 `.gitignore` 和 `.env.example`。
- [x] 安装项目依赖。
- [x] 初始化 Git 仓库并创建首次提交。

### Conda 迁移记录

- 日期：2026-10-13。
- 环境：已创建命名环境 `researchflow`，使用 Python 3.11。
- 解释器：已确认运行时使用新 Conda 环境中的 Python。
- 依赖：`openai`、`dotenv`、`requests` 三个模块均可导入，其中 `dotenv` 来自 `python-dotenv`。
- 依赖检查：`python -m pip check` 已通过。
- 迁移时入口验证：运行当时的 `app/main.py`，输出 `ResearchFlow is ready.` 并正常退出。
- 清理：新环境验证通过后，已清理旧 `.venv`。

### 第一个 LLM 问答示例

- 日期：2026-10-13。
- 实现：在 `app/main.py` 中使用 OpenAI Python SDK 的 Chat Completions 接口调用 DeepSeek。
- 配置：读取项目 `.env` 的 `OPENAI_API_KEY`，填写 DeepSeek 官方密钥，不输出密钥。
- 服务与模型：`https://api.deepseek.com`，`deepseek-flash`。
- 输入：固定问题“请用一句话解释什么是大语言模型。”。
- 请求设置：单次非流式、关闭思考、`max_tokens=200`、30 秒超时、无自动重试。
- 输出：打印“问题：...”和“回答：...”，流程限于输入、模型请求及答案输出。
- 离线单元测试：7 项测试通过，覆盖正常输出、配置定位、缺失密钥、连接失败、超时、HTTP 错误和空回答。
- 真实模型请求：已成功发送一次请求，返回非空回答，程序正常退出。
- 本次模型回答：大语言模型是一种基于海量文本数据训练、通过预测下一个词来生成连贯自然语言的人工智能系统。

## 每日记录模板

复制以下模板，按当天实际情况填写：

### Day __

- 日期：YYYY-MM-DD
- Day：
- 目标：
- 内容：
- 成果：
- 问题：
- 总结：
- 下一步：
