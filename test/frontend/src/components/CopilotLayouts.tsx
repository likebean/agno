"use client";

import {
  CopilotChat,
  CopilotPopup,
  CopilotSidebar,
} from "@copilotkit/react-core/v2";
import { getCopilotChatProps } from "@/lib/copilotChatConfig";
import { MainPreview } from "@/components/MainPreview";
import type { LayoutMode } from "@/components/LayoutModeSwitcher";

interface CopilotLayoutsProps {
  threadId: string;
  mode: LayoutMode;
}

/**
 * @see https://docs.copilotkit.ai/agno/prebuilt-components
 *
 * CopilotSidebar / CopilotPopup render as fixed overlays alongside main content
 * (v2 does not wrap children — body margin is adjusted for sidebar).
 */
export function CopilotLayouts({ threadId, mode }: CopilotLayoutsProps) {
  const chatProps = getCopilotChatProps(threadId);

  if (mode === "sidebar") {
    return (
      <>
        <MainPreview threadId={threadId} layoutMode="CopilotSidebar" />
        <CopilotSidebar
          {...chatProps}
          defaultOpen
          width={420}
          position="right"
        />
      </>
    );
  }

  if (mode === "popup") {
    return (
      <>
        <MainPreview threadId={threadId} layoutMode="CopilotPopup" />
        <CopilotPopup
          {...chatProps}
          defaultOpen
          clickOutsideToClose={false}
        />
      </>
    );
  }

  return (
    <div className="chat-panel">
      <header className="chat-header">
        <h1>Tool Rendering — 天气查询</h1>
        <p>CopilotChat 内嵌模式 · thread {threadId.slice(0, 8)}...</p>
      </header>
      <div className="chat-content">
        <CopilotChat {...chatProps} className="h-full">
          {({ scrollView, input }) => (
            <div style={{ display: "flex", height: "100%", flexDirection: "column" }}>
              <div style={{ minHeight: 0, flex: 1 }}>{scrollView}</div>
              <div style={{ borderTop: "1px solid #e2e8f0", background: "#fff", padding: "1rem" }}>
                {input}
              </div>
            </div>
          )}
        </CopilotChat>
      </div>
    </div>
  );
}
