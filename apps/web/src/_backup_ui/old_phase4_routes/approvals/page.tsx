'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { apiClient } from '@/lib/api';
import {
  PendingApprovalsResponse,
  PermissionPoliciesResponse,
  AuditEventItem,
  AgentTask,
  ImprovementProposal,
} from '@jenna/types';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Shield,
  Clock,
  History,
  Info,
  RefreshCw,
} from 'lucide-react';

export default function ApprovalsPage() {
  const [pending, setPending] = useState<PendingApprovalsResponse | null>(null);
  const [policies, setPolicies] = useState<PermissionPoliciesResponse | null>(null);
  const [history, setHistory] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'queue' | 'policies' | 'history'>('queue');
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pendingRes, policiesRes, historyRes] = await Promise.all([
        apiClient.getPendingApprovals().catch(() => ({ tasks: [], proposals: [], total_pending: 0 })),
        apiClient.getPermissionPolicies().catch(() => null),
        apiClient.getApprovalHistory(25).catch(() => []),
      ]);
      setPending(pendingRes);
      setPolicies(policiesRes);
      setHistory(historyRes);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load approvals data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDecision = async (
    itemType: 'task' | 'proposal',
    itemId: string,
    decision: 'approve' | 'reject'
  ) => {
    setActionLoading(itemId);
    setMessage(null);
    try {
      const reason = rejectReasons[itemId] || undefined;
      await apiClient.submitApprovalDecision({
        item_type: itemType,
        item_id: itemId,
        decision,
        reason,
      });
      setMessage({
        text: `Successfully ${decision === 'approve' ? 'approved' : 'rejected'} ${itemType} ${itemId.slice(0, 8)}`,
        type: 'success',
      });
      await loadData();
    } catch (err: any) {
      setMessage({ text: err.message || `Failed to ${decision} item`, type: 'error' });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Shield className="h-6 w-6 text-primary-500" />
              Approvals & Permissions Queue
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Human-in-the-loop governance: confirm or deny sensitive agent steps, tool executions, and canary proposals.
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

        {/* Message Banner */}
        {message && (
          <div
            className={`p-4 rounded-lg border text-sm flex items-center gap-2 ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400'
            }`}
          >
            {message.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {message.text}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('queue')}
            className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'queue'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400 font-semibold'
                : 'border-transparent text-zinc-500 hover:text-foreground'
            }`}
          >
            <Clock className="h-4 w-4" />
            Pending Queue
            {pending && pending.total_pending > 0 && (
              <span className="bg-amber-500/20 text-amber-600 dark:text-amber-400 text-xs px-2 py-0.5 rounded-full font-bold">
                {pending.total_pending}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('policies')}
            className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'policies'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400 font-semibold'
                : 'border-transparent text-zinc-500 hover:text-foreground'
            }`}
          >
            <Info className="h-4 w-4" />
            3-Tier Permission Matrix
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'history'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400 font-semibold'
                : 'border-transparent text-zinc-500 hover:text-foreground'
            }`}
          >
            <History className="h-4 w-4" />
            Approval History ({history.length})
          </button>
        </div>

        {/* Tab 1: Pending Queue */}
        {activeTab === 'queue' && (
          <div className="space-y-4">
            {loading ? (
              <div className="p-8 text-center text-sm text-zinc-500">Loading pending approvals...</div>
            ) : pending?.total_pending === 0 ? (
              <div className="p-12 text-center border border-dashed border-border rounded-lg bg-card">
                <CheckCircle className="h-10 w-10 text-emerald-500 mx-auto mb-3" />
                <h3 className="font-semibold text-foreground">No Actions Awaiting Confirmation</h3>
                <p className="text-xs text-zinc-500 mt-1">
                  All agent tasks and improvement proposals are clear. Any sensitive action will pause here.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Pending Tasks */}
                {pending?.tasks.map((task: AgentTask) => (
                  <div
                    key={task.id}
                    className="border border-amber-500/30 bg-amber-500/5 dark:bg-amber-500/10 rounded-lg p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        <span className="font-semibold text-foreground">
                          Agent Task Confirmation Required
                        </span>
                        <span className="text-xs font-mono bg-amber-500/20 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded">
                          {task.agent_type}
                        </span>
                      </div>
                      <span className="text-xs text-zinc-500">ID: {task.id.slice(0, 8)}</span>
                    </div>

                    <p className="text-sm text-foreground">{task.description}</p>
                    {task.confirmation_reason && (
                      <div className="p-3 rounded bg-card border border-border text-xs text-zinc-600 dark:text-zinc-400">
                        <strong className="text-foreground">Sensitive Rationale:</strong> {task.confirmation_reason}
                      </div>
                    )}

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2">
                      <input
                        type="text"
                        placeholder="Optional reason for approval or rejection..."
                        value={rejectReasons[task.id] || ''}
                        onChange={(e) =>
                          setRejectReasons({ ...rejectReasons, [task.id]: e.target.value })
                        }
                        className="flex-1 px-3 py-1.5 text-xs rounded border border-border bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                      <button
                        onClick={() => handleDecision('task', task.id, 'approve')}
                        disabled={actionLoading === task.id}
                        className="px-4 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <CheckCircle className="h-3.5 w-3.5" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleDecision('task', task.id, 'reject')}
                        disabled={actionLoading === task.id}
                        className="px-4 py-1.5 text-xs font-semibold rounded bg-rose-600 hover:bg-rose-700 text-white flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Reject
                      </button>
                    </div>
                  </div>
                ))}

                {/* Pending Proposals */}
                {pending?.proposals.map((proposal: any) => (
                  <div
                    key={proposal.proposal_id}
                    className="border border-blue-500/30 bg-blue-500/5 dark:bg-blue-500/10 rounded-lg p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="h-5 w-5 text-blue-500" />
                        <span className="font-semibold text-foreground">
                          Self-Improvement Optimization Proposal
                        </span>
                        <span className="text-xs font-mono bg-blue-500/20 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                          {proposal.category}
                        </span>
                      </div>
                      <span className="text-xs text-zinc-500">
                        {proposal.baseline_version} &rarr; {proposal.target_version}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-foreground">{proposal.title}</h4>
                    <p className="text-xs text-zinc-600 dark:text-zinc-400">{proposal.rationale}</p>

                    <div className="flex items-center gap-2 pt-2 justify-end">
                      <button
                        onClick={() => handleDecision('proposal', proposal.proposal_id, 'approve')}
                        disabled={actionLoading === proposal.proposal_id}
                        className="px-4 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 transition-colors"
                      >
                        <CheckCircle className="h-3.5 w-3.5" />
                        Authorize Deployment
                      </button>
                      <button
                        onClick={() => handleDecision('proposal', proposal.proposal_id, 'reject')}
                        disabled={actionLoading === proposal.proposal_id}
                        className="px-4 py-1.5 text-xs font-semibold rounded bg-rose-600 hover:bg-rose-700 text-white flex items-center gap-1.5 transition-colors"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Reject Proposal
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Permission Policies */}
        {activeTab === 'policies' && policies && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              {policies.tiers.map((t) => (
                <div key={t.tier} className="p-4 rounded-lg border border-border bg-card space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-foreground">
                      {t.tier}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-semibold ${
                        t.requires_confirmation
                          ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                          : 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                      }`}
                    >
                      {t.requires_confirmation ? 'Requires Confirmation' : 'Auto Allowed'}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">{t.description}</p>
                </div>
              ))}
            </div>

            <div className="p-5 rounded-lg border border-border bg-card space-y-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary-500" />
                Immutable Governance Invariants
              </h3>
              <ul className="space-y-1.5 text-xs text-zinc-600 dark:text-zinc-400 list-disc list-inside">
                {policies.governance_invariants.map((inv, i) => (
                  <li key={i}>{inv}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Tab 3: Approval History */}
        {activeTab === 'history' && (
          <div className="border border-border rounded-lg overflow-hidden bg-card">
            {history.length === 0 ? (
              <div className="p-8 text-center text-sm text-zinc-500">No approval history recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 border-b border-border">
                    <tr>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Resource Type</th>
                      <th className="p-3">Resource ID</th>
                      <th className="p-3">Decision</th>
                      <th className="p-3">User Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {history.map((h) => {
                      const isConfirmed = h.metadata?.confirmed;
                      return (
                        <tr key={h.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                          <td className="p-3 text-zinc-500 font-mono">
                            {new Date(h.created_at).toLocaleString()}
                          </td>
                          <td className="p-3 font-semibold text-foreground">
                            {h.metadata?.resource_type || 'task'}
                          </td>
                          <td className="p-3 font-mono text-zinc-500">
                            {h.metadata?.resource_id?.slice(0, 8) || 'N/A'}
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded font-semibold ${
                                isConfirmed
                                  ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                                  : 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                              }`}
                            >
                              {isConfirmed ? 'APPROVED' : 'REJECTED'}
                            </span>
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400">
                            {h.metadata?.user_reason || '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
