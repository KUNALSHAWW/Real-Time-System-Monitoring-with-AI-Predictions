"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useAgent } from "@/context/AgentContext";
import { useWebSocket, type WsAlert } from "@/hooks/useWebSocket";
import api from "@/lib/api";

import Sidebar from "@/components/Sidebar";
import MetricChart from "@/components/MetricChart";
import StatCard from "@/components/StatCard";
import AlertModal from "@/components/AlertModal";

// ---- Types -------------------------------------------------------------

interface DataPoint {
  timestamp: string;
  value: number;
}

interface CurrentSnapshot {
  agent_id: string;
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  disk_write_bytes_delta: number;
  disk_read_bytes_delta: number;
  network_sent_bytes_delta: number;
  network_recv_bytes_delta: number;
}

// ---- Helpers -----------------------------------------------------------

function severityColor(val: number): "green" | "yellow" | "red" {
  if (val >= 95) return "red";
  if (val >= 80) return "yellow";
  return "green";
}

// ---- Page component ----------------------------------------------------

export default function DashboardPage() {
  const { user, loading, token } = useAuth();
  const { agents, selectedAgent, setSelectedAgent } = useAgent();
  const router = useRouter();

  const [cpuData, setCpuData] = useState<DataPoint[]>([]);
  const [memData, setMemData] = useState<DataPoint[]>([]);
  const [diskData, setDiskData] = useState<DataPoint[]>([]);
  const [netData, setNetData] = useState<DataPoint[]>([]);
  const [snapshot, setSnapshot] = useState<CurrentSnapshot | null>(null);
  const [activeAlert, setActiveAlert] = useState<WsAlert | null>(null);

  const onAlert = useCallback((alert: WsAlert) => {
    const hasCritical = alert.data.some((a) => a.severity === "critical");
    if (hasCritical) setActiveAlert(alert);
  }, []);

  const { connected } = useWebSocket({ agentId: selectedAgent, onAlert });

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  const fetchData = useCallback(async () => {
    if (!token || !selectedAgent) return;
    const fetchSeries = async (metric: string) => {
      try {
        const { data } = await api.get(`/metrics/${metric}`, {
          params: { agent_id: selectedAgent, hours: 1 },
        });
        return (data.data_points as DataPoint[]) || [];
      } catch {
        return [];
      }
    };
    const [c, m, d, n] = await Promise.all([
      fetchSeries("cpu"),
      fetchSeries("memory"),
      fetchSeries("disk"),
      fetchSeries("network"),
    ]);
    setCpuData(c);
    setMemData(m);
    setDiskData(d);
    setNetData(n);
    try {
      const { data } = await api.get<CurrentSnapshot[]>("/metrics/current", {
        params: { agent_id: selectedAgent },
      });
      if (data.length > 0) setSnapshot(data[0]);
    } catch { /* no data yet */ }
  }, [token, selectedAgent]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    if (!token || !selectedAgent) return;
    const id = setInterval(fetchData, 10_000);
    return () => clearInterval(id);
  }, [token, selectedAgent, fetchData]);

  if (loading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin h-10 w-10 rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar agents={agents} selectedAgent={selectedAgent} onSelectAgent={setSelectedAgent} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-slate-500">
              Agent: <span className="font-mono text-slate-300">{selectedAgent ?? "none"}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-400" : "bg-slate-600"}`} />
            <span className="text-xs text-slate-500">{connected ? "Live" : "Disconnected"}</span>
          </div>
        </div>

        {snapshot && (
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="CPU" value={`${snapshot.cpu_percent}%`} color={severityColor(snapshot.cpu_percent)} />
            <StatCard label="Memory" value={`${snapshot.memory_percent}%`} color={severityColor(snapshot.memory_percent)} />
            <StatCard label="Disk" value={`${snapshot.disk_percent}%`} color={severityColor(snapshot.disk_percent)} />
            <StatCard
              label="Disk Write Δ"
              value={`${(snapshot.disk_write_bytes_delta / 1_000_000).toFixed(1)} MB`}
              sub="since last reading"
              color={snapshot.disk_write_bytes_delta > 500_000_000 ? "red" : snapshot.disk_write_bytes_delta > 200_000_000 ? "yellow" : "green"}
            />
          </div>
        )}

        {!selectedAgent && (
          <div className="flex flex-col items-center justify-center h-64 text-slate-500">
            <p className="text-lg">No agent selected</p>
            <p className="text-sm mt-1">Select an agent from the sidebar or start the agent sensor</p>
          </div>
        )}

        {selectedAgent && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <MetricChart title="CPU Usage" data={cpuData} color="#6366f1" />
            <MetricChart title="Memory Usage" data={memData} color="#22d3ee" />
            <MetricChart title="Disk Usage" data={diskData} color="#f59e0b" />
            <MetricChart title="Network Sent" data={netData} color="#10b981" unit=" B" />
          </div>
        )}
      </main>

      {activeAlert && <AlertModal alert={activeAlert} onDismiss={() => setActiveAlert(null)} />}
    </div>
  );
}
