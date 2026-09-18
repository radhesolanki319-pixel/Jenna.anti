'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { apiClient } from '@/lib/api';
import { UsageSummaryResponse, UsageLogEntry } from '@jenna/types';
import {
  BarChart3,
  Coins,
  Cpu,
  Zap,
  Clock,
  RefreshCw,
  Gauge,
  Layers,
} from 'lucide-react';

export default function UsagePage() {
  const [summary, setSummary] = useState<UsageSummaryResponse | null>(null);
  const [logs, setLogs] = useState<UsageLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, logsRes] = await Promise.all([
        apiClient.getUsageSummary().catch(() => null),
        apiClient.getUsageLogs(50).catch(() => []),
      ]);
      setSummary(summaryRes);
      setLogs(logsRes);
    } catch (err) {
      console.error('Failed to load usage data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-primary-500" />
              Usage & Cost Visibility
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Live telemetry tracking LLM token consumption, latency metrics, estimated API costs, and daily rate quotas.
            </p>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md border border-border bg-card hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Metrics Grid */}
        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">Total AI Requests</span>
                <Cpu className="h-4 w-4 text-primary-500" />
              </div>
              <p className="text-2xl font-bold text-foreground mt-2">{summary.total_requests}</p>
              <span className="text-[11px] text-zinc-400">Generations & Agent steps</span>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">Total Tokens</span>
                <Layers className="h-4 w-4 text-blue-500" />
              </div>
              <p className="text-2xl font-bold text-foreground mt-2">
                {summary.total_tokens.toLocaleString()}
              </p>
              <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                <span>In: {summary.prompt_tokens.toLocaleString()}</span>
                <span>•</span>
                <span>Out: {summary.completion_tokens.toLocaleString()}</span>
              </div>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">Estimated Cost</span>
                <Coins className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">
                ${summary.estimated_cost_usd.toFixed(4)}
              </p>
              <span className="text-[11px] text-zinc-400">Blended provider rates</span>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">Avg Latency</span>
                <Clock className="h-4 w-4 text-amber-500" />
              </div>
              <p className="text-2xl font-bold text-foreground mt-2">
                {summary.avg_latency_ms.toFixed(0)} ms
              </p>
              <span className="text-[11px] text-zinc-400">Per model completion</span>
            </div>
          </div>
        )}

        {/* Daily Quota Progress */}
        {summary && (
          <div className="p-5 rounded-lg border border-border bg-card space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Gauge className="h-4 w-4 text-primary-500" />
                <span className="text-sm font-semibold text-foreground">Daily Token Quota Allocation</span>
              </div>
              <span className="text-xs font-mono text-zinc-500">
                {summary.total_tokens.toLocaleString()} / {summary.daily_quota_tokens.toLocaleString()} tokens ({summary.quota_percent_used}%)
              </span>
            </div>
            {/* Bar */}
            <div className="w-full h-3 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  summary.quota_percent_used > 85
                    ? 'bg-rose-500'
                    : summary.quota_percent_used > 60
                    ? 'bg-amber-500'
                    : 'bg-primary-600'
                }`}
                style={{ width: `${Math.min(100, summary.quota_percent_used)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-zinc-500">
              <span>Remaining: {summary.quota_remaining_tokens.toLocaleString()} tokens</span>
              <span>Resets daily at 00:00 UTC</span>
            </div>
          </div>
        )}

        {/* Recent Usage Logs Table */}
        <div className="border border-border rounded-lg overflow-hidden bg-card">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground">Recent Model Telemetry Logs</h3>
          </div>
          {loading ? (
            <div className="p-8 text-center text-sm text-zinc-500">Loading telemetry logs...</div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-sm text-zinc-500">No requests recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 border-b border-border">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Provider</th>
                    <th className="p-3">Model</th>
                    <th className="p-3">Prompt</th>
                    <th className="p-3">Completion</th>
                    <th className="p-3">Total</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                      <td className="p-3 text-zinc-500 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td className="p-3 font-semibold text-foreground uppercase">{log.provider}</td>
                      <td className="p-3 text-zinc-600 dark:text-zinc-400">{log.model}</td>
                      <td className="p-3 text-zinc-500">{log.prompt_tokens}</td>
                      <td className="p-3 text-zinc-500">{log.completion_tokens}</td>
                      <td className="p-3 font-semibold text-foreground">{log.total_tokens}</td>
                      <td className="p-3 text-zinc-500">{log.latency_ms.toFixed(0)} ms</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                            log.success
                              ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                              : 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                          }`}
                        >
                          {log.success ? 'OK' : 'ERR'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
