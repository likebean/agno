# QR Code MCP Apps Server

MCP Server tools：

| Tool | UI (`ui/resourceUri`) | 用途 |
|------|----------------------|------|
| `generate_qr` | 有 | CopilotKit MCP Apps / iframe（二维码） |
| `open_booking_form` | 有 | 表单 + 确认（对标 [CK showcase](https://github.com/CopilotKit/CopilotKit/tree/main/examples/showcases/mcp-apps)） |
| `confirm_booking` | 无 | 由表单 iframe 经 Host `tools/call` 提交 |
| `echo_text` | 无 | Agno 侧普通 MCP tool |

**表单确认流：** Agent 调 `open_booking_form` → Host 渲染 booking iframe → 用户填写并点 Confirm → View 调 `confirm_booking` → 展示确认号；可选「Send to chat」走 `app.sendMessage`。

在 **agent-platform Admin** 注册该 MCP，并把相关 tool 勾到同一个 Agent 上验证分流（不必改 `test/backend/main.py`）。

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
