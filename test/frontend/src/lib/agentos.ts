import { AGENT_ID } from "@/lib/config";

const BASE = "/api/agentos";

export interface SessionEntry {
  session_id: string;
  session_name: string;
  created_at: number;
  updated_at?: number;
}

export interface AgentDetails {
  id: string;
  name?: string;
  db_id?: string;
}

export async function fetchAgents(): Promise<AgentDetails[]> {
  const res = await fetch(`${BASE}/agents`);
  if (!res.ok) throw new Error(`Failed to fetch agents: ${res.statusText}`);
  return res.json();
}

export async function fetchSessions(
  dbId: string,
): Promise<SessionEntry[]> {
  const url = new URL(`${BASE}/sessions`, window.location.origin);
  url.searchParams.set("type", "agent");
  url.searchParams.set("component_id", AGENT_ID);
  url.searchParams.set("db_id", dbId);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.statusText}`);
  const data = await res.json();
  return data.data ?? [];
}

export async function fetchSessionRuns(
  sessionId: string,
  dbId: string,
): Promise<import("@/lib/runsToMessages").AgentOsRun[]> {
  const url = new URL(`${BASE}/sessions/${sessionId}/runs`, window.location.origin);
  url.searchParams.set("type", "agent");
  url.searchParams.set("db_id", dbId);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
  return res.json();
}
