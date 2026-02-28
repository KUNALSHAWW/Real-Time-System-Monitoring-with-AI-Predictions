"use client";

interface Props {
  label: string;
  value: string | number;
  sub?: string;
  color?: "default" | "green" | "yellow" | "red";
}

const bgMap = {
  default: "border-slate-800 bg-slate-900",
  green: "border-emerald-800 bg-emerald-950",
  yellow: "border-yellow-800 bg-yellow-950",
  red: "border-red-800 bg-red-950",
};

const valMap = {
  default: "text-white",
  green: "text-emerald-300",
  yellow: "text-yellow-300",
  red: "text-red-300",
};

export default function StatCard({ label, value, sub, color = "default" }: Props) {
  return (
    <div className={`rounded-xl border p-4 ${bgMap[color]}`}>
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <p className={`mt-1 text-2xl font-bold ${valMap[color]}`}>{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}
