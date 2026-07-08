interface MainPreviewProps {
  threadId: string;
  layoutMode: string;
}

/** Main app area shown beside / behind CopilotSidebar & CopilotPopup */
export function MainPreview({ threadId, layoutMode }: MainPreviewProps) {
  return (
    <div className="main-preview">
      <div style={{ maxWidth: "28rem", textAlign: "center" }}>
        <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600 }}>Tool Rendering Demo</h2>
        <p className="muted" style={{ marginTop: "0.5rem" }}>
          当前布局：<strong>{layoutMode}</strong>
        </p>
        <p className="muted" style={{ marginTop: "1rem" }}>
          在 {layoutMode === "chat" ? "右侧聊天区" : "Copilot 面板"} 询问天气，
          例如「London 天气怎么样？」。左侧 Threads 可切换历史对话查看 tool 渲染。
        </p>
        <p style={{ marginTop: "0.75rem", fontFamily: "monospace", fontSize: "0.75rem", color: "#94a3b8" }}>
          thread: {threadId.slice(0, 8)}...
        </p>
      </div>
    </div>
  );
}
