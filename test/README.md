# CopilotKit + Agno Demo

## 架构

```
Chat UI (test/frontend, CopilotKit)
  → CopilotRuntime
       ├─ mcpApps Middleware：发现 MCP tool，注入 AG-UI run_input.tools
       └─ AgnoAgent → test/backend AgentOS（≥2.7.2）
             ├─ get_weather（Agno 本地执行）
             └─ generate_qr 来自 client_tools（无需后端 stub）
                → Agno 暂停 external_execution
                → Middleware 调 MCP Server + iframe 渲染 UI
```

| 组件 | 路径 | 职责 |
|------|------|------|
| Chat UI | `frontend/` | CopilotKit 聊天界面 |
| Agent 后端 | `backend/` | Agno 统一管理 agent；天气本地执行 |
| QR MCP Server | `mcp-apps-qr/mcp-server/` | 真正生成二维码 + 提供 UI resource |
| Runtime mcpApps | `frontend/.../copilotkit/route.ts` | 注入/执行 MCP tool 并渲染 UI |

Agno ≥2.7.2 的 AG-UI 会 `parse_client_tools(run_input.tools)`（见 [#7801](https://github.com/agno-agi/agno/issues/7801) / [#8565](https://github.com/agno-agi/agno/pull/8565)），因此 **不必** 在 `main.py` 再注册 `generate_qr` stub。


## CopilotKit 能力对照

| 文档 | 本 demo 实现 |
|------|-------------|
| [Prebuilt Components](https://docs.copilotkit.ai/agno/prebuilt-components) | 顶部可切换 `CopilotChat` / `CopilotSidebar` / `CopilotPopup` |
| [Threads](https://docs.copilotkit.ai/agno/threads) | 受控 `threadId` + AgentOS session 桥接 |
| [Tool Rendering](https://docs.copilotkit.ai/agno/generative-ui/tool-rendering) | `useRenderTool({ name: "get_weather" })` |
| [MCP Apps](https://docs.copilotkit.ai/agno/generative-ui/mcp-apps) | Runtime `mcpApps` → `http://localhost:3108/mcp` |
| Mock 标记位 | `useAgentContext` → AG-UI context → Agno dependencies |

### Threads 说明

官方 `useThreads` 依赖 Enterprise Intelligence Platform。本 demo 用受控 `threadId` + AgentOS `/sessions`。

## 启动

### 1. QR MCP Server

```bash
cd test/mcp-apps-qr/mcp-server
uv run server.py
# → http://localhost:3108/mcp
```

### 2. Agno 后端

复制 `backend/.env.example` 为 `backend/.env`，配置模型 Key。

```bash
.venvs/demo/bin/python test/backend/main.py
# → http://localhost:8000/agui
```

### 3. Chat UI

```bash
cd test/frontend
cp .env.local.example .env.local   # 如尚未创建
npm install
npm run dev
```

打开 http://localhost:3000

## 试用

1. 「Tokyo 天气怎么样？」→ 天气卡片（Tool Rendering）
2. 「帮我生成 https://docs.agno.com 的二维码」→ 聊天内 MCP Apps 二维码 UI
3. Thread 列表 / 新对话与原先一致

## 环境变量（frontend `.env.local`）

| 变量 | 说明 | 默认 |
|------|------|------|
| `AGENTOS_URL` | Agno AgentOS | `http://127.0.0.1:8000` |
| `MCP_QR_SERVER_URL` | QR MCP Apps | `http://127.0.0.1:3108/mcp` |

## 结构

```
test/
├── backend/main.py              # Agno agents
├── frontend/                    # 唯一 Chat UI
│   └── src/app/api/copilotkit/route.ts   # AgnoAgent + mcpApps
└── mcp-apps-qr/mcp-server/      # 仅 MCP Server（不要另起一套 chat）
```

`mcp-apps-qr/frontend` 是早期独立 BuiltInAgent 试验，**已废弃**；请用本目录 `frontend/`。
