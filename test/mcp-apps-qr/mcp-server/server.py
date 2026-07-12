#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.26.0",
#     "qrcode[pil]>=8.0",
#     "uvicorn>=0.34.0",
#     "starlette>=0.46.0",
# ]
# ///
"""
QR Code MCP Server - Generates QR codes from text

Demo for CopilotKit MCP Apps (test/mcp-apps-qr). Default port 3108 matches CopilotKit docs.
"""
import os
import sys
import io
import base64

import qrcode
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp import types
from starlette.middleware.cors import CORSMiddleware

VIEW_URI = "ui://qr-server/view.html"
HOST = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 for Docker compatibility
PORT = int(os.environ.get("PORT", "3108"))

mcp = FastMCP("QR Code Server", stateless_http=True, host=HOST, port=PORT)

# Interactive MCP App view — proves client-side JS runs inside the iframe
EMBEDDED_VIEW_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta name="color-scheme" content="light dark">
  <style>
    :root {
      --bg: #fffdf8;
      --text: #1c1917;
      --muted: #6b645c;
      --accent: #0f766e;
      --border: #ddd6cb;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
      font: 13px/1.45 system-ui, sans-serif;
    }
    body {
      width: 360px;
      min-height: 480px;
      padding: 12px;
    }
    .card {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      background: #fff;
    }
    .badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      color: var(--accent);
      background: #ccfbf1;
      padding: 2px 8px;
      border-radius: 999px;
      margin-bottom: 8px;
    }
    #preview {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 220px;
      margin: 8px 0;
      background: #f5f2eb;
      border-radius: 8px;
    }
    #preview img {
      width: 200px;
      height: 200px;
      border-radius: 6px;
      transition: transform 0.2s ease, filter 0.2s ease;
    }
    #preview.zoomed img { transform: scale(1.25); }
    #preview.inverted img { filter: invert(1); }
    #meta {
      color: var(--muted);
      font-size: 12px;
      word-break: break-all;
      margin: 0 0 10px;
    }
    #meta strong { color: var(--text); }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    button {
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      border-radius: 8px;
      padding: 6px 10px;
      cursor: pointer;
      font: inherit;
    }
    button:hover { border-color: var(--accent); color: var(--accent); }
    button:disabled { opacity: 0.45; cursor: not-allowed; }
    #status {
      margin-top: 10px;
      font-size: 12px;
      color: var(--accent);
      min-height: 1.2em;
    }
    #clicks {
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">MCP App client UI (iframe)</div>
    <div id="preview"><span style="color:#6b645c">Waiting for QR...</span></div>
    <p id="meta">No result yet.</p>
    <div class="actions">
      <button id="btn-download" disabled>Download PNG</button>
      <button id="btn-copy" disabled>Copy text</button>
      <button id="btn-zoom" disabled>Zoom</button>
      <button id="btn-invert" disabled>Invert</button>
    </div>
    <div id="status"></div>
    <div id="clicks">Client clicks: 0 (proves JS is live)</div>
  </div>
  <script type="module">
    import { App } from "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps";

    const app = new App({ name: "QR View", version: "1.1.0" });
    let current = { mimeType: "image/png", data: "", text: "", serverAt: "" };
    let clicks = 0;

    const preview = document.getElementById("preview");
    const meta = document.getElementById("meta");
    const status = document.getElementById("status");
    const clicksEl = document.getElementById("clicks");
    const buttons = ["btn-download", "btn-copy", "btn-zoom", "btn-invert"].map(id => document.getElementById(id));

    function bump(msg) {
      clicks += 1;
      clicksEl.textContent = `Client clicks: ${clicks} (proves JS is live)`;
      status.textContent = msg;
    }

    function setEnabled(on) {
      for (const b of buttons) b.disabled = !on;
    }

    function renderImage() {
      preview.innerHTML = "";
      const image = document.createElement("img");
      image.src = `data:${current.mimeType};base64,${current.data}`;
      image.alt = "QR Code";
      preview.appendChild(image);
      meta.innerHTML = `<strong>Encoded:</strong> ${escapeHtml(current.text || "(unknown)")}<br/>`
        + `<strong>Server generated at:</strong> ${escapeHtml(current.serverAt || "(n/a)")}<br/>`
        + `<strong>Client rendered at:</strong> ${new Date().toLocaleTimeString()}`;
      setEnabled(true);
      bump("QR received from MCP server — client UI rendered it.");
      try {
        app.notifySizeChanged?.({ height: document.body.scrollHeight });
      } catch (_) {}
    }

    function escapeHtml(s) {
      return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    app.ontoolresult = ({ content }) => {
      const img = content?.find(c => c.type === "image");
      const textPart = content?.find(c => c.type === "text");
      let metaObj = {};
      if (textPart?.text) {
        try { metaObj = JSON.parse(textPart.text); } catch (_) { metaObj = { text: textPart.text }; }
      }
      if (!img) {
        status.textContent = "No image in tool result.";
        return;
      }
      const allowed = ["image/png", "image/jpeg", "image/gif"];
      current = {
        mimeType: allowed.includes(img.mimeType) ? img.mimeType : "image/png",
        data: img.data,
        text: metaObj.text || metaObj.url || "",
        serverAt: metaObj.generated_at || "",
      };
      preview.classList.remove("zoomed", "inverted");
      renderImage();
    };

    document.getElementById("btn-download").onclick = () => {
      if (!current.data) return;
      const a = document.createElement("a");
      a.href = `data:${current.mimeType};base64,${current.data}`;
      a.download = "qr-code.png";
      a.click();
      bump("Downloaded PNG from client UI.");
    };

    document.getElementById("btn-copy").onclick = async () => {
      if (!current.text) return;
      try {
        await navigator.clipboard.writeText(current.text);
        bump("Copied encoded text from client UI.");
      } catch (_) {
        bump("Clipboard blocked — text: " + current.text);
      }
    };

    document.getElementById("btn-zoom").onclick = () => {
      preview.classList.toggle("zoomed");
      bump(preview.classList.contains("zoomed") ? "Zoom on (client CSS)." : "Zoom off.");
    };

    document.getElementById("btn-invert").onclick = () => {
      preview.classList.toggle("inverted");
      bump(preview.classList.contains("inverted") ? "Invert on (client CSS)." : "Invert off.");
    };

    function handleHostContextChanged(ctx) {
      if (ctx?.safeAreaInsets) {
        document.body.style.paddingTop = `${ctx.safeAreaInsets.top + 12}px`;
        document.body.style.paddingRight = `${ctx.safeAreaInsets.right + 12}px`;
        document.body.style.paddingBottom = `${ctx.safeAreaInsets.bottom + 12}px`;
        document.body.style.paddingLeft = `${ctx.safeAreaInsets.left + 12}px`;
      }
    }

    app.onhostcontextchanged = handleHostContextChanged;
    await app.connect();
    const ctx = app.getHostContext();
    if (ctx) handleHostContextChanged(ctx);
  </script>
</body>
</html>"""


@mcp.tool(meta={
    "ui":{"resourceUri": VIEW_URI},
    "ui/resourceUri": VIEW_URI, # legacy support
})
def generate_qr(
    text: str = "https://modelcontextprotocol.io",
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> list:
    """Generate a QR code from text.

    Args:
        text: The text/URL to encode
        box_size: Size of each box in pixels (default: 10)
        border: Border size in boxes (default: 4)
        error_correction: Error correction level - L(7%), M(15%), Q(25%), H(30%)
        fill_color: Foreground color (hex like #FF0000 or name like red)
        back_color: Background color (hex like #FFFFFF or name like white)
    """
    from datetime import datetime, timezone

    error_levels = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=error_levels.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    generated_at = datetime.now(timezone.utc).isoformat()
    print(f"[generate_qr] text={text!r} generated_at={generated_at}")
    meta = {
        "text": text,
        "fill_color": fill_color,
        "back_color": back_color,
        "error_correction": error_correction,
        "generated_at": generated_at,
        "source": "mcp-apps-qr-server",
    }
    return [
        types.TextContent(type="text", text=__import__("json").dumps(meta)),
        types.ImageContent(type="image", data=b64, mimeType="image/png"),
    ]


@mcp.tool()
def echo_text(message: str, uppercase: bool = False) -> str:
    """Echo text back from the MCP server (no UI resource).

    Use this for plain backend-style MCP tools that should run on Agno,
    not CopilotKit MCP Apps.

    Args:
        message: Text to echo
        uppercase: If true, return the message uppercased
    """
    result = message.upper() if uppercase else message
    print(f"[echo_text] message={message!r} uppercase={uppercase} -> {result!r}")
    return result


# IMPORTANT: all the external domains used by app must be listed
# in the meta.ui.csp.resourceDomains - otherwise they will be blocked by CSP policy
@mcp.resource(
    VIEW_URI,
    mime_type="text/html;profile=mcp-app",
    meta={"ui": {"csp": {"resourceDomains": ["https://unpkg.com"]}}},
)
def view() -> str:
    """View HTML resource with CSP metadata for external dependencies."""
    return EMBEDDED_VIEW_HTML

if __name__ == "__main__":
    if "--stdio" in sys.argv:
        # Claude Desktop mode
        mcp.run(transport="stdio")
    else:
        # HTTP mode for basic-host (default) - with CORS
        app = mcp.streamable_http_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        print(f"QR Code Server listening on http://{HOST}:{PORT}/mcp")
        uvicorn.run(app, host=HOST, port=PORT)
