"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useAgent } from "@/context/AgentContext";
import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import MetricChart from "@/components/MetricChart";
import { Activity, TrendingUp, TrendingDown, Minus, AlertTriangle, ShieldCheck } from "lucide-react";

interface Prediction {
  timestamp: string;
  predicted_value: number;
  confidence: number;
}

interface ForecastData {
  metric_name: string;
  agent_id: string;
  current_value: number;
  predictions: Prediction[];
  next_anomaly_probability: number;
  explanation: string;
  data_points_used: number;
}

interface RiskData {
  agent_id: string;
  risk_level: string;
  overall_probability: number;
  metrics_risk: Record<string, { current: number; probability: number; trend: string }>;
}

interface PredictiveAlert {
  metric: string;
  severity: string;
  current_value: number;
  predicted_max: number;
  probability: number;
  message: string;
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "increasing") return <TrendingUp className="h-4 w-4 text-red-400" />;
  if (trend === "decreasing") return <TrendingDown className="h-4 w-4 text-emerald-400" />;
  return <Minus className="h-4 w-4 text-slate-400" />;
}

function riskColor(level: string) {
  if (level === "high") return "text-red-400 bg-red-950/50 border-red-700";
  if (level === "medium") return "text-yellow-400 bg-yellow-950/50 border-yellow-700";
  return "text-emerald-400 bg-emerald-950/50 border-emerald-700";
}

function probBar(prob: number) {
  const pct = Math.round(prob * 100);
  const color = prob > 0.7 ? "bg-red-500" : prob > 0.4 ? "bg-yellow-500" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-slate-400 w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function PredictionsPage() {
  const { user, loading, token } = useAuth();
  const { agents, selectedAgent, setSelectedAgent } = useAgent();
  const router = useRouter();

  const [forecasts, setForecasts] = useState<Record<string, ForecastData>>({});
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [alerts, setAlerts] = useState<PredictiveAlert[]>([]);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  const fetchAll = useCallback(async () => {
    if (!token || !selectedAgent) return;
    setFetching(true);
    try {
      const metrics = ["cpu", "memory", "disk"];
      const results = await Promise.all(
        metrics.map((m) =>
          api
            .get<ForecastData>(`/predictions/forecast/${m}`, { params: { agent_id: selectedAgent } })
            .then(({ data }) => data)
            .catch(() => null)
        )
      );
      const map: Record<string, ForecastData> = {};
      results.forEach((r) => { if (r) map[r.metric_name] = r; });
      setForecasts(map);

      // Anomaly risk
      const { data: riskData } = await api.get<RiskData>("/predictions/anomaly-risk", {
        params: { agent_id: selectedAgent },
      });
      setRisk(riskData);

      // Predictive alerts
      const { data: alertData } = await api.get<{ alerts: PredictiveAlert[] }>("/predictions/alerts/predictive", {
        params: { agent_id: selectedAgent },
      });
      setAlerts(alertData.alerts || []);
    } catch {
      /* ignore */
    } finally {
      setFetching(false);
    }
  }, [token, selectedAgent]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Refresh every 30s
  useEffect(() => {
    if (!token || !selectedAgent) return;
    const id = setInterval(fetchAll, 30_000);
    return () => clearInterval(id);
  }, [token, selectedAgent, fetchAll]);

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
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-brand-400" />
            Predictions &amp; Forecasting
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-powered forecasts for{" "}
            <span className="font-mono text-slate-300">{selectedAgent ?? "no agent"}</span>
          </p>
        </div>

        {!selectedAgent && (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500">
            <Activity className="h-10 w-10 mb-2" />
            <p>Select an agent from the sidebar</p>
          </div>
        )}

        {fetching && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin h-8 w-8 rounded-full border-4 border-brand-500 border-t-transparent" />
          </div>
        )}

        {selectedAgent && !fetching && (
          <>
            {/* Overall risk card */}
            {risk && (
              <div className={`mb-6 rounded-xl border p-5 ${riskColor(risk.risk_level)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wider opacity-70">Overall Risk Level</p>
                    <p className="text-3xl font-bold mt-1">{risk.risk_level.toUpperCase()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs uppercase tracking-wider opacity-70">Probability</p>
                    <p className="text-3xl font-bold mt-1">{Math.round(risk.overall_probability * 100)}%</p>
                  </div>
                </div>

                {/* Per-metric risk breakdown */}
                <div className="mt-4 grid grid-cols-3 gap-4">
                  {Object.entries(risk.metrics_risk).map(([metric, info]) => (
                    <div key={metric} className="rounded-lg bg-black/20 p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold uppercase">{metric}</span>
                        <TrendIcon trend={info.trend} />
                      </div>
                      <p className="text-lg font-mono font-bold">{info.current.toFixed(1)}%</p>
                      {probBar(info.probability)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Predictive alerts */}
            {alerts.length > 0 && (
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-400" />
                  Predictive Alerts (Next 30 min)
                </h2>
                <div className="space-y-2">
                  {alerts.map((a, i) => (
                    <div
                      key={i}
                      className={`rounded-lg border-l-4 p-3 ${
                        a.severity === "high"
                          ? "border-red-500 bg-red-950/30 text-red-200"
                          : "border-yellow-500 bg-yellow-950/30 text-yellow-200"
                      }`}
                    >
                      <p className="text-sm font-medium">{a.message}</p>
                      <p className="text-xs mt-1 opacity-70">
                        Current: {a.current_value}% → Predicted max: {a.predicted_max}% | Probability: {Math.round(a.probability * 100)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {alerts.length === 0 && risk && (
              <div className="mb-6 rounded-lg border border-emerald-800 bg-emerald-950/30 p-4 flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-emerald-400" />
                <div>
                  <p className="text-sm font-medium text-emerald-300">No predictive alerts</p>
                  <p className="text-xs text-emerald-500">All metrics forecasted to stay within safe limits</p>
                </div>
              </div>
            )}

            {/* Forecast charts */}
            <h2 className="text-lg font-semibold text-white mb-3">Forecast Charts</h2>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {Object.entries(forecasts).map(([metric, fc]) => {
                const chartData = fc.predictions.map((p) => ({
                  timestamp: p.timestamp,
                  value: p.predicted_value,
                }));
                const colors: Record<string, string> = {
                  cpu: "#6366f1",
                  memory: "#22d3ee",
                  disk: "#f59e0b",
                };
                return (
                  <div key={metric}>
                    <MetricChart
                      title={`${metric.toUpperCase()} Forecast`}
                      data={chartData}
                      color={colors[metric] || "#6366f1"}
                    />
                    <p className="text-xs text-slate-500 mt-1 px-2">{fc.explanation}</p>
                  </div>
                );
              })}
            </div>

            {/* Info footer */}
            {Object.keys(forecasts).length > 0 && (
              <p className="text-xs text-slate-600 mt-4 text-center">
                Forecasts use moving-average analysis on{" "}
                {Object.values(forecasts)[0]?.data_points_used ?? 0} recent data points
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
