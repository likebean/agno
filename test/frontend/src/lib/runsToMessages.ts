/**
 * Convert AgentOS session runs into AG-UI messages for CopilotKit history hydration.
 *
 * Each run becomes: user message → (optional) assistant+toolCalls → tool results → assistant text.
 */

export interface AgentOsTool {
  tool_call_id?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  result?: unknown;
}

export interface AgentOsRun {
  run_id: string;
  run_input?: string | null;
  content?: string | Record<string, unknown> | null;
  tools?: AgentOsTool[] | null;
  created_at?: string | number | null;
}

export interface AguiMessage {
  id: string;
  role: "user" | "assistant" | "tool";
  content?: string;
  toolCalls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>;
  toolCallId?: string;
}

function newId(): string {
  return crypto.randomUUID();
}

function serializeResult(result: unknown): string {
  if (result === null || result === undefined) return "";
  if (typeof result === "string") return result;
  return JSON.stringify(result);
}

function serializeContent(content: AgentOsRun["content"]): string {
  if (content === null || content === undefined) return "";
  if (typeof content === "string") return content;
  return JSON.stringify(content);
}

export function runsToAguiMessages(runs: AgentOsRun[]): AguiMessage[] {
  const messages: AguiMessage[] = [];

  for (const run of runs) {
    const userText = run.run_input?.trim();
    if (userText) {
      messages.push({
        id: newId(),
        role: "user",
        content: userText,
      });
    }

    const tools = run.tools ?? [];
    if (tools.length > 0) {
      const toolCalls = tools
        .filter((t) => t.tool_call_id && t.tool_name)
        .map((t) => ({
          id: t.tool_call_id as string,
          type: "function" as const,
          function: {
            name: t.tool_name as string,
            arguments: JSON.stringify(t.tool_args ?? {}),
          },
        }));

      if (toolCalls.length > 0) {
        messages.push({
          id: newId(),
          role: "assistant",
          content: "",
          toolCalls,
        });
      }

      for (const t of tools) {
        if (!t.tool_call_id) continue;
        messages.push({
          id: newId(),
          role: "tool",
          content: serializeResult(t.result),
          toolCallId: t.tool_call_id,
        });
      }
    }

    const assistantText = serializeContent(run.content).trim();
    if (assistantText) {
      messages.push({
        id: newId(),
        role: "assistant",
        content: assistantText,
      });
    }
  }

  return messages;
}
