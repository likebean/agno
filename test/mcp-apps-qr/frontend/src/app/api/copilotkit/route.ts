import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { NextRequest } from "next/server";

const MCP_QR_SERVER_URL =
  process.env.MCP_QR_SERVER_URL ?? "http://localhost:3108/mcp";

const MODEL =
  process.env.COPILOT_MODEL ?? "openai/gpt-4.1-mini";

const agent = new BuiltInAgent({
  model: MODEL,
  prompt: `You are a helpful assistant that can generate QR codes.

When the user asks for a QR code (URL, text, WiFi, etc.), call the generate_qr tool.
Prefer generate_qr over describing the QR in text.
You may set fill_color / back_color when the user asks for styling.`,
});

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  agents: {
    default: agent,
  },
  mcpApps: {
    servers: [
      {
        type: "http",
        url: MCP_QR_SERVER_URL,
        serverId: "qr-server",
      },
    ],
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
