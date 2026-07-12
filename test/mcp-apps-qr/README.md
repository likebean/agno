# QR Code MCP Apps Server

MCP Server tools：

| Tool | UI (`ui/resourceUri`) | 用途 |
|------|----------------------|------|
| `generate_qr` | 有 | CopilotKit MCP Apps / iframe |
| `echo_text` | 无 | Agno 侧普通 MCP tool |

在 **agent-platform Admin** 注册该 MCP，并把两个 tool 勾到同一个 Agent 上验证分流（不必改 `test/backend/main.py`）。

## 启动

```bash
uv run server.py
# → QR Code Server listening on http://0.0.0.0:3108/mcp
```

自检：

```bash
.venvs/demo/bin/python test/mcp-apps-qr/verify_tool_split.py
```

详见 [test/README.md](../README.md)。

基于 [modelcontextprotocol/ext-apps qr-server](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/qr-server)。
