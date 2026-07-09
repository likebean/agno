# Tool Rendering 天气查询 Demo

CopilotKit 最佳实践 + Agno 后端 `get_weather`，支持历史 thread 中 tool 渲染。

## CopilotKit 模式对照

| 文档 | 本 demo 实现 |
|------|-------------|
| [Prebuilt Components](https://docs.copilotkit.ai/agno/prebuilt-components) | 顶部可切换 `CopilotChat` / `CopilotSidebar` / `CopilotPopup` |
| [Threads](https://docs.copilotkit.ai/agno/threads) | 受控 `threadId`；自托管用 AgentOS session 桥接（见下） |
| [Slots](https://docs.copilotkit.ai/agno/custom-look-and-feel/slots) | `messageView` / `input` / `children` render function |
| [Tool Rendering](https://docs.copilotkit.ai/agno/generative-ui/tool-rendering) | `useRenderTool({ name: "get_weather" })` |
| Mock 标记位 | `useAgentContext({ description: "mock", value })` → AG-UI `context` → Agno `dependencies` → tool `run_context` |

### Threads 说明

官方 `useThreads` 依赖 **Enterprise Intelligence Platform**（云端 thread 存储）。

本 demo 为自托管 Agno，采用文档推荐的 **`threadId` 受控模式** + AgentOS session 桥接：

- `threadId` → AG-UI `thread_id` → Agno `session_id`
- 左侧 Thread 列表来自 AgentOS `/sessions` API
- 切换 thread 时用 `agent.setMessages()` 注入历史（runs → AG-UI messages）

若接入 EIP，可将 `ThreadSidebar` 替换为 `useThreads({ agentId: "weather_agent" })`。

## 结构

```
test/
├── backend/main.py
└── frontend/
    ├── src/components/
    │   ├── CopilotApp.tsx       # Provider + 布局切换
    │   ├── CopilotLayouts.tsx   # Chat / Sidebar / Popup 三模式
    │   ├── LayoutModeSwitcher.tsx
    │   ├── ThreadSidebar.tsx    # Thread 列表
    │   ├── MockContextToggle.tsx  # Mock 开关 → AG-UI context
    │   └── WeatherToolRenderer.tsx
    └── src/hooks/useAgentOsThreads.ts
```

## 启动

复制 `backend/.env.example` 为 `backend/.env`，配置 DashScope：

```env
AI_MODEL_NAME=qwen3-30b-a3b-instruct-2507
AI_MODEL_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL_API_KEY=sk-...
```

数据库：
- Agent/Session：`test/backend/tmp/agent_platform.db`（SQLite）
- Knowledge 元数据：`test/backend/tmp/knowledge_contents.db`（SQLite，`contents_db`）
- 向量检索：PgVector on `postgresql+psycopg://ai@localhost:5532/ai`

**PgVector 前置（本机 PostgreSQL 17 + pgvector，端口 5532）：**
```bash
# 若 5532 未启动，可用项目内数据目录启动：
PG17=/opt/homebrew/opt/postgresql@17/bin
PGDATA=test/backend/tmp/pgvector-data
mkdir -p "$PGDATA"
[ -f "$PGDATA/PG_VERSION" ] || "$PG17/initdb" -D "$PGDATA" -U ai -A trust --encoding=UTF8 --locale=C
"$PG17/pg_ctl" -D "$PGDATA" -o "-p 5532" -l test/backend/tmp/pgvector.log start
"$PG17/psql" -h localhost -p 5532 -U ai -d postgres -c "CREATE DATABASE ai;" || true
"$PG17/psql" -h localhost -p 5532 -U ai -d ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**后端：**
```bash
.venvs/demo/bin/python test/backend/main.py
```

数据库：SQLite（sessions/components）+ PgVector（向量）；支持 [os.agno.com Knowledge](https://docs.agno.com/agent-os/features/knowledge-management) 页面上传文件

**前端：**
```bash
cd test/frontend
npm install
npm run dev
```

打开 http://localhost:3000

## 使用

1. 顶部切换 **CopilotChat / CopilotSidebar / CopilotPopup** 布局
2. 问「Tokyo 天气怎么样？」→ `get_weather` 渲染天气卡片
3. 点「刷新列表」→ 看到 AgentOS session
4. 点击 thread → 加载历史，`useRenderTool` 渲染历史 tool 调用
5. 「+ 新对话」→ 新 `threadId`（新 session）
