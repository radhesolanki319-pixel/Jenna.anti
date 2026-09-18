'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldAlert,
  FolderTree,
  Terminal,
  Calculator,
  Globe,
  Cpu,
  Boxes,
  PlusCircle,
  FileText,
  Clock,
  Sparkles,
  Link2,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type {
  ToolDefinition,
  ToolCategory,
  ToolExecutionResult,
  ResearchResponse,
  MCPServerInfo,
} from '@jenna/types';

const CATEGORY_META: Record<ToolCategory, { label: string; icon: React.ElementType; color: string }> = {
  CALCULATOR: { label: 'Calculator', icon: Calculator, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  FILESYSTEM: { label: 'Filesystem', icon: FolderTree, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  WEB: { label: 'Web Research', icon: Globe, color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
  SYSTEM: { label: 'System Telemetry', icon: Cpu, color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
  MCP: { label: 'MCP Protocol', icon: Boxes, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
  GENERAL: { label: 'General', icon: Wrench, color: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30' },
};

export default function ToolsPage() {
  const [activeTab, setActiveTab] = useState<'catalog' | 'playground' | 'research' | 'mcp'>('catalog');

  // Tools catalog state
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<ToolCategory | 'ALL'>('ALL');
  const [loadingTools, setLoadingTools] = useState(false);

  // Playground execution state
  const [selectedToolName, setSelectedToolName] = useState<string>('calculator');
  const [paramValues, setParamValues] = useState<Record<string, any>>({ expression: 'sqrt(144) + 10 * 5' });
  const [executionResult, setExecutionResult] = useState<ToolExecutionResult | null>(null);
  const [executing, setExecuting] = useState(false);
  const [confirmSensitive, setConfirmSensitive] = useState(false);

  // Web Research Studio state
  const [researchQuery, setResearchQuery] = useState('');
  const [maxSources, setMaxSources] = useState(3);
  const [researchResult, setResearchResult] = useState<ResearchResponse | null>(null);
  const [researching, setResearching] = useState(false);

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState<MCPServerInfo[]>([]);
  const [loadingMcp, setLoadingMcp] = useState(false);
  const [mcpServerName, setMcpServerName] = useState('ProductionWeatherServer');
  const [connectingMcp, setConnectingMcp] = useState(false);

  // Notification banner
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotify = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // Fetch Tools
  const fetchTools = useCallback(async () => {
    setLoadingTools(true);
    try {
      const items = await apiClient.listTools();
      setTools(items);
    } catch (err: any) {
      showNotify('error', `Failed to load tools: ${err.message}`);
    } finally {
      setLoadingTools(false);
    }
  }, []);

  // Fetch MCP Servers
  const fetchMcpServers = useCallback(async () => {
    setLoadingMcp(true);
    try {
      const servers = await apiClient.listMcpServers();
      setMcpServers(servers);
    } catch (err: any) {
      showNotify('error', `Failed to load MCP servers: ${err.message}`);
    } finally {
      setLoadingMcp(false);
    }
  }, []);

  useEffect(() => {
    fetchTools();
    fetchMcpServers();
  }, [fetchTools, fetchMcpServers]);

  // When selected tool changes in playground, init parameters
  const activeToolDef = tools.find((t) => t.name === selectedToolName);
  useEffect(() => {
    if (activeToolDef) {
      const initial: Record<string, any> = {};
      activeToolDef.parameters.forEach((p) => {
        if (p.default !== undefined && p.default !== null) {
          initial[p.name] = p.default;
        } else if (p.name === 'expression') {
          initial[p.name] = 'sqrt(144) + 10 * 5';
        } else if (p.name === 'path') {
          initial[p.name] = '.';
        } else if (p.name === 'query') {
          initial[p.name] = 'model context protocol';
        } else {
          initial[p.name] = '';
        }
      });
      setParamValues(initial);
      setExecutionResult(null);
      setConfirmSensitive(false);
    }
  }, [selectedToolName, tools]);

  // Execute Tool Call
  const handleExecuteTool = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedToolName) return;

    setExecuting(true);
    try {
      const res = await apiClient.executeTool(selectedToolName, paramValues, confirmSensitive);
      setExecutionResult(res);
      if (res.success) {
        showNotify('success', `Tool '${res.tool_name}' executed in ${res.execution_time_ms}ms`);
      } else if (res.requires_confirmation) {
        showNotify('error', `Confirmation required: ${res.confirmation_reason}`);
      } else {
        showNotify('error', `Tool error: ${res.error}`);
      }
    } catch (err: any) {
      showNotify('error', `Execution failed: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  // Perform Web Research
  const handlePerformResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!researchQuery.trim()) return;

    setResearching(true);
    try {
      const res = await apiClient.performResearch(researchQuery, maxSources);
      setResearchResult(res);
      showNotify('success', `Synthesized ${res.citations.length} verified sources in ${res.execution_time_ms}ms`);
    } catch (err: any) {
      showNotify('error', `Research failed: ${err.message}`);
    } finally {
      setResearching(false);
    }
  };

  // Connect MCP Server
  const handleConnectMcp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mcpServerName.trim()) return;

    setConnectingMcp(true);
    try {
      const res = await apiClient.connectMcpServer(mcpServerName, 'mock');
      showNotify('success', `Connected to MCP server '${res.server_name}'. Registered ${res.tools_registered} tools.`);
      await fetchMcpServers();
      await fetchTools();
      setMcpServerName('');
    } catch (err: any) {
      showNotify('error', `MCP Connection failed: ${err.message}`);
    } finally {
      setConnectingMcp(false);
    }
  };

  // Filtered tools catalog
  const filteredTools = selectedCategory === 'ALL'
    ? tools
    : tools.filter((t) => t.category === selectedCategory);

  return (
    <div className="min-h-screen bg-[#0d1117] text-zinc-100 p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-violet-500/10 border border-violet-500/30 rounded-xl text-violet-400">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Tools & MCP Platform</h1>
              <p className="text-sm text-zinc-400">
                Extensible platform tools, Model Context Protocol integration, and verified web research.
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls & Tabs */}
        <div className="flex items-center gap-3">
          <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('catalog')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'catalog'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Catalog ({tools.length})
            </button>
            <button
              onClick={() => setActiveTab('playground')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'playground'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Playground
            </button>
            <button
              onClick={() => setActiveTab('research')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'research'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Web Research
            </button>
            <button
              onClick={() => setActiveTab('mcp')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'mcp'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              MCP Servers ({mcpServers.length})
            </button>
          </div>

          <button
            onClick={() => {
              fetchTools();
              fetchMcpServers();
            }}
            className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-all"
            title="Refresh Tools"
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
      {/* TAB 1: Tool Catalog                                                  */}
      {/* ===================================================================== */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          {/* Category Filter Bar */}
          <div className="flex flex-wrap gap-2 pb-2">
            {(['ALL', 'CALCULATOR', 'FILESYSTEM', 'WEB', 'SYSTEM', 'MCP'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                  selectedCategory === cat
                    ? 'bg-violet-600 text-white border-violet-500 shadow-sm'
                    : 'bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:border-zinc-700'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Tools Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTools.map((tool) => {
              const meta = CATEGORY_META[tool.category] || CATEGORY_META.GENERAL;
              const Icon = meta.icon;
              return (
                <div
                  key={tool.name}
                  className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 rounded-2xl p-6 space-y-4 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className={`p-2.5 rounded-xl border ${meta.color}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex items-center gap-1.5">
                        {tool.is_sensitive && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                            <ShieldAlert className="w-3 h-3" />
                            Sensitive
                          </span>
                        )}
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-mono">
                          {tool.category}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-bold text-base text-zinc-100 font-mono">{tool.name}</h3>
                      <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{tool.description}</p>
                    </div>

                    {/* Parameters summary */}
                    <div className="space-y-1.5 pt-2 border-t border-zinc-800/80 text-xs">
                      <span className="text-zinc-500 font-medium text-[11px] block">
                        Parameters ({tool.parameters.length}):
                      </span>
                      {tool.parameters.length === 0 ? (
                        <span className="text-zinc-600 text-[11px] italic">No arguments required</span>
                      ) : (
                        <div className="space-y-1">
                          {tool.parameters.map((p) => (
                            <div key={p.name} className="flex items-center justify-between text-[11px]">
                              <span className="font-mono text-zinc-300">
                                {p.name} {p.required && <span className="text-rose-400">*</span>}
                              </span>
                              <span className="text-zinc-500 font-mono text-[10px]">{p.type}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between">
                    <span className="text-[11px] text-zinc-500">Timeout: {tool.timeout_seconds}s</span>
                    <button
                      onClick={() => {
                        setSelectedToolName(tool.name);
                        setActiveTab('playground');
                      }}
                      className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium rounded-xl border border-zinc-700 transition-all flex items-center gap-1.5"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      Try Tool
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: Interactive Tool Playground                                    */}
      {/* ===================================================================== */}
      {activeTab === 'playground' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Tool Selector & Parameter Input Form */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Play className="w-5 h-5 text-violet-400" />
                  <h2 className="font-semibold text-zinc-200">Invoke Tool</h2>
                </div>
              </div>

              <form onSubmit={handleExecuteTool} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Select Tool</label>
                  <select
                    value={selectedToolName}
                    onChange={(e) => setSelectedToolName(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs font-mono text-zinc-200 focus:outline-none focus:border-violet-500"
                  >
                    {tools.map((t) => (
                      <option key={t.name} value={t.name}>
                        [{t.category}] {t.name}
                      </option>
                    ))}
                  </select>
                </div>

                {activeToolDef && (
                  <p className="text-xs text-zinc-400 p-3 bg-zinc-950 border border-zinc-800 rounded-xl">
                    {activeToolDef.description}
                  </p>
                )}

                {/* Parameters Form */}
                {activeToolDef && activeToolDef.parameters.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block">
                      Arguments
                    </span>
                    {activeToolDef.parameters.map((param) => (
                      <div key={param.name}>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-xs font-mono text-zinc-300">
                            {param.name} {param.required && <span className="text-rose-400">*</span>}
                          </label>
                          <span className="text-[10px] text-zinc-500 font-mono">{param.type}</span>
                        </div>
                        {param.type === 'boolean' ? (
                          <input
                            type="checkbox"
                            checked={Boolean(paramValues[param.name])}
                            onChange={(e) =>
                              setParamValues({ ...paramValues, [param.name]: e.target.checked })
                            }
                            className="rounded bg-zinc-950 border-zinc-800 text-violet-600 focus:ring-violet-500 w-4 h-4 cursor-pointer"
                          />
                        ) : (
                          <input
                            type={param.type === 'integer' || param.type === 'number' ? 'number' : 'text'}
                            value={paramValues[param.name] ?? ''}
                            required={param.required}
                            placeholder={param.description}
                            onChange={(e) => {
                              const val =
                                param.type === 'integer'
                                  ? parseInt(e.target.value, 10) || 0
                                  : param.type === 'number'
                                  ? parseFloat(e.target.value) || 0
                                  : e.target.value;
                              setParamValues({ ...paramValues, [param.name]: val });
                            }}
                            className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-xs font-mono focus:outline-none focus:border-violet-500"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Sensitive Action Confirmation Toggle */}
                {activeToolDef?.is_sensitive && (
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
                      <ShieldAlert className="w-4 h-4" />
                      <span>3-Tier Authorization Challenge</span>
                    </div>
                    <p className="text-[11px] text-amber-200/80">
                      This is a sensitive mutating tool. Check the box to authorize execution.
                    </p>
                    <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer pt-1">
                      <input
                        type="checkbox"
                        checked={confirmSensitive}
                        onChange={(e) => setConfirmSensitive(e.target.checked)}
                        className="rounded bg-zinc-900 border-zinc-700 text-amber-500 focus:ring-amber-500 w-4 h-4"
                      />
                      <span className="font-medium">Explicitly Confirm Action</span>
                    </label>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={executing}
                  className="w-full px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-xs font-medium rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-md shadow-violet-600/20"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  {executing ? 'Executing...' : 'Run Tool'}
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Structured Output & Inspection */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-5 min-h-[420px] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
                  <h3 className="font-semibold text-zinc-200">Execution Output & Telemetry</h3>
                  {executionResult && (
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono text-zinc-500">
                        {executionResult.execution_time_ms}ms
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                          executionResult.success
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : executionResult.requires_confirmation
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}
                      >
                        {executionResult.success
                          ? 'SUCCESS'
                          : executionResult.requires_confirmation
                          ? 'REQUIRES CONFIRMATION'
                          : 'FAILED'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Output Display */}
                <div className="pt-4">
                  {executionResult ? (
                    <div className="space-y-4">
                      {executionResult.requires_confirmation && (
                        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs space-y-2">
                          <span className="font-semibold text-amber-400">Confirmation Block:</span>
                          <p className="text-amber-200">{executionResult.confirmation_reason}</p>
                          <p className="text-[11px] text-zinc-400">
                            Check 'Explicitly Confirm Action' and resubmit.
                          </p>
                        </div>
                      )}

                      {executionResult.error && (
                        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs font-mono text-rose-300">
                          {executionResult.error}
                        </div>
                      )}

                      {executionResult.data !== undefined && (
                        <pre className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl text-xs font-mono text-zinc-300 overflow-x-auto max-h-96">
                          {typeof executionResult.data === 'string'
                            ? executionResult.data
                            : JSON.stringify(executionResult.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  ) : (
                    <div className="p-16 text-center text-zinc-500 text-xs">
                      Select a tool and invoke execution to view output data and telemetry.
                    </div>
                  )}
                </div>
              </div>

              {/* Untrusted defense footer note */}
              <div className="text-[11px] text-zinc-600 border-t border-zinc-800/80 pt-3 flex items-center justify-between">
                <span>Security: Output wrapped in &lt;tool_output&gt; defensive boundary</span>
                <span>Audit: Execution logged in audit_events</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 3: Web Research Studio                                            */}
      {/* ===================================================================== */}
      {activeTab === 'research' && (
        <div className="space-y-6">
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
              <Globe className="w-5 h-5 text-blue-400" />
              <h2 className="font-semibold text-zinc-200">Citation-Aware Web Research</h2>
            </div>
            <p className="text-xs text-zinc-400">
              Multi-source synthesis: searches verified sources, cross-references findings, and produces strictly numbered citations.
            </p>

            <form onSubmit={handlePerformResearch} className="flex gap-3 pt-2">
              <input
                type="text"
                required
                placeholder="Enter research topic (e.g. 'FastAPI asyncpg connection pooling' or 'Model Context Protocol')..."
                value={researchQuery}
                onChange={(e) => setResearchQuery(e.target.value)}
                className="flex-1 px-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs focus:outline-none focus:border-blue-500 placeholder:text-zinc-600"
              />
              <select
                value={maxSources}
                onChange={(e) => setMaxSources(parseInt(e.target.value, 10))}
                className="px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-xs text-zinc-300"
              >
                <option value={2}>2 Sources</option>
                <option value={4}>4 Sources</option>
                <option value={6}>6 Sources</option>
              </select>
              <button
                type="submit"
                disabled={researching || !researchQuery.trim()}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium rounded-xl flex items-center gap-2 transition-all shadow-md shadow-blue-600/20"
              >
                <Search className="w-4 h-4" />
                {researching ? 'Researching...' : 'Synthesize'}
              </button>
            </form>
          </div>

          {/* Research Outcome Card */}
          {researchResult && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Synthesized Findings */}
              <div className="lg:col-span-7 bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <h3 className="font-semibold text-zinc-200 text-sm">Synthesized Findings</h3>
                  </div>
                  <span className="text-[11px] text-zinc-500 font-mono">
                    Completed in {researchResult.execution_time_ms}ms
                  </span>
                </div>
                <div className="p-4 bg-zinc-950 border border-zinc-800 rounded-xl text-xs text-zinc-300 whitespace-pre-wrap font-sans leading-relaxed">
                  {researchResult.synthesis}
                </div>
              </div>

              {/* Right Column: Verified Citations */}
              <div className="lg:col-span-5 bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Link2 className="w-4 h-4 text-blue-400" />
                    <h3 className="font-semibold text-zinc-200 text-sm">
                      Verified Sources ({researchResult.citations.length})
                    </h3>
                  </div>
                </div>

                <div className="space-y-3">
                  {researchResult.citations.map((c) => (
                    <div
                      key={c.index}
                      className="p-3 bg-zinc-950 border border-zinc-800 rounded-xl space-y-1 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[10px] font-bold">
                          [{c.index}]
                        </span>
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-zinc-500 hover:text-blue-400 flex items-center gap-1 text-[11px] transition-all"
                        >
                          Visit <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <h4 className="font-medium text-zinc-200 text-xs pt-1">{c.title}</h4>
                      <p className="text-[11px] text-zinc-400 leading-normal">{c.snippet}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 4: MCP Server Management                                          */}
      {/* ===================================================================== */}
      {activeTab === 'mcp' && (
        <div className="space-y-6">
          {/* Header & Connect Box */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Boxes className="w-5 h-5 text-cyan-400" />
                <div>
                  <h2 className="font-semibold text-zinc-200">Model Context Protocol (MCP) Connections</h2>
                  <p className="text-xs text-zinc-400">
                    Connect external tool providers adhering to official JSON-RPC 2.0 specifications.
                  </p>
                </div>
              </div>
            </div>

            <form onSubmit={handleConnectMcp} className="flex gap-3 pt-2">
              <input
                type="text"
                required
                placeholder="MCP Server Instance Name (e.g. BraveSearchMCP or SQLiteMCP)..."
                value={mcpServerName}
                onChange={(e) => setMcpServerName(e.target.value)}
                className="flex-1 px-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs font-mono focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                disabled={connectingMcp || !mcpServerName.trim()}
                className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium rounded-xl flex items-center gap-2 transition-all shadow-md shadow-cyan-600/20"
              >
                <PlusCircle className="w-4 h-4" />
                {connectingMcp ? 'Connecting...' : 'Connect Server'}
              </button>
            </form>
          </div>

          {/* Active Servers Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {mcpServers.length === 0 ? (
              <div className="col-span-2 bg-zinc-900/40 border border-zinc-800 rounded-2xl p-12 text-center text-zinc-500 text-xs">
                No active MCP servers connected. Connect an instance above to discover external tools.
              </div>
            ) : (
              mcpServers.map((srv) => (
                <div
                  key={srv.name}
                  className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-sm text-zinc-100 font-mono">{srv.name}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      Connected
                    </span>
                  </div>

                  <div className="text-xs space-y-1 text-zinc-400">
                    <p>Discovered Tools: <span className="text-zinc-200 font-semibold">{srv.tools_count}</span></p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {srv.tools.map((t) => (
                        <span key={t} className="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-cyan-300">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
