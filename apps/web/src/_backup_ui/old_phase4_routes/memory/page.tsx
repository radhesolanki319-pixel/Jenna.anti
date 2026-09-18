'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  Search,
  Plus,
  Trash2,
  Edit2,
  Sparkles,
  Clock,
  CheckCircle2,
  Layers,
  Database,
  Filter,
  Sliders,
  RefreshCw,
  AlertCircle,
  X,
  ChevronRight,
  Zap,
  Archive,
  ArchiveRestore,
  ThumbsUp,
  ThumbsDown,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  FileText,
  UserCheck,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type {
  MemoryRecord,
  MemoryType,
  MemoryStatus,
  MemoryCandidate,
  MemoryCreateInput,
  MemoryUpdateInput,
  MemorySearchResultItem,
  FeedbackType,
} from '@jenna/types';

const MEMORY_TYPES: { type: MemoryType; label: string; color: string }[] = [
  { type: 'FACT', label: 'Fact', color: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
  { type: 'PREFERENCE', label: 'Preference', color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
  { type: 'PERSONAL_CONTEXT', label: 'Personal Context', color: 'bg-purple-500/10 text-purple-500 border-purple-500/20' },
  { type: 'INSTRUCTION', label: 'Instruction', color: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
  { type: 'CONVERSATION_SUMMARY', label: 'Conv Summary', color: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20' },
  { type: 'TASK_CONTEXT', label: 'Task Context', color: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20' },
  { type: 'TEMPORARY', label: 'Temporary', color: 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20' },
];

export default function MemoryPage() {
  const [activeTab, setActiveTab] = useState<'active' | 'archived' | 'extractor' | 'working'>('active');

  // Memories list state
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [minImportance, setMinImportance] = useState<number>(0);
  const [isSemanticSearch, setIsSemanticSearch] = useState<boolean>(false);
  const [semanticResults, setSemanticResults] = useState<MemorySearchResultItem[] | null>(null);
  const [isSearchingSemantic, setIsSearchingSemantic] = useState<boolean>(false);

  // Working memory state
  const [workingMemory, setWorkingMemory] = useState<Record<string, any>>({});
  const [newWorkingKey, setNewWorkingKey] = useState<string>('');
  const [newWorkingVal, setNewWorkingVal] = useState<string>('');
  const [workingMemoryLoading, setWorkingMemoryLoading] = useState<boolean>(false);

  // Extraction Playground state
  const [extractInput, setExtractInput] = useState<string>('');
  const [extractCandidates, setExtractCandidates] = useState<MemoryCandidate[]>([]);
  const [isExtracting, setIsExtracting] = useState<boolean>(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [editingMemory, setEditingMemory] = useState<MemoryRecord | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [memoryToDelete, setMemoryToDelete] = useState<MemoryRecord | null>(null);

  // Form State
  const [formContent, setFormContent] = useState<string>('');
  const [formSummary, setFormSummary] = useState<string>('');
  const [formType, setFormType] = useState<MemoryType>('FACT');
  const [formImportance, setFormImportance] = useState<number>(0.5);
  const [formConfidence, setFormConfidence] = useState<number>(0.8);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Load memories
  const loadMemories = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const statusFilter = activeTab === 'active' ? 'ACTIVE' : activeTab === 'archived' ? 'ARCHIVED' : undefined;
      const res = await apiClient.listMemories({
        memory_type: selectedType === 'ALL' ? undefined : selectedType,
        status: statusFilter,
        search: searchQuery.trim() ? searchQuery.trim() : undefined,
        min_importance: minImportance > 0 ? minImportance : undefined,
      });
      setMemories(res.items);
      setTotalCount(res.total);
    } catch (err: any) {
      setError(err?.message || 'Failed to load memories.');
    } finally {
      setIsLoading(false);
    }
  }, [activeTab, selectedType, searchQuery, minImportance]);

  // Load working memory
  const loadWorkingMemory = useCallback(async () => {
    setWorkingMemoryLoading(true);
    try {
      const res = await apiClient.getWorkingMemory();
      setWorkingMemory(res.items || {});
    } catch (err: any) {
      setError(err?.message || 'Failed to load working memory.');
    } finally {
      setWorkingMemoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'working') {
      loadWorkingMemory();
    } else if (activeTab === 'active' || activeTab === 'archived') {
      loadMemories();
    }
  }, [activeTab, loadMemories, loadWorkingMemory]);

  const notifySuccess = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 4000);
  };

  // Semantic Search
  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSemanticResults(null);
      return;
    }

    setIsSearchingSemantic(true);
    setError(null);
    try {
      const res = await apiClient.searchMemories(
        searchQuery.trim(),
        5,
        0.35,
        selectedType === 'ALL' ? undefined : [selectedType],
      );
      setSemanticResults(res.results);
    } catch (err: any) {
      setError(err?.message || 'Semantic search failed.');
    } finally {
      setIsSearchingSemantic(false);
    }
  };

  // Feedback handler
  const handleFeedback = async (id: string, type: FeedbackType) => {
    try {
      await apiClient.feedbackMemory(id, type);
      notifySuccess(`Feedback '${type}' recorded.`);
      loadMemories();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit feedback.');
    }
  };

  // Archive / Restore handlers
  const handleArchive = async (id: string) => {
    try {
      await apiClient.archiveMemory(id);
      notifySuccess('Memory moved to archive.');
      loadMemories();
    } catch (err: any) {
      setError(err?.message || 'Failed to archive memory.');
    }
  };

  const handleRestore = async (id: string) => {
    try {
      await apiClient.restoreMemory(id);
      notifySuccess('Memory restored to active.');
      loadMemories();
    } catch (err: any) {
      setError(err?.message || 'Failed to restore memory.');
    }
  };

  // Candidate extraction in playground
  const handleExtractCandidates = async () => {
    if (!extractInput.trim()) return;
    setIsExtracting(true);
    setExtractError(null);
    try {
      const res = await apiClient.extractMemories(extractInput.trim());
      setExtractCandidates(res.candidates);
      if (res.candidates.length === 0) {
        setExtractError('No candidate memories identified in this input.');
      }
    } catch (err: any) {
      setExtractError(err?.message || 'Extraction failed.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleConfirmCandidate = async (candidate: MemoryCandidate, confirm: boolean) => {
    try {
      await apiClient.confirmMemory(candidate, confirm);
      notifySuccess(confirm ? 'Candidate confirmed and saved!' : 'Candidate dismissed.');
      setExtractCandidates((prev) => prev.filter((c) => c !== candidate));
      if (activeTab === 'active') {
        loadMemories();
      }
    } catch (err: any) {
      setExtractError(err?.message || 'Failed to confirm candidate.');
    }
  };

  // Create / Edit modal submit
  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formContent.trim()) return;

    setIsSubmitting(true);
    try {
      if (editingMemory) {
        await apiClient.updateMemory(editingMemory.id, {
          content: formContent.trim(),
          summary: formSummary.trim() || null,
          memory_type: formType,
          importance: formImportance,
          confidence: formConfidence,
        });
        notifySuccess('Memory updated successfully.');
      } else {
        await apiClient.createMemory({
          content: formContent.trim(),
          summary: formSummary.trim() || null,
          memory_type: formType,
          importance: formImportance,
          confidence: formConfidence,
        });
        notifySuccess('Memory created and embedded successfully.');
      }

      setIsCreateModalOpen(false);
      setEditingMemory(null);
      resetForm();
      loadMemories();
    } catch (err: any) {
      setError(err?.message || 'Failed to save memory.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormContent('');
    setFormSummary('');
    setFormType('FACT');
    setFormImportance(0.5);
    setFormConfidence(0.8);
  };

  const openEditModal = (mem: MemoryRecord) => {
    setEditingMemory(mem);
    setFormContent(mem.content);
    setFormSummary(mem.summary || '');
    setFormType(mem.memory_type);
    setFormImportance(mem.importance);
    setFormConfidence(mem.confidence);
    setIsCreateModalOpen(true);
  };

  // Delete memory
  const confirmDelete = async () => {
    if (!memoryToDelete) return;
    try {
      await apiClient.deleteMemory(memoryToDelete.id);
      notifySuccess('Memory deleted.');
      setIsDeleteModalOpen(false);
      setMemoryToDelete(null);
      loadMemories();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete memory.');
    }
  };

  // Working Memory Actions
  const handleSetWorkingMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkingKey.trim() || !newWorkingVal.trim()) return;

    try {
      await apiClient.setWorkingMemory(newWorkingKey.trim(), newWorkingVal.trim());
      setNewWorkingKey('');
      setNewWorkingVal('');
      loadWorkingMemory();
      notifySuccess('Working memory item saved.');
    } catch (err: any) {
      setError(err?.message || 'Failed to set working memory.');
    }
  };

  const handleClearWorkingMemory = async () => {
    try {
      await apiClient.clearWorkingMemory();
      loadWorkingMemory();
      notifySuccess('Working memory cleared.');
    } catch (err: any) {
      setError(err?.message || 'Failed to clear working memory.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Brain className="w-7 h-7 text-indigo-500" />
            Intelligent Memory Center
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
            Privacy-aware semantic vector memory, short-term context, and automated extraction pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (activeTab === 'working') loadWorkingMemory();
              else loadMemories();
            }}
            disabled={isLoading || workingMemoryLoading}
            className="p-2 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading || workingMemoryLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => {
              resetForm();
              setEditingMemory(null);
              setIsCreateModalOpen(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Add Memory
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-600 dark:text-emerald-400 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-b border-zinc-200 dark:border-zinc-800 gap-6 text-sm font-medium overflow-x-auto">
        <button
          onClick={() => {
            setActiveTab('active');
            setSemanticResults(null);
          }}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'active'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold'
              : 'border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <Database className="w-4 h-4" />
          Active Memories ({activeTab === 'active' ? totalCount : '...'})
        </button>
        <button
          onClick={() => {
            setActiveTab('archived');
            setSemanticResults(null);
          }}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'archived'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold'
              : 'border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <Archive className="w-4 h-4" />
          Archived Memories
        </button>
        <button
          onClick={() => setActiveTab('extractor')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'extractor'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold'
              : 'border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Extraction & Safety Playground
        </button>
        <button
          onClick={() => setActiveTab('working')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'working'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-semibold'
              : 'border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Short-Term Working Memory
        </button>
      </div>

      {/* TAB 1 & 2: Active or Archived Memories */}
      {(activeTab === 'active' || activeTab === 'archived') && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="p-4 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-4">
            <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
              {/* Search Box */}
              <form onSubmit={handleSemanticSearch} className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-400" />
                <input
                  type="text"
                  placeholder={
                    isSemanticSearch
                      ? 'Semantic concept search (e.g. "prefers dark UI and concise responses")...'
                      : 'Keyword search in memories...'
                  }
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-24 py-2 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  type="submit"
                  disabled={isSearchingSemantic || !searchQuery.trim()}
                  className="absolute right-1.5 top-1.5 px-3 py-1 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950 dark:hover:bg-indigo-900 text-indigo-600 dark:text-indigo-400 text-xs font-medium rounded-md transition-colors disabled:opacity-50"
                >
                  {isSearchingSemantic ? 'Searching...' : 'Search'}
                </button>
              </form>

              {/* Semantic Search Toggle */}
              <button
                type="button"
                onClick={() => {
                  const nextState = !isSemanticSearch;
                  setIsSemanticSearch(nextState);
                  if (!nextState) setSemanticResults(null);
                }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
                  isSemanticSearch
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Vector Semantic Mode</span>
              </button>
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-zinc-200 dark:border-zinc-800">
              <span className="text-xs text-zinc-400 flex items-center gap-1 mr-2">
                <Filter className="w-3.5 h-3.5" /> Type:
              </span>
              <button
                onClick={() => setSelectedType('ALL')}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedType === 'ALL'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200'
                }`}
              >
                All Types
              </button>
              {MEMORY_TYPES.map((t) => (
                <button
                  key={t.type}
                  onClick={() => setSelectedType(t.type)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                    selectedType === t.type
                      ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 border-transparent'
                      : `${t.color} hover:opacity-80`
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Semantic Search Notice */}
          {semanticResults && (
            <div className="flex items-center justify-between p-3 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/50 rounded-lg text-sm text-indigo-700 dark:text-indigo-300">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                <span>
                  Semantic Search matches for <strong>&quot;{searchQuery}&quot;</strong> (Compound relevance scored)
                </span>
              </div>
              <button
                onClick={() => {
                  setSemanticResults(null);
                  setSearchQuery('');
                }}
                className="text-xs hover:underline"
              >
                Clear Search Results
              </button>
            </div>
          )}

          {/* List of Memories */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-12 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900">
              <RefreshCw className="w-6 h-6 animate-spin text-indigo-500 mb-2" />
              <p className="text-sm text-zinc-500">Retrieving memories...</p>
            </div>
          ) : (semanticResults || memories).length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 border border-dashed border-zinc-300 dark:border-zinc-800 rounded-xl text-center">
              <Brain className="w-10 h-10 text-zinc-300 dark:text-zinc-700 mb-3" />
              <h3 className="text-base font-semibold text-zinc-800 dark:text-zinc-200">
                {activeTab === 'archived' ? 'No archived memories' : 'No memories found'}
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm">
                {activeTab === 'archived'
                  ? 'Archived memories will appear here. Archiving keeps historical facts safe without polluting active context.'
                  : 'Start by having a conversation with Jenna or click "Add Memory" to explicitly teach Jenna a preference or fact.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(semanticResults
                ? semanticResults.map((r) => ({ ...r.memory, _searchScore: r.score, _breakdown: r.breakdown }))
                : memories
              ).map((mem: any) => {
                const typeConfig = MEMORY_TYPES.find((t) => t.type === mem.memory_type) || MEMORY_TYPES[0];
                const isExplicit = mem.source === 'USER_EXPLICIT';

                return (
                  <div
                    key={mem.id}
                    className="flex flex-col justify-between p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-sm hover:border-indigo-500/30 transition-all group"
                  >
                    <div>
                      {/* Card Header: Type, Status, Source */}
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${typeConfig.color}`}>
                            {typeConfig.label}
                          </span>
                          {isExplicit && (
                            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center gap-1">
                              <Zap className="w-3 h-3" /> Explicit
                            </span>
                          )}
                          <span
                            className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                              mem.status === 'ACTIVE'
                                ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                                : mem.status === 'ARCHIVED'
                                ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                                : 'bg-purple-500/10 text-purple-500 border-purple-500/20'
                            }`}
                          >
                            {mem.status}
                          </span>
                        </div>

                        {/* Semantic Score Pill if searching */}
                        {mem._searchScore !== undefined && (
                          <div className="flex items-center gap-1 px-2 py-0.5 bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 rounded-full text-xs font-semibold">
                            <Sparkles className="w-3 h-3" />
                            <span>Score: {(mem._searchScore * 100).toFixed(1)}%</span>
                          </div>
                        )}
                      </div>

                      {/* Content */}
                      <p className="text-sm text-zinc-900 dark:text-zinc-100 font-medium leading-relaxed">
                        {mem.content}
                      </p>

                      {mem.summary && (
                        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 italic">
                          Summary: {mem.summary}
                        </p>
                      )}

                      {/* Explanation note if metadata has reason */}
                      {mem.metadata?.extraction_reason && (
                        <p className="text-[11px] text-zinc-400 dark:text-zinc-500 mt-2 flex items-center gap-1">
                          <HelpCircle className="w-3 h-3" />
                          {mem.metadata.extraction_reason}
                        </p>
                      )}
                    </div>

                    {/* Card Footer: Metrics & Actions */}
                    <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
                      {/* Stats */}
                      <div className="flex items-center gap-3">
                        <span title="Importance Weight">Imp: {Math.round((mem.importance || 0.5) * 100)}%</span>
                        <span title="Confidence Weight">Conf: {Math.round((mem.confidence || 0.8) * 100)}%</span>
                        {mem.has_embedding && (
                          <span className="text-emerald-500 flex items-center gap-1" title="Vector Embedding Active">
                            <CheckCircle2 className="w-3 h-3" /> 768d
                          </span>
                        )}
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1">
                        {/* Feedback Thumbs */}
                        {activeTab === 'active' && (
                          <>
                            <button
                              onClick={() => handleFeedback(mem.id, 'USEFUL')}
                              className="p-1.5 text-zinc-400 hover:text-emerald-500 hover:bg-emerald-500/10 rounded transition-colors"
                              title="Useful memory (boosts confidence)"
                            >
                              <ThumbsUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleFeedback(mem.id, 'INCORRECT')}
                              className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                              title="Incorrect memory"
                            >
                              <ThumbsDown className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleArchive(mem.id)}
                              className="p-1.5 text-zinc-400 hover:text-amber-500 hover:bg-amber-500/10 rounded transition-colors"
                              title="Archive memory"
                            >
                              <Archive className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}

                        {activeTab === 'archived' && (
                          <button
                            onClick={() => handleRestore(mem.id)}
                            className="p-1.5 text-zinc-400 hover:text-indigo-500 hover:bg-indigo-500/10 rounded transition-colors"
                            title="Restore memory to active"
                          >
                            <ArchiveRestore className="w-3.5 h-3.5" />
                          </button>
                        )}

                        <button
                          onClick={() => openEditModal(mem)}
                          className="p-1.5 text-zinc-400 hover:text-indigo-500 hover:bg-indigo-500/10 rounded transition-colors"
                          title="Edit memory"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setMemoryToDelete(mem);
                            setIsDeleteModalOpen(true);
                          }}
                          className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                          title="Delete memory"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Extraction & Safety Playground */}
      {activeTab === 'extractor' && (
        <div className="space-y-6">
          <div className="p-5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-4">
            <div>
              <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-500" />
                Candidate Extraction & Privacy Inspector
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                Test how Jenna extracts memories from conversation text, detects sensitivity (passwords, API keys, credentials), and compares against existing memories to prevent duplicates or contradictory facts.
              </p>
            </div>

            <div>
              <textarea
                value={extractInput}
                onChange={(e) => setExtractInput(e.target.value)}
                placeholder="Enter sample conversation or command (e.g. 'Please remember that I prefer dark mode and work in Seattle', or test credential safety with 'My password is secret123')..."
                rows={3}
                className="w-full p-3 bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setExtractInput('Please remember that I prefer Python and FastAPI for backend development.')}
                  className="px-2.5 py-1 text-xs bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 text-zinc-600 dark:text-zinc-400 rounded-md transition-colors"
                >
                  Pref Sample
                </button>
                <button
                  type="button"
                  onClick={() => setExtractInput('Yaad rakhna mera favorite editor VS Code hai.')}
                  className="px-2.5 py-1 text-xs bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 text-zinc-600 dark:text-zinc-400 rounded-md transition-colors"
                >
                  Hinglish Sample
                </button>
                <button
                  type="button"
                  onClick={() => setExtractInput('Please remember my API key is sk-proj-1234567890abcdef1234567890')}
                  className="px-2.5 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-md transition-colors"
                >
                  Security Test (Blocked)
                </button>
              </div>

              <button
                onClick={handleExtractCandidates}
                disabled={isExtracting || !extractInput.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {isExtracting ? 'Analyzing...' : 'Extract Candidates'}
              </button>
            </div>
          </div>

          {extractError && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-600 dark:text-amber-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{extractError}</span>
            </div>
          )}

          {extractCandidates.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Extracted Candidates ({extractCandidates.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {extractCandidates.map((cand, idx) => {
                  const isBlocked = cand.suggested_action === 'IGNORE' && cand.sensitivity !== 'SAFE';
                  const isSuperseding = cand.suggested_action === 'SUPERSEDE';

                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border flex flex-col justify-between ${
                        isBlocked
                          ? 'bg-red-500/5 border-red-500/30'
                          : isSuperseding
                          ? 'bg-amber-500/5 border-amber-500/30'
                          : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                            {cand.memory_type}
                          </span>

                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded ${
                              cand.sensitivity === 'SAFE'
                                ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                                : 'bg-red-500/10 text-red-500 border border-red-500/20'
                            }`}
                          >
                            {cand.sensitivity === 'SAFE' ? 'SAFE' : 'BLOCKED: ' + cand.sensitivity}
                          </span>
                        </div>

                        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{cand.content}</p>

                        <div className="mt-3 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
                          <p>
                            <strong>Action:</strong> {cand.suggested_action}
                          </p>
                          <p>
                            <strong>Reason:</strong> {cand.reason}
                          </p>
                          <p>
                            <strong>Importance:</strong> {Math.round(cand.importance * 100)}% | <strong>Confidence:</strong>{' '}
                            {Math.round(cand.confidence * 100)}%
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 flex justify-end gap-2">
                        <button
                          onClick={() => handleConfirmCandidate(cand, false)}
                          className="px-3 py-1.5 text-xs text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
                        >
                          Dismiss
                        </button>
                        {cand.suggested_action !== 'IGNORE' && (
                          <button
                            onClick={() => handleConfirmCandidate(cand, true)}
                            className="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                          >
                            {isSuperseding ? 'Confirm Supersession' : 'Save to Memory'}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Short-Term Working Memory */}
      {activeTab === 'working' && (
        <div className="space-y-6">
          <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Ephemeral Working Memory
                </h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Temporary scratchpad stored in Redis with TTL. Automatically injected into active conversations.
                </p>
              </div>

              {Object.keys(workingMemory).length > 0 && (
                <button
                  onClick={handleClearWorkingMemory}
                  className="text-xs text-red-500 hover:text-red-600 font-medium px-3 py-1.5 border border-red-500/20 rounded-lg hover:bg-red-500/10 transition-colors"
                >
                  Clear All Working Memory
                </button>
              )}
            </div>

            {/* Set Item Form */}
            <form onSubmit={handleSetWorkingMemory} className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                placeholder="Key (e.g. active_task, current_topic)..."
                value={newWorkingKey}
                onChange={(e) => setNewWorkingKey(e.target.value)}
                className="flex-1 p-2 text-sm bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-zinc-100"
              />
              <input
                type="text"
                placeholder="Value..."
                value={newWorkingVal}
                onChange={(e) => setNewWorkingVal(e.target.value)}
                className="flex-1 p-2 text-sm bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-zinc-100"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
              >
                Set Item
              </button>
            </form>
          </div>

          {/* Key-Value Items */}
          {Object.keys(workingMemory).length === 0 ? (
            <div className="p-8 border border-dashed border-zinc-300 dark:border-zinc-800 rounded-xl text-center text-sm text-zinc-400">
              Working memory is currently empty.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(workingMemory).map(([k, v]) => (
                <div
                  key={k}
                  className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-mono text-indigo-500 font-semibold">{k}</span>
                    <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200 mt-1">{String(v)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal: Create or Edit Memory */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-zinc-200 dark:border-zinc-800">
              <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                {editingMemory ? 'Edit Memory' : 'Create New Persistent Memory'}
              </h3>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-zinc-400 hover:text-zinc-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Memory Content <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  placeholder="e.g. User prefers concise answers and Python over JavaScript..."
                  className="w-full p-2.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Summary (Optional)
                </label>
                <input
                  type="text"
                  value={formSummary}
                  onChange={(e) => setFormSummary(e.target.value)}
                  placeholder="Brief 1-line gist..."
                  className="w-full p-2 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Memory Category
                  </label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as MemoryType)}
                    className="w-full p-2 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {MEMORY_TYPES.map((t) => (
                      <option key={t.type} value={t.type}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Importance: {Math.round(formImportance * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={formImportance}
                    onChange={(e) => setFormImportance(parseFloat(e.target.value))}
                    className="w-full accent-indigo-600"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-zinc-200 dark:border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-sm text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !formContent.trim()}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : editingMemory ? 'Update Memory' : 'Create & Embed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Delete Confirmation */}
      {isDeleteModalOpen && memoryToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center gap-3 text-red-500">
              <AlertCircle className="w-6 h-6" />
              <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Delete Memory</h3>
            </div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Are you sure you want to permanently remove this memory from Jenna? Once deleted, it will never be retrieved in future conversations.
            </p>
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg text-xs font-mono text-zinc-700 dark:text-zinc-300">
              &quot;{memoryToDelete.content}&quot;
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setMemoryToDelete(null);
                }}
                className="px-4 py-2 text-sm text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
