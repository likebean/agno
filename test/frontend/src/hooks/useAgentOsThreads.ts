"use client";

import { useCallback, useEffect, useState } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import {
  fetchAgents,
  fetchSessionRuns,
  fetchSessions,
  type SessionEntry,
} from "@/lib/agentos";
import { COPILOT_AGENT_ID } from "@/lib/config";
import { runsToAguiMessages } from "@/lib/runsToMessages";

/**
 * Bridges AgentOS sessions → CopilotKit threads (self-hosted Agno).
 *
 * Official `useThreads` needs Enterprise Intelligence Platform:
 * https://docs.copilotkit.ai/agno/threads
 *
 * AG-UI maps CopilotKit `threadId` to Agno `session_id`.
 */
export function useAgentOsThreads(
  threadId: string,
  setThreadId: (id: string) => void,
) {
  const { agent } = useAgent({ agentId: COPILOT_AGENT_ID });
  const [dbId, setDbId] = useState<string | null>(null);
  const [threads, setThreads] = useState<SessionEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents()
      .then((agents) => {
        const weather = agents.find((a) => a.id === "weather-agent");
        if (weather?.db_id) setDbId(weather.db_id);
        else setError("未找到 weather-agent 或 db_id");
      })
      .catch((e) => setError(String(e)));
  }, []);

  const refreshThreads = useCallback(async () => {
    if (!dbId) return;
    setIsLoading(true);
    setError(null);
    try {
      const list = await fetchSessions(dbId);
      setThreads(list);
    } catch (e) {
      setError(String(e));
    } finally {
      setIsLoading(false);
    }
  }, [dbId]);

  useEffect(() => {
    refreshThreads();
  }, [refreshThreads]);

  const selectThread = useCallback(
    async (sessionId: string) => {
      if (!dbId) return;
      setIsLoading(true);
      setError(null);
      try {
        setThreadId(sessionId);
        const runs = await fetchSessionRuns(sessionId, dbId);
        agent.setMessages(runsToAguiMessages(runs) as never);
      } catch (e) {
        setError(String(e));
      } finally {
        setIsLoading(false);
      }
    },
    [agent, dbId, setThreadId],
  );

  const createThread = useCallback(() => {
    const id = crypto.randomUUID();
    setThreadId(id);
    agent.setMessages([]);
  }, [agent, setThreadId]);

  return {
    threadId,
    threads,
    isLoading,
    error,
    refreshThreads,
    selectThread,
    createThread,
  };
}
