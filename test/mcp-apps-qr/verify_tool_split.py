#!/usr/bin/env python3
"""Smoke-check QR MCP server exposes UI + non-UI tools.

Requires: ``uv run test/mcp-apps-qr/mcp-server/server.py``

  .venvs/demo/bin/python test/mcp-apps-qr/verify_tool_split.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = os.getenv("MCP_QR_SERVER_URL", "http://127.0.0.1:3108/mcp")
UI_TOOL = "generate_qr"
BACKEND_TOOL = "echo_text"


def _has_ui_meta(tool) -> bool:
    meta = getattr(tool, "meta", None)
    if not isinstance(meta, dict):
        dump = getattr(tool, "model_dump", None)
        data = dump() if callable(dump) else {}
        meta = data.get("meta") or data.get("_meta") or {}
    if not isinstance(meta, dict):
        return False
    if meta.get("ui/resourceUri"):
        return True
    ui = meta.get("ui")
    return isinstance(ui, dict) and bool(ui.get("resourceUri"))


async def main() -> int:
    print(f"Connecting → {MCP_URL}")
    try:
        async with streamablehttp_client(MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                by_name = {t.name: t for t in listed.tools}
                assert UI_TOOL in by_name, f"missing {UI_TOOL}: {sorted(by_name)}"
                assert BACKEND_TOOL in by_name, f"missing {BACKEND_TOOL}: {sorted(by_name)}"
                assert _has_ui_meta(by_name[UI_TOOL]), f"{UI_TOOL} should have UI meta"
                assert not _has_ui_meta(by_name[BACKEND_TOOL]), f"{BACKEND_TOOL} must not have UI meta"
                print(f"OK tools={sorted(by_name)}")
                print(f"  {UI_TOOL}: UI meta present (for CopilotKit)")
                print(f"  {BACKEND_TOOL}: no UI meta (for Agno after Admin select)")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
