# QR Code MCP Apps Server

仅提供 MCP Server（`generate_qr` tool + UI resource）。

**Chat UI / Agent 不在这里。** 请接到原来的天气 Chat：

- Agent：`test/backend`（Agno）
- Chat + `mcpApps` 注册：`test/frontend/src/app/api/copilotkit/route.ts`

详见 [test/README.md](../README.md)。

## 启动

```bash
uv run server.py
# → QR Code Server listening on http://0.0.0.0:3108/mcp
```

基于 [modelcontextprotocol/ext-apps qr-server](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/qr-server)。

## 说明

`frontend/` 目录是早期独立 CopilotKit BuiltInAgent demo，已废弃，请勿再当作主入口。
