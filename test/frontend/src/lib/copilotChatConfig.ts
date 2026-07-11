import type { CopilotChatProps } from "@copilotkit/react-core/v2";
import { COPILOT_AGENT_ID } from "@/lib/config";

/** Shared labels + slots for CopilotChat / CopilotSidebar / CopilotPopup */
export function getCopilotChatProps(threadId: string): CopilotChatProps {
  return {
    agentId: COPILOT_AGENT_ID,
    threadId,
    labels: {
      welcomeMessageText:
        "可以查天气（Tokyo），也可以生成二维码（例如：帮我生成 https://docs.agno.com 的二维码）",
      chatInputPlaceholder: "查天气或生成二维码...",
      chatDisclaimerText:
        "Agent 在 Agno；天气用 useRenderTool；二维码 UI 由 MCP Apps 自动渲染。",
      modalHeaderTitle: "Weather + MCP Apps",
    },
    input: {
      textArea: "min-h-[44px] resize-none rounded-xl border-slate-300",
      sendButton: "rounded-xl bg-sky-600 hover:bg-sky-700",
    },
    messageView: {
      className: "bg-slate-50/80 p-2",
      assistantMessage: {
        markdownRenderer: "prose prose-sm max-w-none",
        toolCallsView: "my-2",
      },
      userMessage: "bg-sky-100 rounded-xl",
    },
    welcomeScreen: {
      welcomeMessage: "text-slate-600 text-center",
    },
  };
}
