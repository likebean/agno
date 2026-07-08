import type { CopilotChatProps } from "@copilotkit/react-core/v2";
import { COPILOT_AGENT_ID } from "@/lib/config";

/** Shared labels + slots for CopilotChat / CopilotSidebar / CopilotPopup */
export function getCopilotChatProps(threadId: string): CopilotChatProps {
  return {
    agentId: COPILOT_AGENT_ID,
    threadId,
    labels: {
      welcomeMessageText:
        "问我任何城市的天气，例如：San Francisco、Tokyo、London",
      chatInputPlaceholder: "输入城市名查询天气...",
      chatDisclaimerText: "由 Agno Agent 提供，tool 结果以卡片形式渲染。",
      modalHeaderTitle: "Weather Agent",
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
