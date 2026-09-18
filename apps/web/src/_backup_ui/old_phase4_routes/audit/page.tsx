'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { apiClient } from '@/lib/api';
import { AuditEventItem, AuditStats } from '@jenna/types';
import {
  FileText,
  CheckCircle,
  XCircle,
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Lock,
} from 'lucide-react';

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [eventsRes, statsRes] = await Promise.all([
        apiClient.listAuditEvents(filterType || undefined, 100),
        apiClient.getAuditStats().catch(() => null),
      ]);
      setEvents(eventsRes);
      setStats(statsRes);
    } catch (err) {
      console.error('Failed to load audit events', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterType]);

  const filteredEvents = events.filter((e) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      e.event_type.toLowerCase().includes(q) ||
      e.action.toLowerCase().includes(q) ||
      (e.request_id && e.request_id.toLowerCase().includes(q)) ||
      JSON.stringify(e.metadata || {}).toLowerCase().includes(q)
    );
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <FileText className="h-6 w-6 text-primary-500" />
              Audit Trail Explorer
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Immutable audit log of authentication, authorization, agent steps, device control, and system state changes.
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

        {/* Security / Zero Secrets Banner */}
        <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/5 dark:bg-emerald-500/10 flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <div className="text-xs text-zinc-600 dark:text-zinc-300">
            <strong className="text-foreground">Sanitized Telemetry Invariant:</strong> System automatically scrubs
            passwords, session tokens, private keys, and external API credentials before persistent recording.
          </div>
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-zinc-500">Total Recorded Events</span>
              <p className="text-2xl font-bold text-foreground mt-1">{stats.total_events}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-zinc-500">Successful Actions</span>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                {stats.successful_events}
              </p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <span className="text-xs text-zinc-500">Denied or Failed Actions</span>
              <p className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">
                {stats.failed_events}
              </p>
            </div>
          </div>
        )}

        {/* Filter and Search Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search by event type, action, request ID, or metadata..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-md border border-border bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-zinc-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 text-xs rounded-md border border-border bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">All Event Types</option>
              <option value="authz">Authorization (authz)</option>
              <option value="authn">Authentication (authn)</option>
              <option value="agent_confirmation_response">Agent Confirmation</option>
              <option value="tool_execution">Tool Execution</option>
              <option value="voice_event">Voice Event</option>
              <option value="vision_event">Vision Event</option>
              <option value="device_event">Device Event</option>
              <option value="ai_request">AI Request</option>
            </select>
          </div>
        </div>

        {/* Audit Events Table */}
        <div className="border border-border rounded-lg overflow-hidden bg-card">
          {loading ? (
            <div className="p-8 text-center text-sm text-zinc-500">Loading audit trail...</div>
          ) : filteredEvents.length === 0 ? (
            <div className="p-8 text-center text-sm text-zinc-500">No matching audit events found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 border-b border-border">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Event Type</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Request ID</th>
                    <th className="p-3">Sanitized Metadata</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {filteredEvents.map((event) => (
                    <tr key={event.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                      <td className="p-3 text-zinc-500 whitespace-nowrap">
                        {new Date(event.created_at).toLocaleString()}
                      </td>
                      <td className="p-3 font-semibold text-foreground">{event.event_type}</td>
                      <td className="p-3 text-zinc-700 dark:text-zinc-300">{event.action}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                            event.success
                              ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                              : 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                          }`}
                        >
                          {event.success ? 'SUCCESS' : 'FAILED'}
                        </span>
                      </td>
                      <td className="p-3 text-zinc-400">
                        {event.request_id ? event.request_id.slice(0, 8) : '—'}
                      </td>
                      <td className="p-3 text-zinc-500 max-w-md truncate font-mono text-[11px]">
                        {Object.keys(event.metadata || {}).length > 0
                          ? JSON.stringify(event.metadata)
                          : '—'}
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
