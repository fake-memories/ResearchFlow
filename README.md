# ResearchFlow

ResearchFlow 是一个长期 AI Agent 学习与开发项目，用于准备 AI Agent 开发实习。

长期目标是面向复杂知识任务的自主研究 Agent：从论文搜索开始，逐步扩展 PDF 理解、知识库问答和调研报告生成。

当前阶段是 **LLM 工具流程原型**，已具备单次问答、受步数限制的多轮流程，以及“模型生成 JSON 参数 → Python 校验 → arXiv 论文检索”的固定流程，尚未发布正式版本。

Day 1 从项目初始化开始，实现一次简单的 LLM 问答；Day 2 在此基础上新增带消息历史和停止条件的多轮示例。

## 后续路线

以下路线按每日复盘调整：

- Day 3（已完成）：参数校验、模型 JSON 输出与论文搜索串联已通过验证，并完成学习复盘。
- Day 4：接入模型原生 Function Calling，执行工具并回传结果。
- Day 5：组合为最小工具 Agent，依据结果继续推进或结束任务。
- Day 6 起：RAG 入门，再逐步加入 PDF、知识库和调研报告能力。

已跑通“输入需求 → 生成搜索参数 → 调用搜索函数 → 返回有来源的论文列表”，可作为 `v0.2` 的候选里程碑；尚未发布正式版本。

## 项目结构

```text
ResearchFlow/
├── app/
│   ├── main.py
│   ├── agent_loop.py
│   ├── structured_output.py
│   ├── json_output.py
│   └── paper_tools.py
├── tests/
│   ├── .gitkeep
│   ├── test_main.py
│   ├── test_agent_loop.py
│   ├── test_structured_output.py
│   ├── test_json_output.py
│   └── test_paper_tools.py
├── docs/
│   ├── .gitkeep
│   └── day3_prompt_and_tools.md
├── Agent_Study_Progress.md
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

- `app/main.py`：单文件 LLM 问答入口。
- `app/agent_loop.py`：Day 2 多轮示例，保存本次运行的消息历史，检查完成状态并限制最大步数。
- `app/structured_output.py`：Day 3 离线示例，将 JSON 文本解析为字典，校验关键词和返回数量。
- `app/json_output.py`：Day 3 模型 JSON 输出入口，将用户需求转换为搜索参数，并复用已有函数校验。
- `app/paper_tools.py`：Day 3 论文搜索函数，使用 arXiv API 返回标题、来源链接和首次提交年份。
- `tests/`：存放离线单元测试，使用 `.gitkeep` 在 Git 中保留目录。
- `docs/`：存放后续项目文档，使用 `.gitkeep` 在 Git 中保留目录。
- `Agent_Study_Progress.md`：记录每日学习目标、成果和问题。
- `README.md`：项目说明和启动方法。
- `requirements.txt`：Python 依赖清单。
- `.gitignore`：忽略本地环境配置、虚拟环境和 Python 缓存。
- `.env.example`：环境变量示例，不包含真实密钥。

## 本地启动

先安装 Conda。打开 Anaconda Prompt，或使用已配置 Conda 的 CMD，依次执行以下步骤。

1. 进入项目目录：

   ```cmd
   cd /d D:\ResearchFlow
   ```

2. 首次配置时创建 Python 3.11 环境：

   ```cmd
   conda create -n researchflow python=3.11 pip
   ```

3. 激活项目环境：

   ```cmd
   conda activate researchflow
   ```

4. 首次配置时安装依赖：

   ```cmd
   python -m pip install -r requirements.txt
   ```

5. 在项目目录中准备 `.env`，已有文件不会被覆盖：

   ```cmd
   if not exist .env copy .env.example .env
   ```

   用文本编辑器打开 `.env`，将 `OPENAI_API_KEY` 的占位值替换为自己的 **DeepSeek 官方 API 密钥**。这里沿用 OpenAI SDK 的变量名，填写的值是 DeepSeek 密钥。

   `.env.example` 仅提供 `OPENAI_API_KEY` 占位字段。入口仅读取项目 `.env` 中的 `OPENAI_API_KEY`；仅填写 `DEEPSEEK_API_KEY` 不会被入口读取。`.env` 已被 Git 忽略，请勿提交真实密钥。

6. 运行项目入口，发起一次真实模型请求：

   ```cmd
   python app\main.py
   ```

以后进入项目目录并激活现有的 `researchflow` 环境即可运行，无需重复创建环境。

在项目目录中，也可以不激活环境，直接运行：

```cmd
conda run -n researchflow python app\main.py
```

## 问答流程

`app/main.py` 读取固定问题，通过 OpenAI Python SDK 的 Chat Completions 接口请求 DeepSeek，再打印答案。

- 服务地址：`https://api.deepseek.com`。
- 模型：`deepseek-flash`。
- 固定问题：请用一句话解释什么是大语言模型。
- 请求设置：单次非流式调用、关闭思考、`max_tokens=200`、30 秒超时、无自动重试。

输出格式如下，答案以模型实际返回为准：

```text
问题：请用一句话解释什么是大语言模型。
回答：<模型返回的答案>
```

示例只包含输入、模型请求和答案输出，不使用 LangChain、Agent 框架、工具或多轮对话。

## Day 2 多轮示例

在项目目录中激活现有 `researchflow` 环境后运行：

```cmd
python app\agent_loop.py
```

也可以直接使用现有环境：

```cmd
conda run -n researchflow python app\agent_loop.py
```

示例任务是逐轮补充一份包含三项任务的 AI Agent 入门学习计划，每轮只补充一项。程序每轮发起一次真实模型请求，最多三轮。

- `messages` 起初保存任务；后续加入模型回答和继续指令，使下一轮请求包含前轮结果。这些历史只保存在本次运行的内存中。
- 回复必须包含任务正文，最后一行必须是独立的 `STATUS: CONTINUE` 或 `STATUS: DONE`，只能有一条独立状态行。
- 收到 `STATUS: DONE` 时通过 `break` 退出，并显示“模型声明任务完成”。这表示收到结束信号；计划是否包含三项有效任务仍需人工检查。
- 三轮都未收到完成状态时，显示“达到最大步数（3），任务尚未完成”。
- 空回答、非法格式和 API 异常会停止循环并给出简短提示。

这是学习消息历史和循环控制的简化流程。后续再逐步加入工具与依据执行结果选择行动的能力。

## Day 3 JSON 参数校验示例

在项目目录中激活现有环境后运行：

```cmd
conda activate researchflow
python app\structured_output.py
```

也可以直接使用现有环境：

```cmd
conda run -n researchflow python app\structured_output.py
```

`parse_search_params(answer)` 接收 JSON 字符串，成功时返回只包含 `query` 和 `max_results` 的字典：

- 顶层必须是 JSON 对象，两个字段都必须存在。
- `query` 必须是字符串，去掉两端空白后不能为空。
- `max_results` 必须是 1–5 的整数；字符串、浮点数和布尔值会被拒绝。
- 输入或参数不合要求时抛出 `ValueError`，交给调用方处理。

入口使用 8 组固定输入，逐例捕获错误并打印结果，便于比较不同检查。它不请求模型或论文接口，也不读取密钥。模型 JSON 输出与论文检索的入口见下文。

概念、关键代码与实际运行结果见 [Day 3 学习文档](docs/day3_prompt_and_tools.md)。

## Day 3 模型 JSON 输出

在项目根目录使用现有环境运行：

```cmd
conda run -n researchflow python -m app.json_output
```

已激活 `researchflow` 环境时，也可以运行：

```cmd
python -m app.json_output
```

`-m app.json_output` 按模块运行程序，使它能从项目根目录导入 `app.structured_output` 中的校验函数。

此入口会读取已有 `.env` 并发起一次真实 DeepSeek 请求，密钥配置沿用 Day 1。固定需求为“帮我找两篇关于 RAG（检索增强生成）的论文。”。

- `system` 消息说明参数提取规则，`user` 消息提供具体需求。
- 请求设置 `response_format={"type": "json_object"}`，提示中包含 JSON 格式样例。
- 检查完成原因和空回复后，打印模型原始 JSON，再调用 `parse_search_params()`。
- 成功时打印经过校验的参数；截断、异常结束、非法参数或 API 错误会给出提示并退出。

已完成真实调用，返回的关键词为 `retrieval-augmented generation`、数量为整数 `2`，校验通过。字段校验不自动证明参数忠实于需求，关键词含义和数量仍需核对。默认只生成参数，添加下面的 `--search` 后继续检索论文。

## Day 3 论文搜索与完整流程

先用固定关键词直接调用工具，不请求模型、不读取密钥：

```cmd
conda run -n researchflow python -m app.paper_tools
```

然后使用模型生成的参数执行搜索：

```cmd
conda run -n researchflow python -m app.json_output --search
```

`--search` 是命令行开关，程序先生成并校验 JSON 参数，再执行 `search_paper(query, max_results)`。省略该开关时仍只显示参数。

- 工具接收非空关键词和 1–5 的整数数量，默认最多返回 3 篇；演示入口指定 2 篇。
- 使用现有 `requests` 请求 arXiv，按短语检索并按相关性排序，标准库解析返回的 Atom/XML。
- 每篇包含 `title`、`url` 和 `year`；年份来自首次提交日期，缺失或无法解析时显示“年份未知”。
- 无结果时返回空列表并提示调整关键词；网络、HTTP、查询或数据异常会明确报告失败。
- 每次只发起一次检索，没有分页或自动重试。连续请求遵守 arXiv 单连接、至少间隔 3 秒的要求。

直接检索与模型参数串联均已真实运行成功，返回两篇带来源链接的论文，结果保存在 Day 3 文档中。搜索由 Python 固定执行；当前尚未使用模型原生 Tool Calling，也未把检索结果回传给模型。

## 初始依赖

`requirements.txt` 包含以下依赖，暂不固定版本：

- `openai`：使用 OpenAI Python SDK 调用 DeepSeek 兼容接口。
- `python-dotenv`：读取项目 `.env` 配置。
- `requests`：用于请求 arXiv 论文接口。

## 离线测试

在项目目录中激活 `researchflow` 环境后执行：

```cmd
python -m unittest discover -s tests -v
```

测试使用模拟响应，不请求 DeepSeek 或 arXiv，也不需要真实密钥。

当前共 45 项测试：Day 1 的 7 项问答与配置测试、Day 2 的 7 项循环与异常测试，以及 Day 3 的 9 项 JSON 参数校验、12 项模型请求与搜索串联、10 项论文工具测试。

## 常见问题

- 缺少密钥或仍是占位值：检查 `D:\ResearchFlow\.env` 中的 `OPENAI_API_KEY` 是否填写了 DeepSeek 官方密钥。
- API 返回错误状态：401／403 时检查密钥与访问权限；429 时检查额度或限流情况。
- 网络连接失败或超时：检查网络、代理及 DeepSeek 服务状态，恢复后手动重新运行。

## Day 1 状态

- 基础目录和文件已创建。
- Git 仓库已初始化，首次提交用于保存项目骨架。
- 已创建 Conda 环境 `researchflow`，使用 Python 3.11，项目依赖已安装。
- 第一个 LLM 问答示例已实现，7 项离线单元测试通过，DeepSeek 真实问答请求已成功验证。
- 学习记录请在 `Agent_Study_Progress.md` 中按实际情况填写。
