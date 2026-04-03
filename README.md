# life-legacy (生命·传承)

> "死亡不是生命的终点，遗忘才是。" —— 《寻梦环游记》

## 🌟 项目简介

`life-legacy` 是一个开源的个人数字生命构建框架。它允许你导入自己的人生轨迹（照片、日记、聊天记录、人生大事），训练一个基于大模型的 **数字孪生体**。

- **生前**：它是你的**第二大脑**和**代理人**，帮你处理事务，延续你的工作流。
- **身后**：它是你的**数字墓碑**和**灵魂容器**，让亲人能跨越时空与你对话，聆听你的故事。

## 🏗️ 项目结构

```
life-legacy/
├── main.py                      # 核心引擎（DigitalTwin 类）
├── setup.py                     # 初始化向导
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
│
├── web/                         # Web UI
│   ├── app.py                   # FastAPI 后端
│   └── static/
│       └── index.html           # 聊天界面
│
├── skills/
│   ├── core/
│   │   ├── system_prompt.md     # 数字孪生体系统提示词模板
│   │   ├── memory_manager.py    # 记忆管理系统（多源记忆加载 + 检索）
│   │   └── mode_switch.py       # 模式切换（Living / Legacy）
│   │
│   ├── modules/
│   │   ├── storyteller.md       # 回忆讲述者技能规范
│   │   ├── executor.md          # 执行代理技能规范
│   │   └── advisor.md           # 人生建议者技能规范
│   │
│   └── data/
│       ├── timeline.json        # 人生大事记
│       ├── values.md            # 个人价值观与语言风格
│       ├── relationships.md     # 关系图谱
│       ├── diaries/             # 日记文件 (.md / .txt)
│       ├── chats/               # 聊天记录 (.json)
│       └── photos/              # 照片描述文件 (.txt)
│
└── utils/
    ├── photo_analyzer.py        # 照片分析（接入 GPT-4o Vision）
    └── voice_cloner.py          # 语音合成（接入 OpenAI TTS）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key
```

`.env` 文件内容：
```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
WEB_PORT=8000
```

### 3. 初始化

```bash
python setup.py
```

按提示输入你的名字、出生年份、家乡等信息。系统会自动创建数据目录结构。

### 4. 启动

**Web 界面（推荐）：**
```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```
然后访问 http://localhost:8000

**CLI 模式：**
```bash
python main.py
```

## 📂 数据导入

### 人生大事记 (timeline.json)

编辑 `skills/data/timeline.json`，添加你的人生里程碑：

```json
{
  "meta": {
    "name": "张三",
    "birth_year": 1990,
    "hometown": "杭州"
  },
  "milestones": [
    {
      "year": 2008,
      "event": "考入浙江大学计算机科学专业",
      "feeling": "非常激动，那是我第一次离开家乡。",
      "tags": ["教育", "成长"]
    }
  ]
}
```

### 日记

将日记文件放入 `skills/data/diaries/` 目录，支持 `.md` 和 `.txt` 格式。文件名建议为日期，如 `2023-01-15.md`。

### 聊天记录

将聊天记录保存为 JSON 文件放入 `skills/data/chats/` 目录，格式：

```json
{
  "messages": [
    {"role": "user", "content": "今天天气真好"},
    {"role": "assistant", "content": "是啊，适合出去走走"}
  ]
}
```

### 照片分析

使用内置的照片分析工具：

```python
from utils.photo_analyzer import save_photo_description

# 自动分析照片并保存描述
description = save_photo_description("path/to/photo.jpg")
print(description)
```

## ⚙️ 核心功能

### 记忆检索

`MemoryManager` 支持从以下来源检索记忆：
- `timeline.json` 人生大事记
- `diaries/` 日记文件
- `chats/` 聊天记录
- `photos/` 照片描述

使用语义关键词匹配，返回最相关的记忆片段。

### 模式切换

系统根据 `config.json` 中的 `last_active_timestamp` 和 `legacy_trigger_days`（默认365天）自动切换模式：

- **Living Mode**：主动、高效，可执行任务
- **Legacy Mode**：温和、智慧，专注于故事讲述和情感陪伴

### 技能模块

| 技能 | 触发场景 | 说明 |
|---|---|---|
| Storyteller | "讲讲你年轻时..." | 用感官细节讲述人生故事 |
| Executor | "帮我写封邮件..." | 模仿用户风格执行任务 |
| Advisor | "你觉得我该怎么做？" | 基于经历和价值观给出建议 |

## 🔒 安全

- `.env` 和 `config.json` 已在 `.gitignore` 中排除
- 不要在代码中硬编码 API Key
- 敏感信息（密码、财务数据）不会在对话中透露

## 📝 License

MIT License
