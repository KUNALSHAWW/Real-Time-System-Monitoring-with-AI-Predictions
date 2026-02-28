"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useAgent } from "@/context/AgentContext";
import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Settings as SettingsIcon, Key, User, Clock, Copy, Check, RefreshCw } from "lucide-react";

interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  api_key: string;
  is_active: boolean;
  created_at: string;
  agents: { agent_id: string; is_active: boolean; last_seen_at: string | null }[];
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString();
}

function timeSince(iso: string | null) {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function SettingsPage() {
  const { user, loading, token } = useAuth();
  const { agents, selectedAgent, setSelectedAgent } = useAgent();
  const router = useRouter();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!loading && !token) router.push("/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (!token) return;
    api
      .get<UserProfile>("/auth/me")
      .then(({ data }) => setProfile(data))
      .catch(() => {});
  }, [token]);

  const copyApiKey = () => {
    if (!profile) return;
    navigator.clipboard.writeText(profile.api_key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
            <SettingsIcon className="h-6 w-6 text-slate-400" />
            Settings
          </h1>
          <p className="text-sm text-slate-500 mt-1">Account, API keys, and agent management</p>
        </div>

        <div className="max-w-2xl space-y-6">
          {/* Account info */}
          <section className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <User className="h-5 w-5 text-brand-400" />
              Account
            </h2>
            {profile && (
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-sm text-slate-400">Username</span>
                  <span className="text-sm font-medium text-white">{profile.username}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-sm text-slate-400">Email</span>
                  <span className="text-sm font-medium text-white">{profile.email}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-sm text-slate-400">User ID</span>
                  <span className="text-xs font-mono text-slate-300">{profile.user_id}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-sm text-slate-400">Status</span>
                  <span className={`text-sm font-semibold ${profile.is_active ? "text-emerald-400" : "text-red-400"}`}>
                    {profile.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-400">Member since</span>
                  <span className="text-sm text-slate-300">{formatDate(profile.created_at)}</span>
                </div>
              </div>
            )}
          </section>

          {/* API Key */}
          <section className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
              <Key className="h-5 w-5 text-yellow-400" />
              API Key
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Use this key in your agent&apos;s <code className="text-brand-400">.env</code> file as <code className="text-brand-400">USER_API_KEY</code>
            </p>
            {profile && (
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded-lg bg-black/40 border border-slate-600 px-4 py-2 text-sm font-mono text-emerald-400 break-all">
                  {profile.api_key}
                </code>
                <button
                  onClick={copyApiKey}
                  className="rounded-lg bg-slate-700 p-2.5 text-slate-300 hover:bg-slate-600 hover:text-white transition-colors"
                  title="Copy to clipboard"
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>
            )}
          </section>

          {/* Registered Agents */}
          <section className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <RefreshCw className="h-5 w-5 text-cyan-400" />
              Registered Agents
            </h2>

            {profile && profile.agents.length === 0 && (
              <div className="text-center py-8 text-slate-500">
                <p className="text-sm">No agents registered yet</p>
                <p className="text-xs mt-1">Start the agent sensor on any machine to auto-register</p>
              </div>
            )}

            {profile && profile.agents.length > 0 && (
              <div className="space-y-2">
                {profile.agents.map((a) => (
                  <div
                    key={a.agent_id}
                    className="flex items-center justify-between rounded-lg bg-black/20 border border-slate-700 px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`h-2.5 w-2.5 rounded-full ${a.is_active ? "bg-emerald-400" : "bg-slate-600"}`} />
                      <span className="text-sm font-mono font-medium text-white">{a.agent_id}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Clock className="h-3 w-3" />
                      {timeSince(a.last_seen_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Quick Setup Guide */}
          <section className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-3">Quick Agent Setup</h2>
            <div className="rounded-lg bg-black/40 p-4 text-sm font-mono text-slate-300 space-y-1">
              <p className="text-slate-500"># 1. Navigate to the agent directory</p>
              <p>cd agent/</p>
              <p className="text-slate-500 mt-2"># 2. Install dependencies</p>
              <p>pip install -r requirements.txt</p>
              <p className="text-slate-500 mt-2"># 3. Create .env with your API key</p>
              <p>SERVER_URL=http://localhost:8000</p>
              <p>USER_API_KEY=<span className="text-emerald-400">{profile?.api_key ?? "your-key-here"}</span></p>
              <p>AGENT_ID=My-Machine</p>
              <p>COLLECTION_INTERVAL=5</p>
              <p className="text-slate-500 mt-2"># 4. Start the agent</p>
              <p>python sensor.py</p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
