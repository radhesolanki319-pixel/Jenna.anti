'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Play,
  XCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  RefreshCw,
  Search,
  ChevronRight,
  ShieldAlert,
  ArrowRight,
  Code,
  FileText,
  LineChart,
  Cpu,
  Zap,
  ListOrdered,
  Activity,
  PlusCircle,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type {
  AgentRegistryItem,
  AgentTask,
  AgentTaskDetail,
  AgentType,
  AgentTaskStatus,
  TaskPriority,
  AgentDecompositionPlan,
  AgentStepTrace,
} from '@jenna/types';

const AGENT_META: Record<AgentType, { label: string; icon: React.ElementType; color: string; desc: string }> = {
  RESEARCH: {
    label: 'Research Agent',
    icon: Search,
    color: 'border-blue-500/30 bg-blue-500/10 text-blue-400',
    desc: 'Literature synthesis, factual verification, and deep knowledge extraction.',
  },
  CODING: {
    label: 'Coding Agent',
    icon: Code,
    color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
    desc: 'Architecture design, code refactoring, bug fixing, and test generation.',
  },
  ANALYSIS: {
    label: 'Analysis Agent',
    icon: LineChart,
    color: 'border-purple-500/30 bg-purple-500/10 text-purple-400',
    desc: 'Data interpretation, root-cause investigation, and comparative tradeoff analysis.',
  },
  WRITING: {
    label: 'Writing Agent',
    icon: FileText,
    color: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
    desc: 'Technical documentation, executive briefings, release notes, and structured drafting.',
  },
  GENERAL_TASK: {
    label: 'General Agent',
    icon: Cpu,
    color: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-400',
    desc: 'Versatile multi-step execution, triage, workflow coordination, and fallback operations.',
  },
};

const STATUS_BADGES: Record<AgentTaskStatus, { label: string; bg: string; text: string }> = {
  CREATED: { label: 'Created', bg: 'bg-zinc-800 text-zinc-300 border-zinc-700', text: 'text-zinc-400' },
  QUEUED: { label: 'Queued', bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30', text: 'text-indigo-400' },
  RUNNING: { label: 'Running', bg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', text: 'text-cyan-400' },
  WAITING: { label: 'Awaiting Auth', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30', text: 'text-amber-400' },
  SUCCEEDED: { label: 'Succeeded', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', text: 'text-emerald-400' },
  FAILED: { label: 'Failed', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30', text: 'text-rose-400' },
  CANCELLED: { label: 'Cancelled', bg: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30', text: 'text-zinc-400' },
};

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<'orchestrator' | 'registry' | 'tasks'>('orchestrator');

  // Registry state
  const [registry, setRegistry] = useState<AgentRegistryItem[]>([]);
  const [loadingRegistry, setLoadingRegistry] = useState(false);

  // Tasks state
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [totalTasks, setTotalTasks] = useState(0);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskDetail, setSelectedTaskDetail] = useState<AgentTaskDetail | null>(null);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Task creation & planner form
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [agentType, setAgentType] = useState<AgentType>('GENERAL_TASK');
  const [priority, setPriority] = useState<TaskPriority>('NORMAL');
  const [autoDecompose, setAutoDecompose] = useState(true);
  const [decompositionPlan, setDecompositionPlan] = useState<AgentDecompositionPlan | null>(null);
  const [planningInProgress, setPlanningInProgress] = useState(false);
  const [creatingTask, setCreatingTask] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotify = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // Fetch Agent Registry
  const fetchRegistry = useCallback(async () => {
    setLoadingRegistry(true);
    try {
      const items = await apiClient.getAgentRegistry();
      setRegistry(items);
    } catch (err: any) {
      showNotify('error', `Failed to load agent registry: ${err.message}`);
    } finally {
      setLoadingRegistry(false);
    }
  }, []);

  // Fetch Task List
  const fetchTasks = useCallback(async () => {
    setLoadingTasks(true);
    try {
      const res = await apiClient.listAgentTasks({ limit: 30 });
      setTasks(res.tasks || []);
      setTotalTasks(res.total || 0);
      if (res.tasks && res.tasks.length > 0 && !selectedTaskId) {
        setSelectedTaskId(res.tasks[0].id);
      }
    } catch (err: any) {
      showNotify('error', `Failed to load agent tasks: ${err.message}`);
    } finally {
      setLoadingTasks(false);
    }
  }, [selectedTaskId]);

  // Fetch Single Task Details
  const fetchTaskDetail = useCallback(async (taskId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await apiClient.getAgentTask(taskId);
      setSelectedTaskDetail(detail);
    } catch (err: any) {
      showNotify('error', `Failed to load task details: ${err.message}`);
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
    fetchTasks();
  }, [fetchRegistry, fetchTasks]);

  useEffect(() => {
    if (selectedTaskId) {
      fetchTaskDetail(selectedTaskId);
    }
  }, [selectedTaskId, fetchTaskDetail]);

  // Handle Plan Decomposition Preview
  const handlePreviewDecomposition = async () => {
    if (!taskTitle.trim()) {
      showNotify('error', 'Please enter a task title first.');
      return;
    }
    setPlanningInProgress(true);
    try {
      const plan = await apiClient.decomposeAgentTask(taskTitle, taskDescription);
      setDecompositionPlan(plan);
      showNotify('success', `Planner generated ${plan.subtasks.length} subtask steps.`);
    } catch (err: any) {
      showNotify('error', `Decomposition failed: ${err.message}`);
    } finally {
      setPlanningInProgress(false);
    }
  };

  // Handle Create Task
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;

    setCreatingTask(true);
    try {
      const created = await apiClient.createAgentTask({
        title: taskTitle,
        description: taskDescription,
        agent_type: agentType,
        priority,
        auto_decompose: autoDecompose,
      });

      showNotify('success', `Agent task created successfully: "${created.title}"`);
      setTaskTitle('');
      setTaskDescription('');
      setDecompositionPlan(null);
      await fetchTasks();
      setSelectedTaskId(created.id);
    } catch (err: any) {
      showNotify('error', `Failed to create task: ${err.message}`);
    } finally {
      setCreatingTask(false);
    }
  };

  // Execute Task
  const handleExecuteTask = async (taskId: string) => {
    setActionInProgress(true);
    try {
      const updated = await apiClient.executeAgentTask(taskId);
      showNotify('success', `Task execution completed: Status ${updated.status}`);
      await fetchTasks();
      if (selectedTaskId === taskId) {
        await fetchTaskDetail(taskId);
      }
    } catch (err: any) {
      showNotify('error', `Task execution failed: ${err.message}`);
    } finally {
      setActionInProgress(false);
    }
  };

  // Cancel Task
  const handleCancelTask = async (taskId: string) => {
    setActionInProgress(true);
    try {
      await apiClient.cancelAgentTask(taskId);
      showNotify('success', 'Task cancellation signal dispatched.');
      await fetchTasks();
      if (selectedTaskId === taskId) {
        await fetchTaskDetail(taskId);
      }
    } catch (err: any) {
      showNotify('error', `Failed to cancel task: ${err.message}`);
    } finally {
      setActionInProgress(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-zinc-100 p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Agent Control Center</h1>
              <p className="text-sm text-zinc-400">
                Autonomous multi-agent orchestration, bounded decomposition, and execution traces.
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls & Tabs */}
        <div className="flex items-center gap-3">
          <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('orchestrator')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'orchestrator'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Orchestrator
            </button>
            <button
              onClick={() => setActiveTab('registry')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'registry'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Registry ({registry.length})
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'tasks'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Telemetry ({totalTasks})
            </button>
          </div>

          <button
            onClick={() => {
              fetchRegistry();
              fetchTasks();
              if (selectedTaskId) fetchTaskDetail(selectedTaskId);
            }}
            className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-all"
            title="Refresh Agents"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div
          className={`p-4 rounded-xl border text-sm flex items-center gap-3 transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 shrink-0" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 1: Orchestrator & Task Pipeline                                   */}
      {/* ===================================================================== */}
      {activeTab === 'orchestrator' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Task Creator & Planner Decomposition */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-5">
              <div className="flex items-center gap-2 border-b border-zinc-800/80 pb-3">
                <PlusCircle className="w-5 h-5 text-indigo-400" />
                <h2 className="font-semibold text-zinc-200">Dispatch Autonomous Task</h2>
              </div>

              <form onSubmit={handleCreateTask} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Task Goal / Title</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Audit API authentication and refactor session cookies"
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-sm focus:outline-none focus:border-indigo-500 transition-all placeholder:text-zinc-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Detailed Context / Scope</label>
                  <textarea
                    rows={3}
                    placeholder="Provide specific guidelines, file boundaries, or test expectations..."
                    value={taskDescription}
                    onChange={(e) => setTaskDescription(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-sm focus:outline-none focus:border-indigo-500 transition-all placeholder:text-zinc-600"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Specialized Agent</label>
                    <select
                      value={agentType}
                      onChange={(e) => setAgentType(e.target.value as AgentType)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-xs focus:outline-none focus:border-indigo-500"
                    >
                      <option value="GENERAL_TASK">General Agent</option>
                      <option value="RESEARCH">Research Agent</option>
                      <option value="CODING">Coding Agent</option>
                      <option value="ANALYSIS">Analysis Agent</option>
                      <option value="WRITING">Writing Agent</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Priority</label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as TaskPriority)}
                      className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-xs focus:outline-none focus:border-indigo-500"
                    >
                      <option value="LOW">Low</option>
                      <option value="NORMAL">Normal</option>
                      <option value="HIGH">High</option>
                      <option value="CRITICAL">Critical</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-zinc-950 border border-zinc-800/80 rounded-xl text-xs">
                  <div className="space-y-0.5">
                    <span className="font-medium text-zinc-300">Planner Decomposition</span>
                    <p className="text-zinc-500 text-[11px]">Break goal into bounded subtasks automatically</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={autoDecompose}
                    onChange={(e) => setAutoDecompose(e.target.checked)}
                    className="rounded bg-zinc-900 border-zinc-700 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={handlePreviewDecomposition}
                    disabled={planningInProgress || !taskTitle.trim()}
                    className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-300 text-xs font-medium rounded-xl border border-zinc-700 flex items-center justify-center gap-1.5 transition-all"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    {planningInProgress ? 'Decomposing...' : 'Preview Plan'}
                  </button>

                  <button
                    type="submit"
                    disabled={creatingTask || !taskTitle.trim()}
                    className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-md shadow-indigo-600/20"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    {creatingTask ? 'Queueing...' : 'Dispatch Task'}
                  </button>
                </div>
              </form>
            </div>

            {/* Decomposition Plan Preview Card */}
            {decompositionPlan && (
              <div className="bg-zinc-900/40 border border-indigo-500/20 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ListOrdered className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
                      Decomposition Strategy: {decompositionPlan.strategy}
                    </h3>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300">
                    {decompositionPlan.subtasks.length} steps
                  </span>
                </div>

                <div className="space-y-2">
                  {decompositionPlan.subtasks.map((step) => {
                    const meta = AGENT_META[step.agent_type] || AGENT_META.GENERAL_TASK;
                    const Icon = meta.icon;
                    return (
                      <div
                        key={step.order}
                        className="p-3 bg-zinc-950/80 border border-zinc-800 rounded-xl flex items-start gap-3"
                      >
                        <div className="w-5 h-5 rounded-full bg-zinc-800 text-zinc-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                          {step.order}
                        </div>
                        <div className="flex-1 min-w-0 space-y-1">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-medium text-zinc-200 truncate">{step.title}</h4>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${meta.color} flex items-center gap-1`}>
                              <Icon className="w-3 h-3" />
                              {step.agent_type}
                            </span>
                          </div>
                          <p className="text-[11px] text-zinc-400">{step.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Active Task Telemetry & Execution Traces */}
          <div className="lg:col-span-7 space-y-6">
            {/* Quick Task Selector */}
            <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-4 flex items-center justify-between gap-4 overflow-x-auto">
              <div className="flex items-center gap-2 shrink-0">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-medium text-zinc-300">Active Task:</span>
              </div>
              <select
                value={selectedTaskId || ''}
                onChange={(e) => setSelectedTaskId(e.target.value)}
                className="flex-1 max-w-md px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs text-zinc-300 focus:outline-none focus:border-indigo-500"
              >
                {tasks.length === 0 && <option value="">No agent tasks found</option>}
                {tasks.map((t) => (
                  <option key={t.id} value={t.id}>
                    [{t.status}] {t.title} ({t.agent_type})
                  </option>
                ))}
              </select>

              {selectedTaskId && (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleExecuteTask(selectedTaskId)}
                    disabled={actionInProgress}
                    className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    Execute
                  </button>
                  <button
                    onClick={() => handleCancelTask(selectedTaskId)}
                    disabled={actionInProgress}
                    className="px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/30 text-rose-400 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all"
                  >
                    <XCircle className="w-3 h-3" />
                    Cancel
                  </button>
                </div>
              )}
            </div>

            {/* Task Detail Card */}
            {selectedTaskDetail ? (
              <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-6">
                {/* Header info */}
                <div className="space-y-3 border-b border-zinc-800/80 pb-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-zinc-100">{selectedTaskDetail.title}</h3>
                      <p className="text-xs text-zinc-400 mt-1">{selectedTaskDetail.description || 'No description provided.'}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
                          STATUS_BADGES[selectedTaskDetail.status]?.bg || 'bg-zinc-800 text-zinc-400'
                        }`}
                      >
                        {STATUS_BADGES[selectedTaskDetail.status]?.label || selectedTaskDetail.status}
                      </span>
                    </div>
                  </div>

                  {/* Metrics Bar */}
                  <div className="grid grid-cols-4 gap-3 pt-2 text-xs">
                    <div className="p-2.5 bg-zinc-950 border border-zinc-800/80 rounded-xl">
                      <span className="text-[11px] text-zinc-500 block">Agent Type</span>
                      <span className="font-semibold text-zinc-200">{selectedTaskDetail.agent_type}</span>
                    </div>
                    <div className="p-2.5 bg-zinc-950 border border-zinc-800/80 rounded-xl">
                      <span className="text-[11px] text-zinc-500 block">Steps Executed</span>
                      <span className="font-semibold text-zinc-200">
                        {selectedTaskDetail.steps_executed} / {selectedTaskDetail.budget?.max_steps || 10}
                      </span>
                    </div>
                    <div className="p-2.5 bg-zinc-950 border border-zinc-800/80 rounded-xl">
                      <span className="text-[11px] text-zinc-500 block">Tokens Allocated</span>
                      <span className="font-semibold text-zinc-200">
                        {selectedTaskDetail.tokens_used} / {selectedTaskDetail.budget?.max_tokens || 4000}
                      </span>
                    </div>
                    <div className="p-2.5 bg-zinc-950 border border-zinc-800/80 rounded-xl">
                      <span className="text-[11px] text-zinc-500 block">Priority</span>
                      <span className="font-semibold text-indigo-400">{selectedTaskDetail.priority}</span>
                    </div>
                  </div>
                </div>

                {/* Sensitive Confirmation Warning */}
                {selectedTaskDetail.requires_confirmation && (
                  <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs space-y-2">
                    <div className="flex items-center gap-2 text-amber-400 font-semibold">
                      <ShieldAlert className="w-4 h-4" />
                      <span>Action Confirmation Challenge Required</span>
                    </div>
                    <p className="text-amber-200/80">
                      {selectedTaskDetail.confirmation_reason ||
                        'This autonomous step involves external mutations or sensitive tool execution.'}
                    </p>
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleExecuteTask(selectedTaskDetail.id)}
                        className="px-3 py-1.5 bg-amber-500 text-zinc-950 font-bold rounded-lg hover:bg-amber-400 transition-all"
                      >
                        Authorize & Proceed
                      </button>
                      <button
                        onClick={() => handleCancelTask(selectedTaskDetail.id)}
                        className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg transition-all"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                )}

                {/* Result Summary Output */}
                {selectedTaskDetail.result_summary && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                        Outcome Summary
                      </h4>
                    </div>
                    <div className="p-4 bg-zinc-950 border border-zinc-800/80 rounded-xl text-xs font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed">
                      {selectedTaskDetail.result_summary}
                    </div>
                  </div>
                )}

                {/* Subtasks Progression (if decomposed) */}
                {selectedTaskDetail.subtasks && selectedTaskDetail.subtasks.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4 text-indigo-400" />
                        <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                          Pipeline Subtasks ({selectedTaskDetail.subtasks.length})
                        </h4>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {selectedTaskDetail.subtasks.map((sub, idx) => (
                        <div
                          key={sub.id}
                          onClick={() => setSelectedTaskId(sub.id)}
                          className="p-3 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-xl flex items-center justify-between cursor-pointer transition-all"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold text-zinc-500">#{idx + 1}</span>
                            <div>
                              <p className="text-xs font-medium text-zinc-200">{sub.title}</p>
                              <span className="text-[10px] text-zinc-500">{sub.agent_type}</span>
                            </div>
                          </div>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full border ${
                              STATUS_BADGES[sub.status]?.bg || 'bg-zinc-800 text-zinc-400'
                            }`}
                          >
                            {sub.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Execution Traces Stream */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-cyan-400" />
                      <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                        Execution Step Traces ({selectedTaskDetail.traces?.length || 0})
                      </h4>
                    </div>
                  </div>

                  {(!selectedTaskDetail.traces || selectedTaskDetail.traces.length === 0) ? (
                    <div className="p-6 bg-zinc-950/60 border border-zinc-800/80 rounded-xl text-center text-xs text-zinc-500">
                      No step traces recorded yet. Execute the task to generate execution telemetry.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                      {selectedTaskDetail.traces.map((tr) => (
                        <div
                          key={tr.id}
                          className="p-3 bg-zinc-950 border border-zinc-800 rounded-xl space-y-1.5 text-xs font-mono"
                        >
                          <div className="flex items-center justify-between text-[11px]">
                            <div className="flex items-center gap-2">
                              <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-bold">
                                Step {tr.step_index}
                              </span>
                              <span className="text-indigo-400">{tr.action}</span>
                            </div>
                            <div className="flex items-center gap-3 text-zinc-500 text-[10px]">
                              <span>{tr.duration_ms}ms</span>
                              <span
                                className={
                                  tr.status === 'SUCCEEDED'
                                    ? 'text-emerald-400'
                                    : tr.status === 'RUNNING'
                                    ? 'text-cyan-400'
                                    : 'text-rose-400'
                                }
                              >
                                {tr.status}
                              </span>
                            </div>
                          </div>
                          {tr.output_summary && (
                            <p className="text-zinc-400 text-[11px] font-sans pt-1 border-t border-zinc-900">
                              {tr.output_summary}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-12 text-center text-zinc-500 text-sm">
                Select or dispatch an agent task to inspect execution traces and telemetry.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: Agent Registry Overview                                        */}
      {/* ===================================================================== */}
      {activeTab === 'registry' && (
        <div className="space-y-6">
          <div className="border-b border-zinc-800 pb-4">
            <h2 className="text-lg font-semibold text-zinc-200">Specialized Agent Registry</h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              5 domain-tailored agents with bounded token and execution step budgets.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {registry.map((item) => {
              const meta = AGENT_META[item.agent_type] || AGENT_META.GENERAL_TASK;
              const Icon = meta.icon;
              return (
                <div
                  key={item.name}
                  className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 rounded-2xl p-6 space-y-4 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-3 rounded-xl border ${meta.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-mono">
                      {item.agent_type}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-bold text-base text-zinc-100">{item.name}</h3>
                    <p className="text-xs text-zinc-400 mt-1">{item.description}</p>
                  </div>

                  <div className="space-y-2 pt-2 border-t border-zinc-800/80 text-xs">
                    <span className="text-zinc-500 font-medium text-[11px] block">Core Capabilities:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {item.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-300 text-[11px]"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-zinc-800/80 text-[11px]">
                    <div className="p-2 bg-zinc-950 rounded-lg text-center">
                      <span className="text-zinc-500 block text-[10px]">Max Steps</span>
                      <span className="font-semibold text-zinc-300">{item.default_budget.max_steps}</span>
                    </div>
                    <div className="p-2 bg-zinc-950 rounded-lg text-center">
                      <span className="text-zinc-500 block text-[10px]">Max Tokens</span>
                      <span className="font-semibold text-zinc-300">{item.default_budget.max_tokens}</span>
                    </div>
                    <div className="p-2 bg-zinc-950 rounded-lg text-center">
                      <span className="text-zinc-500 block text-[10px]">Timeout</span>
                      <span className="font-semibold text-zinc-300">{item.default_budget.timeout_seconds}s</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 3: Telemetry & Task History                                       */}
      {/* ===================================================================== */}
      {activeTab === 'tasks' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
            <div>
              <h2 className="text-lg font-semibold text-zinc-200">Execution Telemetry & Audit Log</h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                Every agent action, step trace, and state transition is cryptographically audited and user-isolated.
              </p>
            </div>
            <span className="text-xs text-zinc-400 font-mono">Total Tasks: {totalTasks}</span>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-950/80 border-b border-zinc-800 text-zinc-400 font-medium">
                  <tr>
                    <th className="p-4">Task Title</th>
                    <th className="p-4">Agent</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Priority</th>
                    <th className="p-4">Steps / Tokens</th>
                    <th className="p-4">Created</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/80">
                  {tasks.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-zinc-500">
                        No agent tasks recorded. Create a task in the Orchestrator tab.
                      </td>
                    </tr>
                  ) : (
                    tasks.map((t) => (
                      <tr key={t.id} className="hover:bg-zinc-800/30 transition-all">
                        <td className="p-4 font-medium text-zinc-200 max-w-xs truncate">{t.title}</td>
                        <td className="p-4 font-mono text-[11px] text-zinc-400">{t.agent_type}</td>
                        <td className="p-4">
                          <span
                            className={`px-2 py-0.5 rounded-full border text-[10px] font-medium ${
                              STATUS_BADGES[t.status]?.bg || 'bg-zinc-800 text-zinc-400'
                            }`}
                          >
                            {t.status}
                          </span>
                        </td>
                        <td className="p-4 font-medium text-indigo-400">{t.priority}</td>
                        <td className="p-4 font-mono text-zinc-400 text-[11px]">
                          {t.steps_executed} steps | {t.tokens_used} tok
                        </td>
                        <td className="p-4 text-zinc-500 text-[11px]">
                          {new Date(t.created_at).toLocaleTimeString()}
                        </td>
                        <td className="p-4 text-right">
                          <button
                            onClick={() => {
                              setSelectedTaskId(t.id);
                              setActiveTab('orchestrator');
                            }}
                            className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-[11px] font-medium transition-all"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
