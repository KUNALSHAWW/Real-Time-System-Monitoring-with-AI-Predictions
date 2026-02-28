"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  LogOut,
  Monitor,
  Settings,
} from "lucide-react";

interface Props {
  agents: { agent_id: string; is_active: boolean; last_seen_at: string | null }[];
  selectedAgent: string | null;
  onSelectAgent: (id: string) => void;
}

const NAV_ITEMS = [
  { label: "Dashboard", icon: BarChart3, href: "/" },
  { label: "Anomalies", icon: AlertTriangle, href: "/anomalies" },
  { label: "Predictions", icon: Activity, href: "/predictions" },
  { label: "Settings", icon: Settings, href: "/settings" },
];

export default function Sidebar({ agents, selectedAgent, onSelectAgent }: Props) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-900">
      {/* Brand */}
      <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
        <Monitor className="h-6 w-6 text-brand-500" />
        <span className="text-lg font-bold text-white">SysMonitor</span>
      </div>

      {/* Agent Selector */}
      <div className="border-b border-slate-800 px-4 py-3">
        <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
          Agent
        </label>
        <select
          value={selectedAgent ?? ""}
          onChange={(e) => onSelectAgent(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white
                     focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="" disabled>
            Select agent…
          </option>
          {agents.map((a) => (
            <option key={a.agent_id} value={a.agent_id}>
              {a.agent_id} {a.is_active ? "●" : "○"}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map(({ label, icon: Icon, href }) => {
          const active = pathname === href;
          return (
            <Link
              key={label}
              href={href}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors
                ${active
                  ? "bg-brand-600/20 text-brand-400 font-semibold"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="border-t border-slate-800 px-4 py-3">
        <p className="truncate text-sm font-medium text-white">{user?.username}</p>
        <p className="truncate text-xs text-slate-500">{user?.email}</p>
        <button
          onClick={logout}
          className="mt-2 flex items-center gap-2 text-xs text-slate-400 hover:text-red-400 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
