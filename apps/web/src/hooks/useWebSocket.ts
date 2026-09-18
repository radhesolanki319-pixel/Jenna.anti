'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketConnectionStatus, WebSocketMessage } from '@/types/api';

const HEARTBEAT_INTERVAL_MS = 10000;
const MAX_RECONNECT_ATTEMPTS = 5;

export interface UseWebSocketReturn {
  status: WebSocketConnectionStatus;
  lastMessage: WebSocketMessage | null;
  lastHeartbeat: Date | null;
  latencyMs: number | null;
  reconnectAttempts: number;
  send: (msg: Record<string, any>) => void;
  reconnect: () => void;
  disconnect: () => void;
}

export function useWebSocket(urlPath: string = '/api/v1/ws'): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pingTimestampRef = useRef<number | null>(null);
  const manualDisconnectRef = useRef<boolean>(false);
  const reconnectAttemptsRef = useRef<number>(0);

  const clearTimers = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const send = useCallback((msg: Record<string, any>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;

    // Prevent duplicate active connections
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    clearTimers();
    manualDisconnectRef.current = false;

    // Resolve ws/wss protocol & host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
    const cleanPath = urlPath.startsWith('/') ? urlPath : `/${urlPath}`;
    const wsUrl = `${protocol}//${host}${cleanPath}`;

    setStatus((prev) => (prev === 'connected' ? 'connected' : reconnectAttemptsRef.current > 0 ? 'reconnecting' : 'connecting'));

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        setReconnectAttempts(0);

        // Start ping heartbeat
        heartbeatTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            pingTimestampRef.current = Date.now();
            send({ type: 'ping' });
          }
        }, HEARTBEAT_INTERVAL_MS);
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(data);

          if (data.type === 'pong') {
            setLastHeartbeat(new Date());
            if (pingTimestampRef.current) {
              setLatencyMs(Date.now() - pingTimestampRef.current);
              pingTimestampRef.current = null;
            }
          }
        } catch {
          // Ignored non-JSON payloads
        }
      };

      ws.onerror = () => {
        setStatus('error');
      };

      ws.onclose = () => {
        clearTimers();
        wsRef.current = null;

        if (manualDisconnectRef.current) {
          setStatus('disconnected');
          return;
        }

        reconnectAttemptsRef.current += 1;
        const currentAttempts = reconnectAttemptsRef.current;
        setReconnectAttempts(currentAttempts);

        if (currentAttempts <= MAX_RECONNECT_ATTEMPTS) {
          setStatus('reconnecting');
          const delay = Math.min(1000 * Math.pow(1.5, currentAttempts - 1), 15000);
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          setStatus('disconnected');
        }
      };
    } catch {
      setStatus('error');
    }
  }, [urlPath, clearTimers, send]);

  const disconnect = useCallback(() => {
    manualDisconnectRef.current = true;
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, [clearTimers]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    setReconnectAttempts(0);
    connect();
  }, [disconnect, connect]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [urlPath]); // Only re-run when urlPath actually changes!

  return {
    status,
    lastMessage,
    lastHeartbeat,
    latencyMs,
    reconnectAttempts,
    send,
    reconnect,
    disconnect,
  };
}
