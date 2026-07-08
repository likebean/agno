"use client";

import { useAgentOsThreads } from "@/hooks/useAgentOsThreads";

interface ThreadSidebarProps {
  threadId: string;
  setThreadId: (id: string) => void;
}

/**
 * Thread list — AgentOS-backed equivalent of CopilotKit `useThreads` sidebar.
 */
export function ThreadSidebar({ threadId, setThreadId }: ThreadSidebarProps) {
  const {
    threads,
    isLoading,
    error,
    refreshThreads,
    selectThread,
    createThread,
  } = useAgentOsThreads(threadId, setThreadId);

  return (
    <aside className="thread-sidebar">
      <div className="thread-sidebar-header">
        <h2 className="thread-sidebar-title">Threads</h2>
        <button type="button" onClick={createThread} className="thread-btn thread-btn-primary">
          + 新对话
        </button>
        <button type="button" onClick={refreshThreads} className="thread-btn thread-btn-ghost">
          刷新列表
        </button>
      </div>

      <div className="thread-list">
        {isLoading && <p className="muted">加载中...</p>}
        {error && <p className="error">{error}</p>}
        {!isLoading && threads.length === 0 && (
          <p className="muted">暂无对话。发送消息后点「刷新列表」。</p>
        )}
        {threads.map((thread) => (
          <button
            key={thread.session_id}
            type="button"
            onClick={() => selectThread(thread.session_id)}
            className={`thread-item${threadId === thread.session_id ? " active" : ""}`}
          >
            <div className="thread-item-name">{thread.session_name || "新对话"}</div>
            <div className="thread-item-id">{thread.session_id.slice(0, 8)}...</div>
          </button>
        ))}
      </div>
    </aside>
  );
}
