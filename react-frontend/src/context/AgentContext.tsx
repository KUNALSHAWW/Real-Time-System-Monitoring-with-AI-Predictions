"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "./AuthContext";
import api from "@/lib/api";

interface Agent {
  agent_id: string;
  is_active: boolean;
  last_seen_at: string | null;
}

interface AgentContextValue {
  agents: Agent[];
  selectedAgent: string | null;
  setSelectedAgent: (id: string) => void;
  refreshAgents: () => Promise<void>;
}

const AgentContext = createContext<AgentContextValue>({
  agents: [],
  selectedAgent: null,
  setSelectedAgent: () => {},
  refreshAgents: async () => {},
});

export function AgentProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const refreshAgents = async () => {
    if (!token) return;
    try {
      const { data } = await api.get<Agent[]>("/metrics/agents");
      setAgents(data);
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0].agent_id);
      }
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    refreshAgents();
    // Poll agent list every 30s so new agents appear automatically
    const id = setInterval(refreshAgents, 30_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <AgentContext.Provider
      value={{ agents, selectedAgent, setSelectedAgent, refreshAgents }}
    >
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  return useContext(AgentContext);
}
