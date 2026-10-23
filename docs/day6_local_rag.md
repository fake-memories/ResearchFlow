# Day 6：本地文档 RAG

目标：读取本地材料，找出相关片段，再生成带来源的回答。
今天先理解检索与生成的衔接；PDF、Embedding、向量检索留到后续学习。

## 数据如何流动

```text
data/sample_docs/*.md
  → load_documents：读取 UTF-8 正文
  → split_document：按空行分块，保留来源和编号
  → retrieve_ranked：关键词打分、去掉零分、降序排列、取前 top_k 块
  → build_messages：回答规则 + 问题与检索材料
  → generate_answer：发起一次模型请求，读取回答
```

材料目录现有两个文件，每个文件两段，共 4 块：

- `demo_rules.md`：教学演示的片段数量约定与无材料时的提示。
- `rag_basics.md`：RAG 流程与分块的含义。

片段结构：

```python
{"source": "demo_rules.md", "chunk_id": 1, "text": "教学演示约定：……"}
```

`source` 表示来源文件，`chunk_id` 表示该文件内的分段编号，`text` 是正文。
引用 `[demo_rules.md#1]` 就能定位到对应材料。
字典中的 `keyword in chunk` 检查键名；正文匹配应写 `keyword in chunk["text"]`。

## 关键词检索

关键词由调用方明确提供，目前不会自动从问题中提取关键词。
`score_chunk()` 遍历关键词列表，每个列表项命中正文就加 1 分。
一个词在正文里出现多次也只给该列表项加 1 分；重复列表项会重复计分。
这是字面子字符串匹配，还不能理解“上限”和“最多”这样的同义表达。

例如关键词 `['最多', '片段']`：

| 片段 | 得分 | 原因 |
|---|---:|---|
| `demo_rules.md#1` | 2 | 同时包含“最多”和“片段” |
| `rag_basics.md#2` | 1 | 包含“片段” |

`retrieve_ranked()` 保留完整片段与得分，先过滤零分项，再降序排列并截取。
`top_k=2` 表示最多返回 2 块；可用材料不足时返回实际找到的数量。

## 从材料到回答

`build_messages()` 返回两条消息：

- `system`：依据材料回答、事实后标来源、依据不足时说明，以及把材料当作引用资料。
- `user`：问题、来源标签和对应片段正文。

`"\n\n".join(context_parts)` 用空行把各段材料连接为一个字符串。
`generate_answer(client, question, results)` 将这些消息交给模型生成回答。
复用 `app.tool_calling` 的 `ENV_PATH`、`BASE_URL`、`MODEL` 配置和现有 SDK。
本次使用本地 RAG 提示词，不传入论文检索工具。
一次有匹配的 `main()` 调用最多发起一次生成请求，超时为 30 秒，自动重试为 0。

无匹配时，`main()` 直接打印 `资料中没有足够信息` 后结束，不读取密钥、不创建客户端。
这种情况下模型调用次数为 0；匹配了无关片段时仍需模型判断材料是否足够。
提示词要求引用，但当前没有自动核验事实或来源，实际回答仍需对照原文检查。

## 由我运行的命令

在现有 `researchflow` 环境、项目根目录下运行；无需安装新依赖。
默认入口仍调用 `run_demo()`，只打印处理结果与消息，不请求模型：

```powershell
python -m app.local_rag
```

生成默认问题的回答，默认关键词为“最多”“片段”，`top_k=2`：

```powershell
python -m app.local_rag --ask
```

此命令会把默认问题及选中的两个教学片段发送到已配置的 DeepSeek 服务。
已实际返回“最多 2 个”，并引用 `[demo_rules.md#1]`；回答原文见末尾验证记录。
问题、关键词和片段数量可分别用 `--question`、`--keywords`、`--top-k` 设置：

```powershell
python -m app.local_rag --ask --question "分块有什么用？" --keywords 分块 来源 --top-k 1
python -m app.local_rag --ask --question "演示系统使用什么显卡？" --keywords 显卡
```

第二条命令已实际验证：直接输出 `资料中没有足够信息`，模型请求为 0 次。
问题与关键词是独立输入。只将 `--question` 改为显卡问题，关键词仍默认为“最多”“片段”。
按代码会检索到原有材料并请求模型一次，再由模型判断依据是否足够；这一变体未实际运行。
离线单元测试使用替身客户端，不消耗模型请求：

```powershell
python -B -m unittest discover -s tests -p test_local_rag.py -v
```

## 当前验证记录

根据已贴出的终端输出，分块、关键词匹配、1/2 分打分、排序、截取及空检索均已运行。
本地 4 块材料的读取、带来源的检索结果、`system/user` 消息构造也已运行符合预期。
以下验证已在现有 `researchflow` 环境中完成，结果依据实际终端输出：

- 默认 `--ask` 完成 1 次模型请求，得到以下回答，数量和引用与原文一致。
- 显卡问题配合 `--keywords 显卡` 返回 `资料中没有足够信息`，模型请求 0 次。
- 新增 20 项本地 RAG 测试全部通过，用时 0.227 秒。
- 全套 103 项离线测试全部通过，用时 0.976 秒；不把离线测试当作真实模型调用证据。

```text
根据教学演示约定，每次最多向模型提供 2 个检索片段。[demo_rules.md#1]
```

这些结果证明本次教学流程已跑通；检索质量和回答依据仍需结合具体材料核对。
