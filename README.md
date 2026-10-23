# ResearchFlow

ResearchFlow 是一个长期 AI Agent 学习与开发项目，用于准备 AI Agent 开发实习。

长期目标是面向复杂知识任务的自主研究 Agent：从论文搜索开始，逐步扩展 PDF 理解、知识库问答和调研报告生成。

当前阶段已具备 **有次数上限的最小工具 Agent 与本地文档 RAG**：支持单次问答、受步数限制的多轮流程、JSON 参数检索流程、原生 Tool Calling 循环，以及根据本地文档片段生成带来源的回答，尚未发布正式版本。

Day 1 从项目初始化开始，实现一次简单的 LLM 问答；Day 2 在此基础上新增带消息历史和停止条件的多轮示例。

## 后续路线

以下路线按每日复盘调整：

- Day 3（已完成）：参数校验、模型 JSON 输出与论文搜索串联已通过验证，并完成学习复盘。
- Day 4（已完成）：原生 Function Calling 的搜索闭环与直接回答均已实际运行，64 项离线测试通过，并完成学习复盘。
- Day 5（已完成）：组合为有界最小工具 Agent，依据结果继续搜索或回答；搜索与直接回答均已实际运行，83 项离线测试通过，并完成学习复盘。
- Day 6（已完成）：读取本地 Markdown、按段落分块、关键词排序检索、组织来源标签并生成回答；真实回答和无匹配分支已运行，新增 20 项离线测试通过，全套共 103 项通过。
- Day 7（计划）：接入一份 2–4 页的短文本 PDF，复用现有 RAG，保留页码和片段编号，并用固定问题核对回答来源。
- 后续：逐步加入 PDF 理解、Embedding 与向量检索、知识库和调研报告能力。

已跑通“输入需求 → 生成搜索参数 → 调用搜索函数 → 返回有来源的论文列表”，可作为 `v0.2` 的候选里程碑；尚未发布正式版本。

## 项目结构

```text
ResearchFlow/
├── app/
│   ├── main.py
│   ├── agent_loop.py
│   ├── structured_output.py
│   ├── json_output.py
│   ├── paper_tools.py
│   ├── tool_calling.py
│   ├── tool_agent.py
│   └── local_rag.py
├── data/
│   └── sample_docs/
│       ├── demo_rules.md
│       └── rag_basics.md
├── tests/
│   ├── .gitkeep
│   ├── test_main.py
│   ├── test_agent_loop.py
│   ├── test_structured_output.py
│   ├── test_json_output.py
│   ├── test_paper_tools.py
│   ├── test_tool_calling.py
│   ├── test_tool_agent.py
│   └── test_local_rag.py
├── docs/
│   ├── .gitkeep
│   ├── day3_prompt_and_tools.md
│   ├── day4_tool_calling.md
│   ├── day5_tool_agent.md
│   └── day6_local_rag.md
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
- `app/tool_calling.py`：Day 4 原生工具调用入口，让模型提出调用请求，Python 校验、执行并回传结果，再请求模型回答。
- `app/tool_agent.py`：Day 5 最小工具 Agent，保留完整消息历史，最多请求模型三次、执行搜索两次，显示每轮执行记录。
- `app/local_rag.py`：Day 6 本地文档 RAG，读取 Markdown、按段落分块、按关键词检索并生成带来源的回答，默认只打印演示。
- `data/sample_docs/`：Day 6 的两份教学材料，共 4 个段落片段。
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

直接检索与模型参数串联均已真实运行成功，返回两篇带来源链接的论文，结果保存在 Day 3 文档中。这个 Day 3 入口仍由 Python 固定执行搜索，不使用原生 Tool Calling，也不回传检索结果；新的闭环见下文 Day 4 入口。

## Day 4 原生 Tool Calling

在项目根目录使用现有环境运行：

```cmd
conda run -n researchflow python -m app.tool_calling
```

已激活 `researchflow` 时直接执行 `python -m app.tool_calling`。入口沿用已有 `.env`，默认查找两篇 RAG 论文，也可以指定需求：

```cmd
python -m app.tool_calling --request "请解释什么是 Tool Calling。"
```

- 第一次请求通过 `tools` 提供搜索工具的名称、用途和参数结构；模型可以提出调用请求，也可以直接回答。
- Python 只允许执行 `search_paper`，复用已有参数校验。未知工具、非法参数或检索失败会停止流程并明确报错。
- 成功后保存完整的 `assistant` 调用消息，再用匹配的 `tool_call_id` 回传 `tool` 结果；终端显示调用 ID、参数和实际结果。
- 第二次请求根据返回的标题、首次提交年份和来源链接回答，不提供新的工具。直接回答路径只请求模型一次，不搜索；搜索路径最多请求模型两次、执行工具一次。
- 本日先限制为一条工具调用，多条请求会明确报错，多步 Agent 循环留到 Day 5。空列表代表本次无匹配结果，超时等失败不会伪装成空结果。

该入口已完成真实工具调用闭环，返回两篇论文后由模型整理出对应标题、年份和来源链接；本地也已验证一般问题直接回答、无需搜索的路径。代码、流程说明与实际验证结果见 [Day 4 学习文档](docs/day4_tool_calling.md)。每日学习在独立分支进行，结束时再集中更新 `Agent_Study_Progress.md`，确认成果满意后合并回 `main`。

## Day 5 最小工具 Agent

在项目根目录、已激活的 `researchflow` 环境中运行：

```cmd
python -m app.tool_agent
python -m app.tool_agent --request "请用一句话解释 Tool Calling，不需要检索论文。"
```

也可以使用 `conda run -n researchflow python -m app.tool_agent`。入口沿用已有 `.env` 与默认的两篇 RAG 论文需求，每轮都提供工具描述，让模型根据历史决定继续搜索或回答。

- `messages` 在循环外初始化，后续保留完整的 `assistant` 调用请求与对应 `tool_call_id` 的 `tool` 结果。
- 默认最多请求模型三次、执行搜索两次；先接受有效答案，最后一次响应若仍要求工具则停止，不执行新的搜索。
- 每轮只处理一条工具调用；未知工具、非法参数或工具失败会明确报错并停止，不自动重试。
- 第一次搜索前不等待，此后每次搜索前额外等待三秒。终端显示请求编号、成功搜索次数、工具参数、结果和结束状态。
- 已实际验证一次搜索后回答（两次模型请求、一次搜索）和直接回答（一次模型请求、零次搜索）。两次搜索、达到上限与等待顺序由离线测试覆盖。

关键代码、计数方式、消息历史与真实运行证据见 [Day 5 学习文档](docs/day5_tool_agent.md)。

## Day 6 本地文档 RAG

在项目根目录、已激活的 `researchflow` 环境中运行：

```cmd
python -m app.local_rag
python -m app.local_rag --ask
python -m app.local_rag --ask --question "演示系统使用什么显卡？" --keywords 显卡
```

第一条只打印分块、检索与模型消息，不请求模型。`--ask` 沿用已有 `.env` 和 DeepSeek 配置，将问题及检索片段发送给模型，最多请求一次、30 秒超时、无自动重试。

- 材料来自 `data/sample_docs/*.md`，按空行分块，每块保留文件名、编号和正文。
- 关键词由调用方提供；每个列表项匹配正文就加 1 分，过滤零分、降序排序后取前 `top_k` 块。
- 默认问题为“根据教学演示约定，每次最多向模型提供几个检索片段？”，默认关键词为“最多”“片段”，`top_k=2`。可用 `--question`、`--keywords`、`--top-k` 分别调整。
- 无匹配时直接输出“资料中没有足够信息”，在读取密钥和创建客户端前返回，模型请求为 0 次。
- 已实际运行默认问答，回答“最多 2 个”并引用 `[demo_rules.md#1]`；显卡问题配合关键词“显卡”已验证无匹配、0 次模型请求。
- 检索目前是字面匹配，问题不会自动变成关键词；引用由提示词要求，事实和引用是否得到材料支持仍需核对。目前尚未加入 PDF 或 Embedding。

分块结构、消息构造、实际回答和验证边界见 [Day 6 学习文档](docs/day6_local_rag.md)。

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

当前共 103 项测试：Day 1–3 的 45 项测试、Day 4 的 19 项工具调用测试、Day 5 的 19 项有界循环测试，以及 Day 6 的 20 项本地 RAG 测试。Day 5 覆盖请求次数、消息历史、最后一轮正常回答、搜索间隔、空结果与失败停止等行为；Day 6 覆盖分块、读取、排序检索、消息构造、单次生成与无匹配时跳过配置和模型调用等行为。

Day 6 收尾时已在 `researchflow` 环境中实际运行：新增 20 项测试通过，全套 103 项测试通过。单独运行本地 RAG 测试：

```cmd
python -B -m unittest discover -s tests -p test_local_rag.py -v
```

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
