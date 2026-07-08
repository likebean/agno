# Tool Rendering 天气查询 Demo

CopilotKit 最佳实践 + Agno 后端 `get_weather`，支持历史 thread 中 tool 渲染。

## CopilotKit 模式对照

| 文档 | 本 demo 实现 |
|------|-------------|
| [Prebuilt Components](https://docs.copilotkit.ai/agno/prebuilt-components) | 顶部可切换 `CopilotChat` / `CopilotSidebar` / `CopilotPopup` |
| [Threads](https://docs.copilotkit.ai/agno/threads) | 受控 `threadId`；自托管用 AgentOS session 桥接（见下） |
| [Slots](https://docs.copilotkit.ai/agno/custom-look-and-feel/slots) | `messageView` / `input` / `children` render function |
| [Tool Rendering](https://docs.copilotkit.ai/agno/generative-ui/tool-rendering) | `useRenderTool({ name: "get_weather" })` |

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
    │   └── WeatherToolRenderer.tsx
    └── src/hooks/useAgentOsThreads.ts
```

## 启动

**前置：** 本机 MySQL 已有 `agent_platform` 库（默认 `root` / 见 `backend/.env.example`）

复制 `backend/.env.example` 为 `backend/.env`，配置 DashScope：

```env
AI_MODEL_NAME=qwen3-30b-a3b-instruct-2507
AI_MODEL_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL_API_KEY=sk-...
```

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS agent_platform;"
```

**后端：**
```bash
.venvs/demo/bin/python test/backend/main.py
```

数据库连接：`mysql+pymysql://root@localhost:3306/agent_platform`（可用 `MYSQL_*` 环境变量覆盖）

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
