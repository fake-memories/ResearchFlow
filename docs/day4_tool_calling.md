# Day 4：原生 Tool Calling

本日先完成一次工具调用闭环，多步自主选择行动留到 Day 5。继续使用原生 Python、现有 OpenAI SDK、JSON 参数校验和 arXiv 搜索函数，不增加依赖。

## 运行方式

在项目根目录使用现有环境：

```cmd
conda activate researchflow
python -m app.tool_calling
```

也可以不激活环境：

```cmd
conda run -n researchflow python -m app.tool_calling
```

默认需求是“帮我找两篇关于 RAG（检索增强生成）的论文。”。指定其他需求：

```cmd
python -m app.tool_calling --request "请解释什么是 Tool Calling。"
```

入口沿用项目 `.env` 配置。以上命令会请求真实模型；模型请求论文搜索时还会访问 arXiv。工具 ID、模型参数、实际检索结果和最终回答会打印到终端，密钥不输出。

## 从 Day 3 到 Day 4

| 阶段 | 模型提供什么 | Python 做什么 |
|---|---|---|
| Day 3 | `content` 中的 JSON 参数文本 | 校验参数，按 `--search` 开关固定执行搜索 |
| Day 4 | `tool_calls` 中的工具名、参数和调用 ID，或直接回答 | 检查请求、执行已允许的函数、按 ID 回传结果，再请求模型回答 |

`generate_search_params(client, request)` 会请求模型生成参数；`parse_search_params(answer)` 处理已有的 JSON 文本。Day 4 已从 `function.arguments` 得到模型参数，应复用解析函数，不再请求模型重新生成参数。

## 工具描述和实际函数

`TOOLS` 是提供给模型的工具说明，包含名称、用途和参数结构。`parameters.properties` 描述各字段类型，`required` 要求模型提供哪些字段；Python 函数的默认值不会自动改变这份要求。

工具描述没有实现搜索，也不会自动执行本地函数。第一次请求通过 `tools=TOOLS` 让模型看到说明；实际执行由 `execute_tool_call()` 完成，只允许 `search_paper`，不用 `eval()` 或按任意模型名称执行代码。

```python
if tool_call.function.name != "search_paper":
    raise ValueError("未知工具:" + tool_call.function.name)

params = parse_search_params(tool_call.function.arguments)
papers = search_paper(params["query"], params["max_results"])
```

`arguments` 是 JSON 字符串；`params` 是校验后的字典；`papers` 是搜索返回的论文列表。合法 JSON 不等于参数合格。数量 `"2"` 是字符串，会在参数校验时抛出 `ValueError`，不会执行后面的搜索。

`raise` 主动报告异常，`except` 在调用方捕获异常并决定如何处理。`search_paper(params)` 会把整个字典传给关键词参数，正确写法是分别传入关键词和数量。

## 两次模型请求之间发生了什么

```text
用户需求
  → 第一次请求模型，提供 tools
  → 模型提出工具调用请求
  → Python 检查工具名、解析并校验参数
  → Python 执行 search_paper()
  → 保存 assistant 调用请求和 tool 执行结果
  → 第二次请求模型，根据实际检索结果组织回答
```

```python
messages.append(message.model_dump(exclude_none=True))
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(papers, ensure_ascii=False),
})
```

- `assistant` 消息保存模型提出的调用请求，其中包括工具名称、参数和调用 ID。`model_dump()` 将 SDK 消息对象转成字典，保留完整 `tool_calls`；不能只保存可能为空的 `content`。
- `tool` 消息保存 Python 执行工具后返回的结果。`tool_call_id` 对应具体调用的 `id`，不是工具名称。
- `json.loads()` 将 JSON 文本解析为 Python 数据；`json.dumps()` 将论文列表转成消息正文所需的字符串。`ensure_ascii=False` 保留可读中文。
- `print(papers)` 只在终端显示，不会让模型看到结果。必须加入 `messages`，并在下一次请求中发送。

正常搜索路径最多请求模型两次、执行搜索一次。模型直接回答时，请求模型一次，不执行搜索，也不发第二次请求。`return` 结束当前函数，返回调用方；它不会自动结束调用方后续的代码，因此两条路径在同一个完整流程函数中分开处理。

本日明确限制为一条工具调用，多条请求会报错，不会只执行第一条后带着未完成的调用历史继续。第二次请求只发送已有历史，不提供工具；如果仍收到新的调用请求，则明确拒绝继续。

## 无结果与执行失败

| 工具情况 | 实际含义 | 当前处理 |
|---|---|---|
| 正常返回论文列表 | 已取得这次检索的数据 | 回传模型，整理标题、年份和链接 |
| 正常返回 `[]` | 本次检索没有匹配结果 | 回传空列表，说明可调整关键词 |
| 网络、HTTP 或数据异常 | 没有正常取得检索结果 | 报告失败并停止，不转换成空列表 |

超时不能说明没有相关论文。若将失败伪装成 `[]`，会丢失“本次未能完成搜索”的信息。当前入口用 `try/except` 显示清晰错误；以后也可以将明确的错误结果回传模型，由模型说明失败。

论文工具返回标题、来源链接和首次提交年份，不含全文，最终回答不能据此声称阅读全文或验证了论文结论。

## 验证记录

日期：2026-10-16。Day 4 已完成开发、两条路径的本地运行确认和学习复盘，学习档案在当天收尾时集中更新。以下区分开发验证和本地运行证据。

### 离线测试

- 新增 `tests/test_tool_calling.py`，19 项测试通过，覆盖参数校验、未知工具、调用 ID、完整消息历史、直接回答、空结果、检索失败、截断、空响应和多条调用限制等情况。
- 在现有 `researchflow` 环境（Python 3.11.17）运行完整测试，64 项全部通过：

  ```cmd
  python -B -m unittest discover -s tests -q
  ```

- 首次完整测试在沙箱中因 Day 1 的系统临时目录写入权限失败；在沙箱外用同一环境、同一套测试重跑后通过，没有为此修改原有测试或环境配置。
- 模拟数据只检查程序行为，不作为真实检索结果。Day 4 测试验证了：错误参数不会执行搜索，工具失败不会发起第二次模型请求；成功的空列表会如实回传。

### 真实工具调用闭环

实际运行：`python -B -m app.tool_calling`，使用现有环境和本地配置，退出码为 0。

- 用户需求：帮我找两篇关于 RAG（检索增强生成）的论文。
- 模型返回的调用 ID：`call_00_4LJb3KQl7875epwdjxMb5686`。
- 模型选择的工具：`search_paper`。
- 模型原始参数：`{"query": "Retrieval-Augmented Generation", "max_results": 2}`。
- Python 校验后执行真实 arXiv 检索，返回以下两条记录：

| 标题 | 首次提交年份 | 来源 |
|---|---|---|
| Automated Literature Review Using NLP Techniques and LLM-Based Retrieval-Augmented Generation | 2024 | [arXiv:2411.18583v1](http://arxiv.org/abs/2411.18583v1) |
| Riddle Me This! Stealthy Membership Inference for Retrieval-Augmented Generation | 2025 | [arXiv:2502.00306v2](http://arxiv.org/abs/2502.00306v2) |

程序按对应调用 ID 回传真实结果，第二次模型请求成功。最终回答列出了上述两篇论文及其首次提交年份、来源链接，与工具返回的记录一致。这里只验证检索与消息回传，没有阅读全文或评价论文结论。

### 本地运行确认

- 在现有 `researchflow` 环境中运行 `python -m app.tool_calling`，终端截图显示 `search_paper` 调用、有效 ID、关键词 `Retrieval-Augmented Generation` 和整数数量 `2`，实际返回上表两篇论文，最终回答列出一致的标题、年份和来源链接，程序回到命令提示符。
- 再运行 `python -m app.tool_calling --request "请用一句话解释 Tool Calling，不需要检索论文。"`，截图中输出从用户需求直接到最终回答，没有工具调用或结果信息，并回到命令提示符。结合代码与离线请求计数测试，对应一次模型请求、零次搜索的直接回答分支。
- 搜索结果仅包含标题、年份和链接。回答末尾对论文方向的概括属于根据标题作出的推断，没有读取摘要、全文或验证论文结论。

运行结果证明当前流程可用；完整代码的组合、异常处理和边界控制仍通过后续需求修改与调试继续练习。

参考：[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)。
