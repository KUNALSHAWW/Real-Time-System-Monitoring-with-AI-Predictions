"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Alert payload pushed by the server over  WS /ws/alerts/{agentId}
 */
export interface WsAlert {
  type: "alert";
  agent_id: string;
  data: {
    metric: string;
    value: number;
    severity: string;
    message: string;
    agent_id: string;
  }[];
  timestamp: string;
}

interface UseWebSocketOptions {
  /** Agent ID to subscribe to — connection is created when set */
  agentId: string | null;
  /** Called for every alert frame received */
  onAlert?: (alert: WsAlert) => void;
  /** Reconnect delay in ms (default 3000) */
  reconnectDelay?: number;
}

export interface UseWebSocketReturn {
  connected: boolean;
  lastAlert: WsAlert | null;
  /** Manually close the socket */
  disconnect: () => void;
}

/**
 * React hook that opens a WebSocket to `ws://<host>/ws/alerts/{agentId}`.
 *
 * Automatically:
 *  - reconnects on disconnection (with configurable backoff)
 *  - sends periodic "ping" keep-alive frames
 *  - cleans up on unmount or agentId change
 */
export function useWebSocket({
  agentId,
  onAlert,
  reconnectDelay = 3_000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [connected, setConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<WsAlert | null>(null);

  // Stable callback ref so reconnect logic doesn't re-create socket
  const onAlertRef = useRef(onAlert);
  onAlertRef.current = onAlert;

  const connect = useCallback(() => {
    if (!agentId) return;

    // Derive ws url from the current page location
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host; // includes port if any
    const url = `${proto}://${host}/ws/alerts/${agentId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // Start keep-alive pings every 25 s
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 25_000);
    };

    ws.onmessage = (evt) => {
      try {
        const payload: WsAlert = JSON.parse(evt.data);
        setLastAlert(payload);
        onAlertRef.current?.(payload);
      } catch {
        // ignore non-JSON frames
      }
    };

    ws.onclose = () => {
      cleanup();
      setConnected(false);
      // Schedule reconnect
      reconnectTimer.current = setTimeout(connect, reconnectDelay);
    };

    ws.onerror = () => {
      ws.close(); // triggers onclose → reconnect
    };
  }, [agentId, reconnectDelay]);

  const cleanup = useCallback(() => {
    if (pingRef.current) clearInterval(pingRef.current);
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    pingRef.current = null;
    reconnectTimer.current = null;
  }, []);

  const disconnect = useCallback(() => {
    cleanup();
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, [cleanup]);

  // Open / re-open when agentId changes
  useEffect(() => {
    disconnect();
    if (agentId) connect();
    return disconnect;
  }, [agentId, connect, disconnect]);

  return { connected, lastAlert, disconnect };
}
