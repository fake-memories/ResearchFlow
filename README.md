# ResearchFlow

ResearchFlow 是一个长期 AI Agent 学习与开发项目，用于准备 AI Agent 开发实习。

Day 1 仅完成项目初始化，建立基础目录、简单 Python 入口和学习档案。

## 项目结构

```text
ResearchFlow/
├── app/
│   └── main.py
├── tests/
│   └── .gitkeep
├── docs/
│   └── .gitkeep
├── Agent_Study_Progress.md
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

- `app/main.py`：项目的简单启动入口。
- `tests/`：存放后续测试，使用 `.gitkeep` 在 Git 中保留目录。
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

5. 运行项目入口：

   ```cmd
   python app\main.py
   ```

以后进入项目目录并激活现有的 `researchflow` 环境即可运行，无需重复创建环境。

在项目目录中，也可以不激活环境，直接运行：

```cmd
conda run -n researchflow python app\main.py
```

当前入口仅输出 `ResearchFlow is ready.`，不调用 API，也不需要 API Key。

## 初始依赖

`requirements.txt` 包含以下依赖，暂不固定版本：

- `openai`：用于后续接入 OpenAI API。
- `python-dotenv`：用于后续读取环境变量配置。
- `requests`：用于后续发送 HTTP 请求。

## 后续 API 配置

`.env.example` 中的 `OPENAI_API_KEY` 是占位示例。后续接入 API 时，可在项目目录中执行：

```cmd
if not exist .env copy .env.example .env
```

然后在 `.env` 中填写自己的密钥。当前入口尚未读取 `.env`；`.env` 已列入忽略规则，请勿提交真实密钥。

## Day 1 状态

- 基础目录和文件已创建。
- Git 仓库已初始化，首次提交用于保存项目骨架。
- 已创建 Conda 环境 `researchflow`，使用 Python 3.11，项目依赖已安装。
- 学习记录请在 `Agent_Study_Progress.md` 中按实际情况填写。
