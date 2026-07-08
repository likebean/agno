"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import { CopilotLayouts } from "@/components/CopilotLayouts";
import {
  LayoutModeSwitcher,
  type LayoutMode,
} from "@/components/LayoutModeSwitcher";
import { ThreadSidebar } from "@/components/ThreadSidebar";
import { WeatherToolRenderer } from "@/components/WeatherToolRenderer";
import { COPILOT_AGENT_ID } from "@/lib/config";
import { useEffect, useState } from "react";

export function CopilotApp() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("chat");

  useEffect(() => {
    setThreadId(crypto.randomUUID());
  }, []);

  if (!threadId) {
    return (
      <div className="app-shell" style={{ alignItems: "center", justifyContent: "center" }}>
        <p className="muted">加载中...</p>
      </div>
    );
  }

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent={COPILOT_AGENT_ID}
      threadId={threadId}
    >
      <WeatherToolRenderer />
      <div className="app-shell">
        <LayoutModeSwitcher mode={layoutMode} onChange={setLayoutMode} />
        <div className="app-body">
          <ThreadSidebar threadId={threadId} setThreadId={setThreadId} />
          <div className="app-main">
            <CopilotLayouts threadId={threadId} mode={layoutMode} />
          </div>
        </div>
      </div>
    </CopilotKit>
  );
}
