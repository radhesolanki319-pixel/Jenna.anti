'use client';

import React from 'react';
import {
  X,
  Check,
  Zap,
  Flame,
  Cpu,
  Eye,
  Volume2,
  Code,
  ChevronRight,
  Upload,
  Image as ImageIcon,
  Video,
  Globe,
  LayoutTemplate,
  FileCode,
} from 'lucide-react';

interface AstraModelDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  onOpenUpload: () => void;
  onOpenImageGen: () => void;
  onSelectToolPrompt: (prompt: string) => void;
}

export function AstraModelDrawer({
  isOpen,
  onClose,
  selectedModel,
  onSelectModel,
  onOpenUpload,
  onOpenImageGen,
  onSelectToolPrompt,
}: AstraModelDrawerProps) {
  if (!isOpen) return null;

  const models = [
    {
      id: 'gemini-3.8-flash',
      name: 'GPT-6 Astra',
      badge: 'Advanced',
      tag: 'Most advanced reasoning',
      icon: Flame,
      color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    },
    {
      id: 'gemini-3.6-flash',
      name: 'GPT-5.6 Luna',
      badge: 'Fast',
      tag: 'Fast & efficient',
      icon: Zap,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    },
    {
      id: 'gemini-2.5-flash',
      name: 'GPT-5',
      badge: 'Standard',
      tag: 'Balanced for everyday use',
      icon: Cpu,
      color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
    },
    {
      id: 'gemini-vision',
      name: 'Vision',
      badge: 'Multimodal',
      tag: 'Image & video understanding',
      icon: Eye,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    },
    {
      id: 'gemini-audio',
      name: 'Audio',
      badge: 'Voice',
      tag: 'Voice & speech capabilities',
      icon: Volume2,
      color: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
    },
    {
      id: 'gemini-code',
      name: 'Code',
      badge: 'Specialized',
      tag: 'Optimized for programming',
      icon: Code,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    },
  ];

  const tools = [
    {
      id: 'upload',
      name: 'Upload File',
      desc: 'PDF, DOC, TXT...',
      icon: Upload,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      action: onOpenUpload,
    },
    {
      id: 'image',
      name: 'Create Image',
      desc: 'Text to image',
      icon: ImageIcon,
      color: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
      action: onOpenImageGen,
    },
    {
      id: 'video',
      name: 'Generate Video',
      desc: 'Text to video',
      icon: Video,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
      action: () => onSelectToolPrompt('Generate a short sci-fi video storyboard: '),
    },
    {
      id: 'search',
      name: 'Web Search',
      desc: 'Real-time info',
      icon: Globe,
      color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
      action: () => onSelectToolPrompt('Search the web for the latest updates on: '),
    },
    {
      id: 'template-life',
      name: 'Use a Template',
      desc: 'Real-time life',
      icon: LayoutTemplate,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      action: () => onSelectToolPrompt('Provide a daily routine and lifestyle productivity template for: '),
    },
    {
      id: 'template-code',
      name: 'Use a Template',
      desc: 'Ready-made prompts',
      icon: FileCode,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      action: () => onSelectToolPrompt('Create a full TypeScript + React component template for: '),
    },
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Content */}
      <aside className="relative w-84 sm:w-96 h-full bg-[#0a0e17]/95 backdrop-blur-2xl border-l border-white/[0.08] shadow-2xl flex flex-col z-10 overflow-y-auto">
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <span>GPT-6 Astra</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                Active
              </span>
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">Most advanced model</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.08] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Model Selection Section */}
        <div className="p-5 border-b border-white/[0.06] space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
            Select a model
          </div>

          <div className="space-y-1.5">
            {models.map((m) => {
              const isSelected = selectedModel === m.id || (m.id === 'gemini-3.8-flash' && selectedModel.includes('3.8'));
              const Icon = m.icon;

              return (
                <button
                  key={m.id}
                  onClick={() => {
                    onSelectModel(m.id);
                  }}
                  className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'bg-blue-600/15 border-blue-500/40 text-white shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                      : 'bg-white/[0.02] border-white/[0.04] text-zinc-300 hover:bg-white/[0.05] hover:border-white/[0.08]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${m.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-white flex items-center gap-2">
                        <span>{m.name}</span>
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5">{m.tag}</div>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onSelectToolPrompt('Explain the differences and architecture between all available Astra neural models.')}
            className="w-full flex items-center justify-between px-3 py-2 text-xs text-zinc-400 hover:text-cyan-300 transition"
          >
            <span>More models</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Tools Section */}
        <div className="p-5 space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
            Tools
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {tools.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => {
                    t.action();
                    onClose();
                  }}
                  className="p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.06] hover:border-blue-500/30 transition-all text-left group"
                >
                  <div className={`w-8 h-8 rounded-lg border flex items-center justify-center mb-2.5 ${t.color} group-hover:scale-105 transition-transform`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-semibold text-white truncate">{t.name}</div>
                  <div className="text-[10px] text-zinc-400 truncate mt-0.5">{t.desc}</div>
                </button>
              );
            })}
          </div>
        </div>
      </aside>
    </div>
  );
}
