# ResearchFlow

ResearchFlow 是一个长期 AI Agent 学习与开发项目，用于准备 AI Agent 开发实习。

Day 1 从项目初始化开始，当前示例演示一次简单的 LLM 问答。

## 项目结构

```text
ResearchFlow/
├── app/
│   └── main.py
├── tests/
│   ├── .gitkeep
│   └── test_main.py
├── docs/
│   └── .gitkeep
├── Agent_Study_Progress.md
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

- `app/main.py`：单文件 LLM 问答入口。
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

## 初始依赖

`requirements.txt` 包含以下依赖，暂不固定版本：

- `openai`：使用 OpenAI Python SDK 调用 DeepSeek 兼容接口。
- `python-dotenv`：读取项目 `.env` 配置。
- `requests`：用于后续发送 HTTP 请求。

## 离线测试

在项目目录中激活 `researchflow` 环境后执行：

```cmd
python -m unittest discover -s tests -v
```

测试使用模拟响应，不请求 DeepSeek，也不需要真实密钥。

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
