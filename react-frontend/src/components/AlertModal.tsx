"use client";

import type { WsAlert } from "@/hooks/useWebSocket";

interface Props {
  alert: WsAlert;
  onDismiss: () => void;
}

/**
 * Full-screen, screen-blocking red alert modal.
 * Rendered when the WebSocket delivers a CRITICAL severity alert.
 */
export default function AlertModal({ alert, onDismiss }: Props) {
  const criticalItems = alert.data.filter(
    (a) => a.severity === "critical" || a.severity === "high",
  );

  if (criticalItems.length === 0) return null;

  return (
    <div className="alert-overlay animate-pulse-alert" role="alertdialog">
      <div className="mx-4 w-full max-w-lg space-y-6 rounded-2xl border-2 border-red-500 bg-red-950 p-8 shadow-2xl">
        {/* Icon + Title */}
        <div className="flex flex-col items-center gap-3 text-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-16 w-16 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01M10.29 3.86l-8.3 14.58A1 1 0 003 20h18a1 1 0 00.92-1.39l-.01-.03-8.3-14.58a1 1 0 00-1.72-.14l-.01.01z"
            />
          </svg>
          <h2 className="text-2xl font-bold text-red-200">
            CRITICAL ALERT
          </h2>
          <p className="text-sm text-red-300">
            Agent: <span className="font-mono font-semibold">{alert.agent_id}</span>
          </p>
        </div>

        {/* Alert details */}
        <ul className="space-y-3">
          {criticalItems.map((item, i) => (
            <li
              key={i}
              className="rounded-lg bg-red-900/60 px-4 py-3 text-sm text-red-100"
            >
              <p className="font-semibold">{item.message}</p>
              <p className="mt-1 text-xs text-red-300">
                Metric: {item.metric} &middot; Value: {item.value} &middot;
                Severity: {item.severity.toUpperCase()}
              </p>
            </li>
          ))}
        </ul>

        {/* Dismiss */}
        <button
          onClick={onDismiss}
          className="w-full rounded-lg bg-red-700 py-2.5 font-semibold text-white hover:bg-red-600 transition-colors"
        >
          Acknowledge &amp; Dismiss
        </button>
      </div>
    </div>
  );
}
