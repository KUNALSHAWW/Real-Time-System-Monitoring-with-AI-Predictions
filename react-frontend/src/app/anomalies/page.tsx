"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useAgent } from "@/context/AgentContext";
import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { AlertTriangle, CheckCircle, ShieldAlert, Clock } from "lucide-react";

interface AnomalyEvent {
  id: number;
  agent_id: string;
  metric_name: string;
  value: number;
  z_score: number | null;
  severity: string;
  message: string | null;
  acknowledged: boolean;
  timestamp: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-red-500 bg-red-950/50 text-red-200",
  high: "border-orange-500 bg-orange-950/50 text-orange-200",
  medium: "border-yellow-500 bg-yellow-950/50 text-yellow-200",
  low: "border-blue-500 bg-blue-950/50 text-blue-200",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-600 text-white",
  medium: "bg-yellow-600 text-black",
  low: "bg-blue-600 text-white",
};

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString();
}

export default function AnomaliesPage() {
  const { user, loading, token } = useAuth();
  const { agents, selectedAgent, setSelectedAgent } = useAgent();
  const router = useRouter();

  const [anomalies, setAnomalies] = useState<AnomalyEvent[]>([]);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (!token || !selectedAgent) return;
    setFetching(true);
    api
      .get<{ anomalies: AnomalyEvent[] }>("/anomalies/list", {
        params: { agent_id: selectedAgent, limit: 100 },
      })
      .then(({ data }) => setAnomalies(data.anomalies ?? []))
      .catch(() => setAnomalies([]))
      .finally(() => setFetching(false));
  }, [token, selectedAgent]);

  // Auto-refresh every 15s
  useEffect(() => {
    if (!token || !selectedAgent) return;
    const id = setInterval(() => {
      api
        .get<{ anomalies: AnomalyEvent[] }>("/anomalies/list", {
          params: { agent_id: selectedAgent, limit: 100 },
        })
        .then(({ data }) => setAnomalies(data.anomalies ?? []))
        .catch(() => {});
    }, 15_000);
    return () => clearInterval(id);
  }, [token, selectedAgent]);

  if (loading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin h-10 w-10 rounded-full border-4 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  const criticalCount = anomalies.filter((a) => a.severity === "critical").length;
  const highCount = anomalies.filter((a) => a.severity === "high").length;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar agents={agents} selectedAgent={selectedAgent} onSelectAgent={setSelectedAgent} />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-red-400" />
            Anomaly Detection
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real threats and anomalies detected for{" "}
            <span className="font-mono text-slate-300">{selectedAgent ?? "no agent"}</span>
          </p>
        </div>

        {/* Summary cards */}
        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Total Events</p>
            <p className="text-2xl font-bold text-white mt-1">{anomalies.length}</p>
          </div>
          <div className="rounded-xl border border-red-800 bg-red-950/30 p-4">
            <p className="text-xs text-red-400 uppercase tracking-wider">Critical</p>
            <p className="text-2xl font-bold text-red-300 mt-1">{criticalCount}</p>
          </div>
          <div className="rounded-xl border border-orange-800 bg-orange-950/30 p-4">
            <p className="text-xs text-orange-400 uppercase tracking-wider">High</p>
            <p className="text-2xl font-bold text-orange-300 mt-1">{highCount}</p>
          </div>
          <div className="rounded-xl border border-emerald-800 bg-emerald-950/30 p-4">
            <p className="text-xs text-emerald-400 uppercase tracking-wider">Status</p>
            <p className="text-sm font-bold text-emerald-300 mt-1 flex items-center gap-1">
              {criticalCount === 0 ? (
                <><CheckCircle className="h-4 w-4" /> All clear</>
              ) : (
                <><AlertTriangle className="h-4 w-4" /> Action needed</>
              )}
            </p>
          </div>
        </div>

        {/* No data state */}
        {!selectedAgent && (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500">
            <AlertTriangle className="h-10 w-10 mb-2" />
            <p>Select an agent from the sidebar</p>
          </div>
        )}

        {selectedAgent && anomalies.length === 0 && !fetching && (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500">
            <CheckCircle className="h-10 w-10 mb-2 text-emerald-500" />
            <p className="text-lg text-emerald-400">No anomalies detected</p>
            <p className="text-sm mt-1">System is operating within normal parameters</p>
          </div>
        )}

        {fetching && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin h-8 w-8 rounded-full border-4 border-brand-500 border-t-transparent" />
          </div>
        )}

        {/* Anomaly event list */}
        {anomalies.length > 0 && (
          <div className="space-y-3">
            {anomalies.map((a) => (
              <div
                key={a.id}
                className={`rounded-xl border-l-4 p-4 ${SEVERITY_STYLES[a.severity] ?? SEVERITY_STYLES.low}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${SEVERITY_BADGE[a.severity] ?? SEVERITY_BADGE.low}`}>
                        {a.severity.toUpperCase()}
                      </span>
                      <span className="text-xs font-mono text-slate-400">{a.metric_name}</span>
                    </div>
                    <p className="text-sm font-medium">
                      {a.message || `${a.metric_name} = ${a.value}`}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatTime(a.timestamp)}
                      </span>
                      <span>Value: <span className="font-mono font-semibold text-slate-300">{a.value.toFixed(2)}</span></span>
                      {a.z_score != null && (
                        <span>Z-Score: <span className="font-mono font-semibold text-slate-300">{a.z_score.toFixed(2)}</span></span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
