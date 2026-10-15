# ResearchFlow 学习笔记

## 项目目标

我希望通过持续学习和开发 ResearchFlow，积累 Python 与 AI Agent 开发实践，为实习做准备。这份笔记保存每天的概念解释、关键代码、开发成果和问题，方便以后忘记时直接查阅和复习。

长期希望把 ResearchFlow 做成面向复杂知识任务的自主研究 Agent，逐步加入论文搜索、PDF 理解、知识库问答和调研报告生成。当前仍是 LLM 应用原型，长期目标不作为已实现的功能。

## 每日学习与交流约定

1. **开始学习**：回顾前一天的记录，确定今天的目标、学习内容、编码任务、预计时间和验证方法。
2. **学习过程中**：遇到报错、不懂的代码或概念时及时提问，把有用的理解和问题整理进笔记。
3. **结束学习**：补全当天的成果、问题、理解和总结，检查 Git 差异，提交并同步需要保存的内容。
4. **复盘与调整**：结合当天记录和运行结果检查目标完成情况，修正理解，再调整下一天的任务。

每日记录持续追加，保留此前的 Day 记录。项目整体状态单独维护，初始化清单不在每天重复。当天结束时填写全部栏目；没有阻塞问题时说明实际状态。只记录发生过的工作、验证结果和实际学习情况，预计时间与实际用时分开，不将运行成功等同于已经掌握原理。

日记按自己的学习笔记来写，简洁记录学习内容、开发成果、问题和理解，不逐字保存聊天。需要补充的概念直接标为“补充”，还没弄清楚的部分留作下一步练习。

学习内容要写出具体知识和正确结论，包括概念是什么、有什么用、代码怎样运行以及容易混淆的地方。项目状态只保留简短进度，正文以能直接复习的内容为主。

## 项目状态

- 当前阶段：Day 3 已完成；下一步在 Day 4 学习模型原生 Tool Calling，复用现有论文搜索函数完成工具结果回传。
- 开发环境：Conda 命名环境 `researchflow`，Python 3.11。
- 当前能力：提供单次问答、带停止条件的多轮示例，以及“需求 → DeepSeek 生成 JSON 参数 → Python 校验 → arXiv 论文检索”的固定流程。
- 已完成：项目初始化、基础异常处理、45 项离线测试，以及问答、多轮流程、JSON 输出、论文检索及串联的实际运行验证。
- 尚未开始：模型自主选择工具及行动的 Agent、持久化 Memory、原生 Tool Calling、RAG。
- 当前版本：尚未发布正式版本。

## 后续学习路线

2026-10-15 根据[学习计划建议](https://chatgpt.com/s/t_6acfc27c4cdc81918f0118bfb297f1f7)调整：基础调用和循环已经有可运行成果，接下来把 Prompt、结构化输出与具体工具任务结合，为模型调用工具做好准备。

| 阶段 | 学习与开发重点 | 状态或验收目标 |
|---|---|---|
| Day 1 | Python 环境与第一次 LLM API 调用 | 已完成单次问答及验证 |
| Day 2 | 消息历史、循环控制与停止条件 | 已完成多轮示例及两种退出路径验证 |
| Day 3 | Prompt 基础、JSON 输出、论文搜索工具函数 | 已完成；参数生成、校验与真实检索均已验证并完成复盘 |
| Day 4 | 模型原生 Function Calling / Tool Calling | 待开始；模型返回工具名和参数，Python 校验后执行，再把工具结果回传给模型 |
| Day 5 | 第一个最小工具 Agent | 待开始；根据模型决定执行工具、观察结果并继续或结束，保留最大步数和执行记录 |
| Day 6 起 | RAG 入门 | 待开始；从小文档的分块、检索和带来源的回答开始，再逐步扩展 PDF 与知识库 |

阶段编号表示计划推进顺序，后续依据运行结果和复盘调整，不把计划写成已经完成。论文搜索是第一个具体场景，之后再扩展到更一般的知识任务。

## Day 1：项目初始化、环境配置与第一个 LLM 问答示例

- 日期：2026-10-13
- 状态：已完成；关键概念后续继续通过复述和练习巩固。

### 目标

1. 完成 ResearchFlow 项目结构、学习档案和 Git 管理。
2. 配置 Conda 环境与依赖，了解环境隔离、配置文件和密钥管理的作用。
3. 实现最小 LLM 问答程序，梳理输入、请求和响应流程。
4. 使用离线测试与一次真实请求验证程序，并同步到 GitHub。

### 今日学习

**1. Python 环境与依赖**

- Conda 环境提供项目使用的 Python 解释器和依赖包。不同项目可以使用不同环境，减少版本冲突；本项目使用 `researchflow` 和 Python 3.11。
- `conda create` 创建环境，`conda activate` 选择当前终端使用的环境；创建环境和安装项目依赖是两个步骤。
- `requirements.txt` 记录依赖名称，`python -m pip install -r requirements.txt` 使用当前 Python 对应的 pip 安装这些依赖。
- `openai` 提供调用模型接口的 SDK；`python-dotenv` 用于读取 `.env`，导入时包名是 `dotenv`；`requests` 用于发送 HTTP 请求，目前保留给后续任务使用。
- PowerShell 与 CMD 是不同的命令解释器，语法和脚本运行方式不同。Day 1 曾在 PowerShell 激活 `.venv` 时遇到执行策略限制，之后改用 Conda。

常用命令（在 Anaconda Prompt 或已配置 Conda 的 CMD 中）：

```cmd
cd /d D:\ResearchFlow
conda activate researchflow
python -m pip install -r requirements.txt
python app\main.py
```

环境已创建后，无需每天重新创建；没有新增或变更依赖时，也无需每天重新安装。

**2. 配置文件与密钥**

- `.env` 保存本地配置，例如 API 密钥。程序读取配置后再发起请求，密钥不写进代码、笔记或 Git 提交。
- `.env.example` 是配置格式示例，只保留字段名和占位值，方便重新配置项目。
- `.gitignore` 告诉 Git 忽略哪些未跟踪文件，本项目忽略 `.env`、`.venv/` 和 `__pycache__/`。如果文件已经被跟踪，仅添加忽略规则不会自动取消跟踪。
- `dotenv_values(ENV_PATH)` 把 `.env` 内容读成字典，再通过 `config.get("OPENAI_API_KEY")` 取出密钥；这个函数不会自动把配置写入进程环境变量。
- `Path(__file__).resolve().parent.parent / ".env"` 根据脚本位置定位项目配置，因此不会因为终端当前目录改变而读错 `.env`。

**3. 模型请求中的四个基本概念**

| 名称 | 含义与用途 | 本项目中的用法 |
|---|---|---|
| API Key | 请求身份认证所用的密钥，服务据此判断访问权限 | 从 `.env` 的 `OPENAI_API_KEY` 读取，实际填写 DeepSeek 密钥 |
| `base_url` | API 服务的基础地址，SDK 据此构造具体接口请求 | `https://api.deepseek.com` |
| `model` | 服务识别的模型标识，决定请求使用哪个模型 | 当前代码使用 `deepseek-flash` |
| `messages` | 按顺序发送给模型的消息列表，每条包含角色和内容 | Day 1 只有一条 `user` 消息；Day 2 加入历史回答与继续指令 |

SDK 是封装请求和响应处理的 Python 库。虽然这里使用 `OpenAI` 类，但请求实际发送到 `base_url` 指定的 DeepSeek 服务；SDK 的名称不等于实际服务提供方。

一条消息的结构：

```python
{"role": "user", "content": "请用一句话解释什么是大语言模型。"}
```

`role` 表示消息来源，`content` 是消息正文。请求参数叫复数 `messages`，因为它接收的是列表。

**4. 单次调用与回答提取**

完整流程：读取 `.env` → 检查密钥 → 创建 `client` → 调用 `create()` → 接收完整响应 → 提取回答文本 → 打印。

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": QUESTION}],
    max_tokens=200,
    extra_body={"thinking": {"type": "disabled"}},
)

answer = (response.choices[0].message.content or "").strip()
```

上面是关键片段；完整程序还会先检查 `response.choices` 是否为空，并处理请求异常。

- `response` 是完整响应对象，除了回复，还包含模型信息、用量等数据，不是直接的回答字符串。
- `response.choices` 是候选回复列表；`[0]` 取第一条，因为 Python 的列表索引从 0 开始。
- `.message` 是这条候选结果中的单条回复，`.content` 才是回答文本。
- `or ""` 把可能的 `None` 转为空字符串，避免后续对 `None` 调用字符串方法；`.strip()` 去掉文本两端的空白。
- 提取后仍要检查 `answer` 是否为空，不能把空回答当作成功。

**5. 请求限制与验证方式**

- `timeout=30.0` 配置请求超时；`max_retries=0` 关闭 SDK 自动重试。
- `max_tokens=200` 限制单次生成的 token 数。token 是模型处理文本的单位，不等于中文字数。
- 离线测试通过模拟 SDK 响应检查程序行为，不访问真实模型，也不需要真实密钥。
- 真实运行验证密钥、网络、接口和模型是否能一起工作；两种验证互相补充。

接口与响应结构参考：[OpenAI Chat Completions 文档](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create)。

### 今日开发

**项目初始化**

- [x] 创建 `app/`、`tests/` 和 `docs/` 目录。
- [x] 创建简单入口 `app/main.py`。
- [x] 创建 `README.md` 和 `Agent_Study_Progress.md`。
- [x] 创建 `requirements.txt`，包含 `openai`、`python-dotenv`、`requests`。
- [x] 创建 `.gitignore` 和 `.env.example`，忽略 `.env`、`.venv/` 和 `__pycache__/`。
- [x] 初始化 Git 仓库、创建首次提交并建立公开 GitHub 仓库。

**Conda 环境配置**

- 创建命名环境 `researchflow`，使用 Python 3.11，并在该环境中安装项目依赖。
- 确认解释器属于该环境；`openai`、`dotenv`、`requests` 均可导入，其中 `dotenv` 来自 `python-dotenv`。
- `python -m pip check` 已通过。
- 迁移时运行当时的入口，输出 `ResearchFlow is ready.` 并正常退出；这是环境迁移阶段的验证，之后入口已改为 LLM 问答。
- 新环境验证成功后清理旧 `.venv`，不修改 Conda 全局配置。

**第一个 LLM 问答程序**

- 在 `app/main.py` 中使用 OpenAI Python SDK 的 Chat Completions 接口调用 DeepSeek。
- 按脚本位置读取项目 `.env` 的 `OPENAI_API_KEY`，填写 DeepSeek 官方密钥，不输出或提交密钥。
- 服务地址：`https://api.deepseek.com`；本次验证模型：`deepseek-flash`。
- 输入：固定问题“请用一句话解释什么是大语言模型。”。
- 请求设置：单次非流式、关闭思考、`max_tokens=200`、30 秒超时、无自动重试。
- 输出：打印问题和模型回答；为缺失密钥、连接失败、HTTP 错误及空回答提供简短提示。
- 添加标准库 `unittest` 离线测试，使用模拟响应与假密钥。

### 成果

- 完成项目初始化和环境迁移，实现“读取配置 → 发送问题 → 获取回答 → 打印结果”的最小流程。
- 7 项离线单元测试通过，覆盖正常输出、配置定位、缺失密钥、连接失败、超时、HTTP 错误和空回答。
- 实现阶段的一次真实模型请求成功，返回非空回答，程序正常退出。回答为：

  > 大语言模型是一种基于海量文本数据训练、通过预测下一个词来生成连贯自然语言的人工智能系统。

- 随后自行执行 `conda activate researchflow` 和 `python app/main.py`，终端再次显示正常问答结果并返回命令提示符。
- 代码与相关文档已同步到公开仓库 [fake-memories/ResearchFlow](https://github.com/fake-memories/ResearchFlow)。当时最新提交：`ae974ca`，`Add first DeepSeek LLM API example`。

### 遇到的问题

- **PowerShell 激活 `.venv` 时报脚本执行限制**：之后按熟悉的方式迁移到 Conda，已验证 `researchflow` 环境可以激活并运行程序。
- **希望沿用熟悉的分步环境创建流程**：确定采用 `conda create -n researchflow python=3.11 pip`，再激活环境并使用 `python -m pip install -r requirements.txt` 安装依赖。
- **密钥字段与程序读取字段不一致**：原有 DeepSeek 密钥存放在 `DEEPSEEK_API_KEY`，程序读取 `OPENAI_API_KEY`；已在本地配置中对齐，真实请求验证成功。
- **此前 Git 推送遇到 TLS 错误**：环境迁移文档通过 GitHub 接口完成同步；第一个 LLM 示例的普通推送已成功，不再作为当前阻塞。
- 当前未发现阻塞后续学习的问题；接下来需要通过复述代码流程检查自己的理解。

### 我的理解

今天梳理出的理解要点，后续继续结合代码复述和练习：

- Conda 环境提供项目使用的 Python 和依赖；激活 `researchflow` 后应使用该环境的解释器运行程序。
- API Key 用于请求身份验证，放在本地 `.env` 中；`.gitignore` 防止该文件被常规 Git 提交跟踪。
- SDK 名称是 OpenAI，`base_url` 指定实际请求的服务地址，因此本程序请求的是 DeepSeek。
- `model` 指定模型，`messages` 描述发送的消息；当前只发送一条 `user` 消息。
- 模型返回后，从 `response.choices[0].message.content` 提取回答，再打印到终端。
- 当前已完成一次 LLM 调用。后续需要学习任务如何循环推进、何时结束以及如何调用工具，才能逐步构建 Agent。

当天总结：已完成环境、代码、测试和真实请求的验证，建立了可以继续开发的基础；下一次学习前先用自己的话复述完整调用流程。

### 下一步

1. 不看笔记，解释 API Key、`base_url`、`model`、`messages` 分别起什么作用；不清楚的部分回到代码确认。
2. Day 2 学习 Agent 的基本结构与简单循环：先复述现有 LLM 调用流程，再用现有 SDK 实现带明确完成判断和最大步数的最小示例。
3. 后续参考顺序为 Prompt 设计、Memory、Tool Calling、RAG，再组合为第一个 ResearchFlow Agent；按实际掌握情况调整，不提前记为完成。

Day 2 预计安排：概念学习与代码复述 30 分钟，编码 60–90 分钟，验证与日志复盘 20 分钟。交付为可运行示例、正常结束和达到最大步数时的验证结果，以及追加的 Day 2 日志和 Git 提交；这是下次计划，尚未开始实施。

## Day 2：理解 Agent 循环与实现最小多轮示例

- 日期：2026-10-14 开始；2026-10-15 继续编码与验证。
- 状态：已完成；2026-10-15 完成学习、开发、验证和复盘，响应结构与循环上限的易错点已补充到笔记。
- 预计时间：学习与代码复述 30 分钟；编码 60–90 分钟；验证与日志复盘 20 分钟，总计约 110–140 分钟。
- 实际用时：未统计。

### 目标

1. 复述现有 LLM 调用流程，解释 API Key、`base_url`、`model`、`messages` 和响应内容读取方式。
2. 理解任务、上下文、循环与停止条件；区分单次问答、简化多轮流程和模型自主决定行动的 Agent。
3. 新增 `app/agent_loop.py`，沿用现有 SDK 和配置方式，实现保存消息历史、打印每轮结果、完成状态判断及最大步数限制。
4. 验证正常结束和达到最大步数时的退出行为，检查下一轮是否包含前轮结果；当天结束后依据证据完善记录并提交、同步 GitHub。

### 今日学习

**1. 初始化一次，每轮发起请求**

`main()` 在一次程序运行中读取 `.env`、检查密钥并创建 `client`，然后把客户端传给 `run_loop(client)`。循环不会每轮重新读取密钥、创建客户端；每轮调用 `client.chat.completions.create(...)` 发起新的模型请求。

`run_loop` 的初始消息只包含任务目标和输出要求：

```python
messages = [{"role": "user", "content": TASK}]
```

每轮把当前整个 `messages` 列表发给模型，接收完整 `response`，再从 `response.choices[0].message.content` 提取本轮文本到 `answer`。变量名区别：`messages` 是请求和历史的列表，`message` 是响应中的单条消息属性，`answer` 是提取后的字符串。

**2. 用消息列表保留上下文**

当前调用方式需要显式发送历史消息。只发送“请继续”时，请求里没有原任务和前轮回答，模型就缺少继续所需的上下文。

```python
messages.append({"role": "assistant", "content": answer})

if status == "STATUS: DONE":
    print("模型声明任务完成，结束循环。")
    break

if step < MAX_STEPS:
    messages.append({"role": "user", "content": "请继续，补充下一项任务。"})
```

- `append()` 在原列表末尾加入一项，之前的消息仍保留在列表中。
- `assistant` 标明这条历史消息是模型回复，`content=answer` 保存本轮正文和状态行。
- 没有完成且还有下一轮时，再追加一条 `user` 继续指令。
- 收到 `DONE` 或已经达到步数上限时，不再追加继续指令。

前两轮均返回 `CONTINUE` 时，发送请求前的历史如下：

| 请求轮次 | 消息数量 | 角色顺序 |
|---|---|---|
| 第 1 轮 | 1 | `user`：原任务 |
| 第 2 轮 | 3 | `user → assistant → user`：原任务、第一轮回答、继续指令 |
| 第 3 轮 | 5 | `user → assistant → user → assistant → user`：再加第二轮回答、继续指令 |

第二轮回答刚加入时确实有四条，但发送第三轮请求前还会加入继续指令，因此实际发送五条。第三轮回答保存后有六条；达到上限后不会再发第四轮请求。

**3. 最大步数与两种退出路径**

```python
for step in range(1, MAX_STEPS + 1):
    # 每轮请求模型并检查回复
    ...
    if status == "STATUS: DONE":
        break
else:
    print(f"达到最大步数（{MAX_STEPS}），任务尚未完成。")
```

这是循环结构示意。`range` 不包含结束值，所以 `MAX_STEPS=3` 时，`range(1, 4)` 只产生 1、2、3，最多请求三次。

- **完成退出**：任意一轮收到有效 `STATUS: DONE`，执行 `break`，不进入 `for` 的 `else`。
- **上限退出**：第三轮仍是 `STATUS: CONTINUE`，循环正常耗尽，执行 `else`，报告任务尚未完成。
- 第三轮恰好收到 `DONE` 时仍算完成，执行 `break`，不会再打印上限提示。
- 达到最大步数就停止，不是超过上限后才停止。即使模型一直要求继续，也不会发第四次请求。

这里的 `else` 属于 `for`，不是前面的 `if`；只有循环正常耗尽且没有被 `break` 中断时才执行。请求异常或格式错误会直接停止程序，不会误报完成。

**4. 完成状态是约定的文本格式**

`STATUS: CONTINUE` 和 `STATUS: DONE` 是程序通过提示约定的文本，不是 SDK 自动提供的任务完成字段。

```python
lines = answer.splitlines()
status = lines[-1].strip()
body = "\n".join(lines[:-1]).strip()
```

- `splitlines()` 按行拆分字符串；`[-1]` 取最后一行；`[:-1]` 取最后一行之前的内容。
- 最后一行是状态，前面的内容是正文；`"\n".join(...)` 把正文行重新拼成字符串。
- 代码要求正文非空，末行完整等于两个允许状态之一，且正文里不能再有独立的合法状态行。
- 不能使用 `"DONE" in answer` 判断完成，因为正文可能只是提到这个词，或出现 `NOT_DONE` 等其他内容。
- 当前检查的是回复格式与退出信号，并没有自动检查是否真有三项任务、每项是否包含有效练习或是否满足 100 字限制；内容还需要查看。

**5. 三种限制分别控制什么**

| 设置 | 控制对象 | 当前设置 |
|---|---|---|
| `MAX_STEPS` | 多轮循环最多发起几次请求 | 3 |
| `max_tokens` | 单次回复的生成长度，以 token 计数 | 200 |
| `max_retries` | SDK 遇到可重试的请求错误时自动重试几次 | 0 |

限制单次回答长度不能代替限制循环轮数；一个回答很短的程序也可能无限请求，所以两种限制都需要考虑。

**6. 多轮流程、Agent 与记忆的区别**

- 单次问答只发起一次请求，直接输出回答。
- 当前示例按照程序固定的循环推进，通过历史消息继续任务，再用完成状态和最大步数停止，是学习循环控制的简化流程。
- 自主 Agent 通常还会根据任务和执行反馈决定下一步行动、选择工具，并根据结果调整过程。多次调用 LLM 本身不足以说明已经实现这些能力。
- 当前 `messages` 只存在本次运行的内存中，再次启动程序会从原任务重新开始；持久化记忆需要额外保存和读取机制。
- 模型声明 `DONE` 只表示它发出了完成信号，不能证明内容正确，也不能证明输出中提到的工具调用或记忆功能已经实现。

参考：[OpenAI：对话状态](https://developers.openai.com/api/docs/guides/conversation-state)、[Anthropic：Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)。

### 今日开发

- 新增 `app/agent_loop.py`，沿用 Day 1 的 SDK 和配置，实现消息历史、完整状态行检查、完成退出与最多三轮限制，并处理空回答、非法格式和 API 异常。
- 新增 `tests/test_agent_loop.py` 的 7 项离线测试，覆盖消息历史、两种退出路径、边界条件和异常；保留 Day 1 程序及原有测试。
- 更新 `README.md` 的运行说明。我运行了多轮示例，查看输出，并结合代码理解每一轮是怎样推进的。
- 复盘后调整 Day 3–6 的学习路线：把 Prompt、JSON 输出和论文搜索工具结合起来，先直接调用函数，再学习模型原生工具调用；同步完善项目说明与协作约定。

### 成果

- `conda run -n researchflow python -m unittest discover -s tests -v`：14 项测试全部通过（Day 1 七项、Day 2 七项）。
- 离线测试验证了两轮完成、三轮达到上限、第三轮完成、历史传递及错误处理。
- 真实调用验证通过：运行三轮，状态为 `CONTINUE → CONTINUE → DONE`，进程退出码为 0。
- 我在本地运行后看到了三项带目标和练习的学习任务，第三轮显示完成提示，中文正常。正常结束有运行输出作为证据，上限退出由离线测试验证。
- `git diff --check` 通过；确认 `.env` 和 Python 缓存目录仍被 Git 忽略。
- Git 提交和同步：循环代码、测试和说明已提交并同步到 [fake-memories/ResearchFlow](https://github.com/fake-memories/ResearchFlow) 的 `main` 分支，代码提交为 `ae45636`（`Add bounded multi-turn LLM loop`）；学习笔记与复盘提交为 `aa14c09`（`Complete Day 2 study notes and review`），已同步。

### 遇到的问题

- 把完整响应和回复消息混在一起：`response` 保存完整响应，单条回复在 `response.choices[0].message` 中，文本是它的 `.content`。
- 数第三轮请求的消息时漏算了继续指令：第二轮回答保存后有四条，加入继续指令后才是五条。
- 循环边界容易写成“超过最大步数才停止”：实际是达到三轮后仍未完成就停止，不会执行第四轮。
- 发现重复独立状态行可能被误当作正文，已修正判断并通过测试。
- 验证时遇到临时目录权限和输出捕获乱码问题；调整运行方式后测试通过，本地终端中文正常。目前没有程序运行阻塞。

### 我的理解

- 整个程序分为准备阶段和循环阶段：先读取配置并创建客户端，再初始化保存任务目标的 `messages`，每轮用它请求模型。
- 补充：请求得到的是完整 `response`，通过 `response.choices[0].message.content` 取出文本到 `answer`，不能把完整响应当作一条消息或字符串。
- 每轮保存一条 `assistant` 回答；如果未完成且仍有下一轮，再加入一条 `user` 继续指令，下一次请求带着累积历史继续。
- 最后一行是有效 `STATUS: DONE` 时，通过 `break` 结束；补充：达到 `MAX_STEPS` 仍未完成时，循环耗尽并提示未完成，不会超过上限。
- 提示中的任务目标负责说明要做什么，代码中的状态检查和循环上限负责控制怎样继续、何时停止；回答内容是否合理还要查看。
- 后续复习重点：完整响应的访问路径、消息追加的先后顺序，以及 `for-else` 的执行条件。
- 当天总结：在单次问答的基础上增加了消息历史、完成状态和最大步数，形成可运行的多轮示例。真实运行正常结束，离线测试覆盖了完成退出和上限退出。完整流程可以分为“准备客户端 → 初始化任务消息 → 每轮请求与提取文本 → 保存历史 → 判断继续或结束”。复习时重点检查完整响应的访问路径、消息顺序和循环边界。

### 下一步

Day 3 调整为 **Prompt 基础 + JSON 结构化输出 + 第一个工具函数**，预计约 3 小时，尚未开始。

1. **Prompt 基础，40 分钟**：按角色、任务、上下文、约束、输出格式组织提示；用论文搜索请求作为练习，保存一次实际输入输出。重点是让模型明确要整理哪些参数，而不是凭空生成论文信息。
2. **JSON 输出，60 分钟**：使用 DeepSeek JSON Output，提示中明确 JSON 格式并提供样例；用标准库 `json.loads()` 解析，检查必需字段、类型及范围。有效 JSON 不等于字段一定正确，空回答、截断和格式错误也要处理。
3. **工具函数，60 分钟**：实现 `search_paper(query, max_results=3)`，先由 Python 直接调用，再接入真实论文检索接口，优先参考 arXiv API。返回论文标题、来源链接及可获取的年份信息，支持无结果和请求失败的清晰提示。
4. **验证与复盘，20 分钟**：验证正常 JSON、缺字段、错误类型和非法 JSON；检查工具输入限制、无结果和请求失败。保存至少一次真实检索的关键词、来源及实际返回结果，并补全笔记与 Git 收尾。

计划中的搜索参数格式：

```json
{"query": "AI agents", "max_results": 3}
```

`query` 是非空字符串，`max_results` 是 1–5 的整数；只有通过检查后才能作为工具参数使用。工具测试可以用固定离线样例，但样例不是实时搜索结果；网络失败时如实记录，不用样例冒充真实检索成功。

交付目标：结构化输出示例、`app/paper_tools.py` 中的搜索函数、相关验证，以及 `docs/day3_prompt_and_tools.md` 中的定义、关键代码和实际输入输出。现有 Day 1、Day 2 示例保留。

阶段能力边界：Day 3 的工具由 Python 程序直接调用；Day 4 再让模型通过 `tool_calls` 选择函数和参数，Python 负责实际执行并回传结果。普通函数调用、JSON 格式输出与模型原生 Tool Calling 分开学习和记录。

参考：[DeepSeek JSON Output](https://api-docs.deepseek.com/zh-cn/guides/json_mode/)、[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)、[arXiv API Basics](https://info.arxiv.org/help/api/basics.html)。

## Day 3：Prompt 基础、JSON 参数校验与论文搜索工具

- 日期：2026-10-15 开始；2026-10-16 完成运行结果确认与学习复盘。
- 状态：已完成；参数校验、模型 JSON 输出与论文检索串联已验证，易混淆的类型和函数职责已补充说明，后续继续巩固。
- 预计时间：Prompt 40 分钟；JSON 输出与校验 60 分钟；工具函数 60 分钟；验证与复盘 20 分钟，总计约 3 小时。
- 实际用时：未统计。

### 目标

1. 按角色、任务、上下文、约束和输出格式编写搜索参数提示词。
2. 解析并校验 JSON 搜索参数，再接入模型的实际 JSON 输出。
3. 实现论文搜索函数，由 Python 直接调用并返回有来源的论文结果。
4. 验证正常输入和错误输入，保存真实模型与检索结果，结束时完成复盘及 Git 同步。

### 今日学习

**1. Prompt 与参数生成**

Prompt 是给模型的任务说明，可明确角色、任务、上下文、约束和输出格式。例如把“搜索两篇 RAG 论文”整理为 `{"query": "retrieval augmented generation", "max_results": 2}`。本阶段模型负责整理搜索条件，论文信息由后续真实搜索工具取得；“相关性高”要结合检索结果判断，不能只靠提示中的要求证明。

**2. JSON 解析与参数校验**

`answer` 保存 JSON 文本；`params = json.loads(answer)` 将文本解析为 Python 数据。JSON 对象解析后是字典，但顶层也可能是列表或其他值，因此解析后先检查是否为字典，再读取字段。

- `2` 是整数，`"2"` 是字符串；两者都是合法 JSON 值，解析时不会自动互相转换。
- `max_results=0` 的类型正确，但不符合 1–5 的范围要求。
- 合法 JSON 不等于参数合格。完整检查包含输入是否为空、JSON 格式、顶层类型、必需字段、字段类型和数值范围。

**3. 关键词检查与错误处理**

先通过 `"query" not in params` 检查字段是否缺失，避免直接读取时出现 `KeyError`。用 `isinstance(query, str)` 检查字符串类型，再执行 `query.strip()` 去掉两端空白，最后用 `if not query` 拒绝空关键词。

数量先使用 `type(max_results) is int` 检查，再使用 `1 <= max_results <= 5` 判断范围。补充：Python 中 `bool` 是 `int` 的子类，严格类型检查可以排除布尔值，也会拒绝 `2.0` 和 `"2"`。

不合格输入使用 `raise ValueError(...)` 抛出错误；调用方用 `try/except` 决定怎样处理。函数只有校验全部通过后才返回整理好的参数字典，后续搜索应放在成功返回之后。

**4. 模型 JSON 输出与两条消息**

`system` 消息放参数整理规则，`user` 消息放具体需求。请求设置 `response_format={"type": "json_object"}`，并在提示中明确 JSON 要求和格式样例。模型仍返回文本，提取 `response.choices[0].message.content` 后再调用已有的 `parse_search_params()`。

JSON 模式负责输出格式，Python 负责字段、类型和范围。请求返回后先检查空 `choices` 与 `finish_reason`；`length` 表示长度限制导致生成停止，不能把截断回复当作成功；这里只接受 `stop`，再检查内容是否为空。`finish_reason` 是接口提供的生成结束原因，和 Day 2 文本中自行约定的 `STATUS: DONE` 不同，也不证明答案内容正确。

实际参数的关键词含义、数量是否符合原需求仍需核对。例如数量为整数 `3` 可以通过 1–5 的范围检查，但如果用户明确要两篇，它仍然没有忠实表达需求。

**5. Python 工具函数与真实论文检索**

工具函数接收参数、执行一项具体工作并返回结果。`search_paper(query, max_results=3)` 返回论文列表，每项包含标题 `title`、来源链接 `url`、首次提交年份 `year`；没有结果时返回空列表。函数不打印，入口使用 `print_papers()` 展示结果。

请求使用现有 `requests`，通过 `params` 传递 `search_query`、`max_results` 和相关性排序设置。关键词使用 `all:"检索短语"`；`response.raise_for_status()` 检查 HTTP 错误。arXiv 返回 Atom/XML，使用标准库 `ElementTree` 解析，再按命名空间读取论文条目。模型 JSON 和论文接口 XML 是两个接口的不同数据格式，不能都用 `json.loads()` 读取。

标题来自 `<title>`，来源链接来自 `<id>`，年份来自 `<published>`，表示 arXiv 首次提交年。日期缺失或无效时保留未知，不猜测期刊发表年份。无结果与网络失败不同：前者是正常的空列表，后者要明确报告失败。

`python -m app.paper_tools` 用固定参数直接调用工具；`python -m app.json_output --search` 先请求模型、校验参数，再由 Python 固定调用工具。`--search` 是命令行开关，省略时仍只生成参数。当前没有模型原生 `tool_calls`，也没有将工具结果回传给模型。

### 今日开发

- 新增 `app/structured_output.py`，提供 `parse_search_params(answer)` 和 8 组固定输入的离线演示。函数返回去掉关键词两端空白的 `query` 与通过类型、范围检查的 `max_results`。
- 新增 `tests/test_structured_output.py` 的 9 项测试，覆盖参数边界、缺字段、空白关键词、非法 JSON 和错误类型等情况。
- 新增 `docs/day3_prompt_and_tools.md`，保存提示练习、概念、关键代码和实际离线运行结果；更新 `README.md` 的运行方式与项目进度。
- 离线示例只使用 Python 标准库，不读取密钥或触网；我已在本地运行 8 组示例，结果与预期一致，并有终端截图。
- 新增 `app/json_output.py`，沿用现有 SDK 和密钥配置，请求模型生成 JSON 参数，再复用已有函数校验；从项目根目录使用 `python -m app.json_output` 运行。
- 新增 `tests/test_json_output.py` 的 9 项离线测试，覆盖 JSON 请求、空回复、截断、异常结束、字段校验及 API 错误；同步更新文档。
- 我在本地运行模型 JSON 示例，截图中的关键词为 `Retrieval-Augmented Generation`、数量为整数 `2`，校验通过。
- 新增 `app/paper_tools.py` 与 10 项离线工具测试，使用已有 `requests` 和标准库完成论文检索；更新 `app/json_output.py`，新增 `--search` 串联入口与 3 项集成测试。

### 成果

- 在现有 `researchflow` 环境（Python 3.11.17）运行离线示例，8 组输入均显示对应的通过或失败提示，退出码 0。
- 数量为 `2` 时通过；`"2"` 提示必须是整数；`0` 提示必须在 1–5 之间。关键词 `" RAG "` 被整理为 `"RAG"`。
- 离线校验阶段的完整 23 项测试通过；接入模型入口后新增 9 项测试，完整 32 项测试在沙箱外运行全部通过。
- 真实运行 `conda run -n researchflow python -m app.json_output` 成功，需求为“帮我找两篇关于 RAG（检索增强生成）的论文。”；模型实际输出 `{"query": "retrieval-augmented generation", "max_results": 2}`，Python 校验通过，进程退出码 0。
- 新增工具与串联测试后，完整 45 项离线测试在沙箱外全部通过。
- 真实运行 `python -m app.paper_tools` 与 `python -m app.json_output --search`，均在现有 Conda 环境中成功，退出码均为 0；关键词为 `retrieval-augmented generation`，模型数量为整数 `2`，工具实际返回两篇论文，完整标题和来源保存在 `docs/day3_prompt_and_tools.md`。
- 实际结果：2024 年的 *Automated Literature Review Using NLP Techniques and LLM-Based Retrieval-Augmented Generation*（[arXiv:2411.18583v1](http://arxiv.org/abs/2411.18583v1)）；2025 年的 *Riddle Me This! Stealthy Membership Inference for Retrieval-Augmented Generation*（[arXiv:2502.00306v2](http://arxiv.org/abs/2502.00306v2)）。年份为首次提交年，未逐篇阅读全文。
- 本地完整流程也已运行，截图显示模型生成 `{"query": "retrieval-augmented generation", "max_results": 2}`，Python 校验通过，并返回上述两篇论文的标题、年份与来源链接，终端已返回命令提示符。2026-10-16 确认了这份运行证据。
- Git 收尾范围为 3 个程序文件、3 个测试文件、Day 3 文档、README 和学习档案；提交与同步进行中，完成后补充实际结果。

### 遇到的问题

- 最初没有区分数字 `2` 与字符串 `"2"`；结合双引号、Python 类型和计算示例，已能正确预测三种数量输入的检查结果。
- 曾把 `generate_search_params()` 理解为访问 arXiv 的步骤。正确分工是：它请求 DeepSeek 生成并校验参数；`search_paper()` 内的 `requests.get()` 才访问 arXiv，并在同一函数中解析 XML、取得论文列表。这个区别已明确，后续继续结合代码巩固。
- 完整测试曾因沙箱限制无法访问临时目录而失败；更换临时目录仍失败，沙箱外重跑后 23 项通过，测试产生的临时目录已清理。没有修改原有测试或环境配置。
- 结束复盘时暂时没有不清楚的地方，也没有阻塞后续学习的问题。

### 我的理解

- 今天学习了 Prompt 基础和 JSON 结构化输出，实现了第一个论文搜索工具。实际用时未统计。
- 我最初通过读代码预测 `2`、`"2"` 和 `0` 对应的分支，没有亲自敲代码运行；之后运行了完整离线示例，实际结果与预测一致。
- JSON 格式正确后，仍要检查字段是否存在、类型是否正确、值是否符合要求。数量 `0` 虽然是整数，但不符合 1–5 的约定。
- 我已理解目前讨论的关键词检查和数量检查代码；接下来结合完整函数的实际输出继续巩固。
- 模型负责生成搜索条件，Python 校验参数并显式调用工具。`params` 是参数字典，`papers` 是工具返回的论文列表；`generate_search_params()` 访问 DeepSeek，`search_paper()` 访问 arXiv 并整理结果。
- 补充：模型 JSON 模式、`system`/`user` 消息与 `finish_reason` 的作用已结合新代码说明，接下来需要阅读和复述完整请求流程。
- 补充：论文工具与参数串联已加入项目，仍需结合新代码复述 HTTP 请求、XML 解析、返回列表以及 Python 调用工具的过程。
- 当天总结：完成了 Prompt 基础、JSON 参数生成与校验，以及第一个论文搜索工具；离线示例和完整流程均已运行，测试与真实检索都有证据。结束时暂时没有不清楚的地方，之后结合新任务继续巩固数据格式和模型与 Python 的分工。

### 下一步

Day 4 计划学习原生 Tool Calling，预计约 170 分钟（2 小时 50 分钟），尚未开始：

1. **复习分工，15 分钟**：复述 `generate_search_params()` 与 `search_paper()` 的职责，确认模型提出请求、Python 实际执行工具。
2. **工具描述与调用消息，35 分钟**：为 `search_paper` 定义工具名称、用途和参数结构，认识 `tool_calls` 与普通 JSON 文本的区别。
3. **校验和执行，50 分钟**：新增 `app/tool_calling.py`，只执行已登记的搜索函数，复用现有 JSON 参数校验；处理未知工具、非法参数与执行失败。
4. **结果回传，40 分钟**：保存模型的工具调用消息，按对应 `tool_call_id` 回传真实工具结果，再请求模型基于检索来源回答。先完成一次工具调用闭环，多步自主循环留到 Day 5。
5. **验证与复盘，30 分钟**：用离线样例验证正常路径、无需工具、未知工具、非法参数和工具失败；再保存一次真实调用闭环及带来源的最终回答，更新笔记并收尾。

计划交付为 `app/tool_calling.py`、相关离线测试、`docs/day4_tool_calling.md` 与一次真实工具调用记录；继续使用现有 SDK、原生 Python 和已有工具，不增加大型框架。

## 每日记录模板

复制以下模板，将新一天记录追加在已有 Day 记录之后、此模板之前。问题、理解和总结在当天结束时填写完整；历史记录保留，仅纠正错误或补充事实。

```markdown
## Day X：当天主题

- 日期：YYYY-MM-DD
- 状态：进行中 / 已完成 / 部分完成（说明原因）
- 预计时间：学习 __；编码 __
- 实际用时：按实际填写；未记录时写“未统计”

### 目标

1. 完成的开发任务：
2. 需要理解的概念：
3. 验证方法和交付成果：

### 今日学习

- 概念的含义、用途和正确结论：
- 关键代码、执行流程和具体例子：
- 容易混淆的地方及补充解释：

### 今日开发

- 修改了什么文件，实现了什么行为：

### 成果

- 运行或测试结果、可验证的输出：
- Git 提交和同步情况：

### 遇到的问题

- 问题、原因、处理方式和当前状态；确实没有阻塞时如实说明：

### 我的理解

- 用自己的话解释关键概念及代码流程：
- 仍不清楚的部分：
- 当天总结：完成了什么，哪些理解还需要验证：

### 下一步

- 下次任务及验证方式：
```
