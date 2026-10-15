# Day 3：Prompt、JSON 参数与论文搜索工具

日期：2026-10-15 开始，2026-10-16 完成复盘。Day 3 已完成：JSON 参数校验、模型 JSON 输出、论文搜索工具及串联均已验证。

## 1. Prompt 负责说明要生成什么

Prompt 可以按角色、任务、上下文、约束和输出格式组织。本阶段让模型整理搜索条件，论文标题与来源将在后续由真实搜索工具取得。

实际请求使用两条消息。`system` 消息规定通用的参数整理规则：

```text
你是论文搜索参数整理助手。
根据用户需求，提取搜索关键词 query 和返回数量 max_results。
这些参数将交给 Python 搜索函数使用；当前只整理参数，不生成论文列表。

要求：
- query 是非空字符串，使用表达主题的英文搜索关键词，缩写优先展开为全称。
- max_results 是 1–5 的整数，用户未指定时默认为 3。
- 只输出包含 query 和 max_results 两个字段的合法 JSON，不附加解释或 Markdown 代码块。

示例 JSON：
{"query": "AI agents", "max_results": 3}
```

`user` 消息提供具体需求：`帮我找两篇关于 RAG（检索增强生成）的论文。`。规则和需求分开后，更换需求时可以复用相同的规则。

“相关性高”需要结合实际检索结果检查，参数生成阶段不能证明已经搜索到相关论文。提示中的默认数量也不会自动成为解析函数的行为：当前函数要求两个字段都明确存在，缺字段时报告错误。

## 2. JSON 文本与 Python 字典

```python
import json

answer = '{"query": "RAG", "max_results": 2}'
params = json.loads(answer)
```

`answer` 是字符串。这个例子中，`json.loads()` 把 JSON 对象解析成 Python 字典，之后可以使用 `params["query"]` 读取字段。JSON 的顶层也可以是列表、数字等，因此解析成功后还需要检查是否为字典。

| JSON 中的值 | Python 类型 | 当前参数检查结果 |
|---|---|---|
| `2` | `int`，整数 | 通过类型与范围检查 |
| `"2"` | `str`，字符串 | 类型错误 |
| `0` | `int`，整数 | 范围错误 |

合法 JSON 不等于参数合格。解析负责读取数据，校验负责判断数据是否满足程序要求。

## 3. 参数校验函数

实现位置：`app/structured_output.py` 中的 `parse_search_params(answer)`。

执行顺序：检查输入文本 → `json.loads()` → 确认顶层是字典 → 检查必需字段 → 检查并整理关键词 → 检查数量类型与范围 → 返回参数字典。

关键词的关键代码：

```python
if "query" not in params:
    raise ValueError("缺少 query 字段")

query = params["query"]
if not isinstance(query, str):
    raise ValueError("query 必须是字符串")
query = query.strip()
if not query:
    raise ValueError("query 不能为空")
```

先检查键是否存在，避免直接读取缺失字段导致 `KeyError`；先检查类型，再调用字符串的 `.strip()`。空字符串和只包含空白的关键词都不合要求。

数量的关键代码：

```python
max_results = params["max_results"]
if type(max_results) is not int:
    raise ValueError("max_results 必须是整数")
if not 1 <= max_results <= 5:
    raise ValueError("max_results 必须在 1–5 之间")
```

补充：Python 的 `bool` 是 `int` 的子类，因此这里使用严格类型检查，排除 JSON 中的 `true`、`false`。`2.0` 也不是整数类型。函数不自动把 `"2"` 转成 `2`。

`raise ValueError(...)` 将错误交给调用方。演示入口逐例使用 `try/except` 打印错误，再继续下一个例子；未来的工具调用方只有收到正常返回的参数后才能继续执行搜索。

## 4. 实际离线运行与验证

在项目根目录执行：

```cmd
conda run -n researchflow python app\structured_output.py
```

2026-10-15 实际运行成功，退出码 0。入口包含 8 组固定输入，结果如下；这些是离线样例，不是模型或论文接口返回的数据。

| 输入情况 | 实际结果 |
|---|---|
| `{"query": " RAG ", "max_results": 2}` | 校验通过，返回 `{'query': 'RAG', 'max_results': 2}` |
| `max_results` 为 `"2"` | `max_results 必须是整数` |
| `max_results` 为 `0` | `max_results 必须在 1–5 之间` |
| 缺少 `query` | `缺少 query 字段` |
| `query` 为 `123` | `query 必须是字符串` |
| `query` 为三个空格 | `query 不能为空` |
| JSON 缺少末尾右花括号 | `JSON 格式错误，请检查双引号、逗号和括号` |
| 顶层为 `[]` | `JSON 顶层必须是对象` |

演示会捕获预期的输入错误，因此错误样例不会让整个演示进程失败；直接调用函数时，不合格输入仍会抛出 `ValueError`。

离线测试命令：

```cmd
conda run -n researchflow python -m unittest discover -s tests -v
```

参数校验的 9 项测试覆盖正常输入、1 和 5 的边界、空输入、非法 JSON、顶层类型、缺字段、关键词类型与空白、数量类型和越界。离线校验阶段完整 23 项测试通过，接入模型入口后 32 项通过，加入论文工具与串联后完整 45 项通过。验证环境的沙箱曾阻止原有测试访问新建的临时目录，完整测试在沙箱外运行；没有为此修改原有测试或环境配置。

## 5. 模型 JSON 输出与实际调用

新增 `app/json_output.py`，复用 `parse_search_params()`，不重复编写校验逻辑。从项目根目录运行：

```cmd
conda run -n researchflow python -m app.json_output
```

使用 `-m` 按模块运行，能够导入同一项目中的 `app.structured_output`。该入口读取现有本地配置，发起一次真实请求，使用 `deepseek-flash`、关闭思考、200 token 上限、30 秒超时和无自动重试。

关键请求代码：

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ],
    response_format={"type": "json_object"},
    max_tokens=200,
    extra_body={"thinking": {"type": "disabled"}},
)
```

JSON 模式约束输出格式，提示仍需明确 JSON 要求并提供样例；空内容和截断仍要处理。参考：[DeepSeek JSON Output](https://api-docs.deepseek.com/zh-cn/guides/json_mode/)。

返回后先检查 `choices` 和 `finish_reason`：

- `length` 表示达到生成或上下文长度限制，拒绝该回复并提示调整长度。
- 仅接受正常结束的 `stop`；其他结束原因也不进入成功路径。
- 然后提取 `message.content` 并检查是否为空，再交给 `parse_search_params()`。

`finish_reason` 是接口返回的生成结束原因，和 Day 2 在回复文本中自行约定的 `STATUS: DONE` 不同；`stop` 也不能证明内容正确。参考：[DeepSeek Chat Completions](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)。

2026-10-15 的一次真实运行输出如下，退出码 0：

```text
用户需求：帮我找两篇关于 RAG（检索增强生成）的论文。
模型原始 JSON：
{"query": "retrieval-augmented generation", "max_results": 2}
校验通过的搜索参数：{'query': 'retrieval-augmented generation', 'max_results': 2}
```

这次实际返回的英文关键词与主题一致，整数 `2` 与需求数量一致；后续运行的措辞可能变化。字段校验只检查结构、类型和范围，没有自动验证关键词含义或数量是否忠实于需求，语义仍需核对。该默认命令只生成参数；添加后文的 `--search` 开关后继续执行论文检索，仍不使用原生 Tool Calling。

`tests/test_json_output.py` 最初有 9 项离线测试，覆盖 JSON 模式请求、两条消息传递、空回复、截断与异常结束、参数校验、缺失密钥和 API 错误提示；接入搜索后增加 3 项串联测试，共 12 项。测试使用模拟响应和假配置，不读取真实密钥、不触网；真实调用单独验证。

## 6. 第一个工具函数：论文搜索

实现位置：`app/paper_tools.py`。工具仍然是普通 Python 函数，接收参数、完成一项具体工作并返回数据：

```python
papers = search_paper("retrieval-augmented generation", max_results=2)
```

返回值是论文列表，每项包含 `title`、`url`、`year`。搜索函数不打印，显示由 `print_papers()` 负责，便于后续把返回值交给其他代码。

**请求与解析流程：**

1. 工具再次检查关键词和数量，因为它也可能被直接调用。
2. 使用 `requests.get(..., params=..., timeout=30.0)` 请求 arXiv，`params` 负责 URL 参数编码。
3. `search_query` 为 `all:"检索短语"`，当前用于简单关键词短语；`sortBy="relevance"` 按接口相关性排序。请求中的 `max_results` 控制最多返回多少篇。
4. `response.raise_for_status()` 检查 HTTP 错误；成功后用 `ET.fromstring(response.content)` 解析 Atom/XML，再按命名空间读取 `<entry>`。
5. 从 `<title>` 读取标题、`<id>` 读取来源链接、`<published>` 读取首次提交日期并提取年份。标题会合并换行和多余空格；日期缺失或无效时保留 `None`，不从标题猜年份。

模型的 JSON 输出与 arXiv 的 Atom/XML 是不同接口的数据格式，各用对应的解析方法。这里的年份表示 arXiv 首次提交年，不表示正式期刊发表年。接口排序也不等于已经逐篇阅读或证明论文质量。参考：[arXiv API 用户手册](https://info.arxiv.org/help/api/user-manual.html)。

无结果时返回 `[]`，显示“未找到匹配论文”；连接失败、HTTP 错误、无效 XML、arXiv 错误条目或关键元数据缺失会抛出 `RuntimeError`，入口显示失败提示。这两种情况不能混为一谈。

每次只发起一次请求，不自动重试或分页。连续调用时需要单连接且请求间隔至少 3 秒；当前演示与实际验证均按此要求执行。参考：[arXiv API 使用要求](https://info.arxiv.org/help/api/tou.html)。

## 7. 真实检索与模型参数串联

先直接调用工具：

```cmd
conda run -n researchflow python -m app.paper_tools
```

再运行完整流程：

```cmd
conda run -n researchflow python -m app.json_output --search
```

`argparse` 读取命令行开关；`--search` 让 `main(search=True)` 在参数校验成功后继续执行：

```python
papers = search_paper(params["query"], params["max_results"])
print_papers(papers)
```

2026-10-15 两个入口均真实运行成功，退出码均为 0。关键词为 `retrieval-augmented generation`，指定最多 2 篇，arXiv 实际返回：

| 标题 | 首次提交年 | 来源 |
|---|---|---|
| Automated Literature Review Using NLP Techniques and LLM-Based Retrieval-Augmented Generation | 2024 | [arXiv:2411.18583v1](http://arxiv.org/abs/2411.18583v1) |
| Riddle Me This! Stealthy Membership Inference for Retrieval-Augmented Generation | 2025 | [arXiv:2502.00306v2](http://arxiv.org/abs/2502.00306v2) |

完整流程中模型实际生成 `{"query": "retrieval-augmented generation", "max_results": 2}`，校验后传给工具，返回上述论文。这是当次真实检索的结果，后续接口结果可能变化，没有使用固定样例冒充实时结果。

2026-10-16 确认本地完整流程的运行截图：同样生成上述参数、通过校验并返回这两篇论文，终端已返回命令提示符。运行结果已有本地证据，概念理解仍需通过复述与练习检查。

新增的 10 项工具测试使用固定 Atom 样例，覆盖参数限制、默认数量与边界、正常元数据、无结果、网络/HTTP/查询错误、异常 XML 和年份缺失。新增的 3 项串联测试验证参数传递、错误参数不执行工具、工具失败会停止。完整 45 项测试通过；网络调用另外验证。

本阶段由 Python 按固定顺序调用函数。模型尚未通过 `tool_calls` 选择工具，工具结果也没有回传给模型继续推理；这些是 Day 4 的学习内容。

两个函数的分工需要分清：`generate_search_params()` 访问 DeepSeek，返回经过校验的参数字典；`search_paper()` 内部访问 arXiv 并解析返回数据，最终得到论文列表。取得论文的整个过程都在搜索工具中完成。

## 8. 下一步

学习总结：学习了 Prompt 基础与 JSON 结构化输出，实现了第一个论文搜索工具。结束时暂时没有不清楚的地方，实际用时未统计；继续通过复述与后续练习巩固数据格式和函数分工。

Day 4 复用现有搜索函数，学习工具描述、`tool_calls`、Python 校验执行和按调用 ID 回传结果，完成一次“模型请求工具 → 执行 → 结果回传 → 最终回答”的闭环。多步自主循环留到 Day 5。
