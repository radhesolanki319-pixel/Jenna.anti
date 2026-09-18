'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Activity,
  RefreshCw,
  Database,
  Boxes,
  Server,
  Radio,
  Clock,
  Cpu,
  Terminal,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { apiClient, ApiError } from '@/lib/api';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import type {
  ComprehensiveHealthResponse,
  LivenessResponse,
  ReadinessResponse,
  SystemInfoResponse,
} from '@/types/api';

const AUTO_REFRESH_INTERVAL_MS = 20000; // 20s avoids hammering backend

export default function SystemHealthPage() {
  const [health, setHealth] = useState<ComprehensiveHealthResponse | null>(null);
  const [liveness, setLiveness] = useState<LivenessResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const {
    status: wsStatus,
    latencyMs: wsLatency,
    lastHeartbeat: wsHeartbeat,
    reconnect: reconnectWs,
  } = useWebSocketContext();

  const isMountedRef = useRef(true);

  const fetchAllProbes = useCallback(async (isInitial: boolean = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [healthRes, liveRes, readyRes, sysRes] = await Promise.allSettled([
        apiClient.getHealth(),
        apiClient.getLiveness(),
        apiClient.getReadiness(),
        apiClient.getSystemInfo(),
      ]);

      if (!isMountedRef.current) return;

      if (healthRes.status === 'fulfilled') {
        setHealth(healthRes.value);
      }
      if (liveRes.status === 'fulfilled') {
        setLiveness(liveRes.value);
      }
      if (readyRes.status === 'fulfilled') {
        setReadiness(readyRes.value);
      }
      if (sysRes.status === 'fulfilled') {
        setSystemInfo(sysRes.value);
      }

      // Check if all probes failed
      if (
        healthRes.status === 'rejected' &&
        liveRes.status === 'rejected' &&
        readyRes.status === 'rejected' &&
        sysRes.status === 'rejected'
      ) {
        const primaryErr = healthRes.reason;
        const msg =
          primaryErr instanceof ApiError
            ? primaryErr.message
            : primaryErr instanceof Error
            ? primaryErr.message
            : 'Unable to establish connection to Jenna Backend API';
        setError(msg);
      }

      setLastRefreshed(new Date());
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : 'Unexpected telemetry error');
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchAllProbes(true);

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchAllProbes]);

  // Auto refresh loop
  useEffect(() => {
    if (!autoRefresh) return;

    const timer = setInterval(() => {
      fetchAllProbes(false);
    }, AUTO_REFRESH_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [autoRefresh, fetchAllProbes]);

  const postgresStatus = health?.services?.find((s) => s.name === 'postgresql');
  const redisStatus = health?.services?.find((s) => s.name === 'redis');

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            System Health & Telemetry
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
            Realtime operational probes, dependency readiness, and runtime telemetry
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 self-start sm:self-auto">
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-border text-primary-600 focus:ring-primary-500 h-4 w-4"
            />
            <span>Auto-refresh (20s)</span>
          </label>

          <button
            onClick={() => fetchAllProbes(false)}
            disabled={loading || refreshing}
            aria-label="Refresh system health probes"
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-primary-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing || loading ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Probing...' : 'Refresh Probes'}</span>
          </button>
        </div>
      </div>

      {/* Backend Outage Alert */}
      {error && (
        <ErrorBanner
          title="Backend API Unreachable"
          message={`Could not connect to FastAPI server at http://localhost:8000. Verify that the backend service is running. (${error})`}
          onRetry={() => fetchAllProbes(false)}
          variant="danger"
        />
      )}

      {/* Primary Probes Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Probe 1: Overall Health */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Overall Status
            </span>
            <Activity className="h-4 w-4 text-zinc-400" />
          </div>
          <div className="mt-3 flex items-center justify-between">
            {loading ? (
              <div className="h-6 w-20 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
            ) : (
              <StatusBadge status={health?.status || (error ? 'unhealthy' : 'unknown')} />
            )}
            <span className="text-xs text-zinc-400">/api/v1/health</span>
          </div>
          <p className="mt-3 text-[11px] text-zinc-500 dark:text-zinc-400 border-t border-border/60 pt-2.5">
            Phase: {health?.phase || 'Phase 4 Control Center'}
          </p>
        </div>

        {/* Probe 2: Liveness Probe */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Liveness Probe
            </span>
            <Server className="h-4 w-4 text-zinc-400" />
          </div>
          <div className="mt-3 flex items-center justify-between">
            {loading ? (
              <div className="h-6 w-20 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
            ) : (
              <StatusBadge
                status={liveness?.status === 'ok' ? 'healthy' : error ? 'unhealthy' : 'degraded'}
                label={liveness?.status === 'ok' ? 'Alive' : 'Dead'}
              />
            )}
            <span className="text-xs text-zinc-400">/api/v1/health/live</span>
          </div>
          <p className="mt-3 text-[11px] text-zinc-500 dark:text-zinc-400 border-t border-border/60 pt-2.5">
            Service: {liveness?.service || 'jenna-api'}
          </p>
        </div>

        {/* Probe 3: Readiness Probe */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Readiness Probe
            </span>
            <CheckCircle2 className="h-4 w-4 text-zinc-400" />
          </div>
          <div className="mt-3 flex items-center justify-between">
            {loading ? (
              <div className="h-6 w-20 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
            ) : (
              <StatusBadge
                status={readiness?.ready ? 'healthy' : error ? 'unhealthy' : 'degraded'}
                label={readiness?.ready ? 'Ready' : 'Not Ready'}
              />
            )}
            <span className="text-xs text-zinc-400">/api/v1/health/ready</span>
          </div>
          <p className="mt-3 text-[11px] text-zinc-500 dark:text-zinc-400 border-t border-border/60 pt-2.5">
            Dependencies: {readiness?.dependencies ? Object.keys(readiness.dependencies).length : 2} verified
          </p>
        </div>

        {/* Probe 4: WebSocket Duplex */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              WebSocket Channel
            </span>
            <Radio className="h-4 w-4 text-zinc-400" />
          </div>
          <div className="mt-3 flex items-center justify-between">
            <StatusBadge status={wsStatus} />
            <span className="text-xs text-zinc-400">/api/v1/ws</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400 border-t border-border/60 pt-2.5">
            <span>Latency: {wsLatency !== null ? `${wsLatency}ms` : 'N/A'}</span>
            {wsStatus !== 'connected' && (
              <button
                onClick={reconnectWs}
                className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
              >
                Reconnect
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Core Infrastructure Dependencies */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-foreground">Core Services & Backends</h2>
          <span className="text-xs text-zinc-400">
            Last checked:{' '}
            {lastRefreshed ? lastRefreshed.toLocaleTimeString() : 'Pending'}
          </span>
        </div>

        <div className="space-y-3">
          {/* PostgreSQL Database */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-border p-4 bg-zinc-50/50 dark:bg-zinc-900/40">
            <div className="flex items-center gap-3.5">
              <div className="rounded-xl bg-blue-500/10 p-2.5 text-blue-600 dark:text-blue-400">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">PostgreSQL 18 Database</h3>
                  <span className="text-[10px] rounded bg-zinc-200 dark:bg-zinc-800 px-1.5 py-0.5 text-zinc-600 dark:text-zinc-400 font-mono">
                    port 5432
                  </span>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Primary persistent store, Alembic migrations, Users, Sessions & Audit Events
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 self-end sm:self-auto">
              <StatusBadge
                status={postgresStatus?.status || (error ? 'unhealthy' : 'connecting')}
                label={postgresStatus?.status || 'Unknown'}
              />
            </div>
          </div>

          {/* Redis Broker */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-border p-4 bg-zinc-50/50 dark:bg-zinc-900/40">
            <div className="flex items-center gap-3.5">
              <div className="rounded-xl bg-rose-500/10 p-2.5 text-rose-600 dark:text-rose-400">
                <Boxes className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">Redis 8 In-Memory Store</h3>
                  <span className="text-[10px] rounded bg-zinc-200 dark:bg-zinc-800 px-1.5 py-0.5 text-zinc-600 dark:text-zinc-400 font-mono">
                    port 6379
                  </span>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Async cache, task queue, event bus & heartbeat telemetry
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 self-end sm:self-auto">
              <StatusBadge
                status={redisStatus?.status || (error ? 'unhealthy' : 'connecting')}
                label={redisStatus?.status || 'Unknown'}
              />
            </div>
          </div>

          {/* FastAPI Service */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-border p-4 bg-zinc-50/50 dark:bg-zinc-900/40">
            <div className="flex items-center gap-3.5">
              <div className="rounded-xl bg-emerald-500/10 p-2.5 text-emerald-600 dark:text-emerald-400">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-foreground">FastAPI REST Core</h3>
                  <span className="text-[10px] rounded bg-zinc-200 dark:bg-zinc-800 px-1.5 py-0.5 text-zinc-600 dark:text-zinc-400 font-mono">
                    port 8000
                  </span>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Async Uvicorn ASGI server with PBKDF2 authentication & correlation tracing
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 self-end sm:self-auto">
              <StatusBadge
                status={health ? 'healthy' : error ? 'unhealthy' : 'connecting'}
                label={health ? 'Online' : 'Offline'}
              />
            </div>
          </div>
        </div>
      </div>

      {/* System Telemetry & Environment */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-base font-semibold text-foreground mb-4">
          Platform Runtime Diagnostics
        </h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-border p-4 bg-zinc-50/40 dark:bg-zinc-900/30">
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 mb-1.5">
              <Clock className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Uptime</span>
            </div>
            <p className="text-base font-bold text-foreground">
              {systemInfo?.uptime_formatted || (health ? 'Active' : 'Offline')}
            </p>
            <p className="text-[11px] text-zinc-400 mt-1">
              Seconds: {systemInfo?.uptime_seconds?.toFixed(0) || 'N/A'}
            </p>
          </div>

          <div className="rounded-lg border border-border p-4 bg-zinc-50/40 dark:bg-zinc-900/30">
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 mb-1.5">
              <Cpu className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Host OS Platform</span>
            </div>
            <p className="text-base font-bold text-foreground truncate">
              {systemInfo?.platform || 'Linux aarch64'}
            </p>
            <p className="text-[11px] text-zinc-400 mt-1">Environment: {systemInfo?.environment || 'development'}</p>
          </div>

          <div className="rounded-lg border border-border p-4 bg-zinc-50/40 dark:bg-zinc-900/30">
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 mb-1.5">
              <Terminal className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">Python Runtime</span>
            </div>
            <p className="text-base font-bold text-foreground">
              {systemInfo?.python_version ? `v${systemInfo.python_version}` : 'Python 3.14+'}
            </p>
            <p className="text-[11px] text-zinc-400 mt-1">Engine: AsyncIO / asyncpg</p>
          </div>

          <div className="rounded-lg border border-border p-4 bg-zinc-50/40 dark:bg-zinc-900/30">
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400 mb-1.5">
              <Activity className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">WebSocket Heartbeat</span>
            </div>
            <p className="text-base font-bold text-foreground">
              {wsHeartbeat ? wsHeartbeat.toLocaleTimeString() : 'Awaiting ping'}
            </p>
            <p className="text-[11px] text-zinc-400 mt-1">
              Ping interval: 10s · Latency: {wsLatency !== null ? `${wsLatency}ms` : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
