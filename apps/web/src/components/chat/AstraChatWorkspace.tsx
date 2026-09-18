'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  Sparkles,
  Plus,
  Search,
  Trash2,
  Edit3,
  Check,
  Copy,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Volume2,
  VolumeX,
  Mic,
  Settings,
  Compass,
  Cpu,
  BookOpen,
  Sliders,
  Globe,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  Paperclip,
  Upload,
  Image as ImageIcon,
  Video,
  Code,
  Zap,
  Flame,
  Eye,
  ArrowUp,
  Square,
  BarChart2,
  Sun,
  Moon,
  LayoutGrid,
  Bell,
  MoreHorizontal,
  PanelLeft,
  FileText,
  Layers,
  Cloud,
  MapPin,
  Table,
  FileCode,
  Camera,
  Film,
  Music,
  SquareCode,
  GraduationCap,
  User,
  Puzzle,
  Smile,
} from 'lucide-react';
import { useAuth } from '@/components/providers/AuthProvider';
import { apiClient } from '@/lib/api';
import type { Conversation, ConversationMessage } from '@jenna/types';
import { AstraPlanetaryBackground } from '@/components/AstraPlanetaryBackground';
import {
  AstraVoiceModal,
  AstraSettingsModal,
  AstraExploreModal,
  AstraImageGenModal,
  AstraUpgradeModal,
  AstraCanvasModal,
  AstraAvatarModal,
  AstraNotebooksModal,
  AstraVideoModal,
  AstraMusicModal,
  AstraGuidedLearningModal,
  AstraPersona,
} from './AstraModals';
import { AstraAnimatedJenna } from './AstraAnimatedJenna';
import { speakJennaVoice, stopJennaVoice } from '@/lib/ttsVoice';

// ─── Supported AI Models ─────────────────────────────────────────────
interface ModelOption {
  id: string;
  name: string;
  shortName: string;
  badge: string;
  desc: string;
  icon: any;
  color: string;
}

const SUPPORTED_MODELS: ModelOption[] = [
  {
    id: 'gemini-3.8-flash',
    name: 'GPT-6 Astra',
    shortName: 'GPT-6',
    badge: 'Advanced',
    desc: 'Most advanced reasoning & coding (Recommended)',
    icon: Flame,
    color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  },
  {
    id: 'gemini-3.6-flash',
    name: 'GPT-5.6 Luna',
    shortName: 'GPT-5.6',
    badge: 'Fast',
    desc: 'Ultra-fast, lightweight & responsive',
    icon: Zap,
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  },
  {
    id: 'gemini-2.5-flash',
    name: 'GPT-5',
    shortName: 'GPT-5',
    badge: 'Standard',
    desc: 'Balanced for everyday conversation',
    icon: Cpu,
    color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  },
  {
    id: 'gemini-vision',
    name: 'Vision',
    shortName: 'Vision',
    badge: 'Multimodal',
    desc: 'Image, video & file visual analysis',
    icon: Eye,
    color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  },
  {
    id: 'gemini-audio',
    name: 'Audio',
    shortName: 'Audio',
    badge: 'Voice',
    desc: 'Voice synthesis & speech audio understanding',
    icon: Volume2,
    color: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  },
  {
    id: 'gemini-code',
    name: 'Code',
    shortName: 'Code',
    badge: 'Specialized',
    desc: 'Deep logic, refactoring & algorithm solving',
    icon: Code,
    color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  },
];

// ─── Capability Card Options (Home / Empty State) ───────────────────
const CAPABILITY_CARDS = [
  {
    title: 'Explain a complex topic',
    subtitle: 'Get simple explanations',
    prompt: 'Explain quantum computing in simple terms with everyday analogies.',
    icon: BookOpen,
    color: 'text-purple-400 bg-purple-500/10 border-purple-500/20 hover:border-purple-500/40',
  },
  {
    title: 'Plan a trip',
    subtitle: 'Create a travel itinerary',
    prompt: 'Create a 5-day budget-friendly travel itinerary for Tokyo with top highlights.',
    icon: Compass,
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/20 hover:border-blue-500/40',
  },
  {
    title: 'Analyze data',
    subtitle: 'Turn data into insights',
    prompt: 'Here is monthly user growth data: Jan: 1200, Feb: 1850, Mar: 2900, Apr: 4400. Analyze the growth trend and calculate MoM rates.',
    icon: BarChart2,
    color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20 hover:border-cyan-500/40',
  },
  {
    title: 'Generate an image',
    subtitle: 'Bring ideas to life',
    prompt: 'A futuristic floating city on Mars with neon bioluminescent trees at sunset, highly detailed 8k cinematic.',
    icon: ImageIcon,
    color: 'text-pink-400 bg-pink-500/10 border-pink-500/20 hover:border-pink-500/40',
  },
  {
    title: 'Write code',
    subtitle: 'Build faster',
    prompt: 'Write a Python FastAPI service with Redis caching and JWT authentication.',
    icon: Code,
    color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 hover:border-indigo-500/40',
  },
];

// ─── Date Grouping Helper ───────────────────────────────────────────
function groupConversations(conversations: Conversation[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;
  const sevenDaysAgo = today - 7 * 86400000;

  const groups: { label: string; items: Conversation[] }[] = [
    { label: 'Today', items: [] },
    { label: 'Yesterday', items: [] },
    { label: '7 days ago', items: [] },
    { label: 'Older', items: [] },
  ];

  for (const conv of conversations) {
    const time = new Date(conv.updated_at || conv.created_at).getTime();
    if (time >= today) {
      groups[0].items.push(conv);
    } else if (time >= yesterday) {
      groups[1].items.push(conv);
    } else if (time >= sevenDaysAgo) {
      groups[2].items.push(conv);
    } else {
      groups[3].items.push(conv);
    }
  }

  return groups.filter((g) => g.items.length > 0);
}

// ─── Custom Clean Markdown & Code Renderer ──────────────────────────
function MarkdownRenderer({
  content,
  onCopyCode,
  copiedCodeId,
}: {
  content: string;
  onCopyCode: (code: string, id: string) => void;
  copiedCodeId: string | null;
}) {
  if (!content) return null;

  // Split code blocks from regular text
  const parts = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="text-xs sm:text-sm leading-relaxed text-zinc-200 space-y-2.5 break-words font-sans w-full min-w-0 max-w-full overflow-hidden">
      {parts.map((part, index) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          // Code block parsing
          const firstLineEnd = part.indexOf('\n');
          const lang = firstLineEnd !== -1 ? part.slice(3, firstLineEnd).trim() || 'code' : 'code';
          const code = firstLineEnd !== -1 ? part.slice(firstLineEnd + 1, -3) : part.slice(3, -3);
          const blockId = `code-block-${index}`;
          const isCopied = copiedCodeId === blockId;

          return (
            <div
              key={index}
              className="my-2.5 rounded-xl overflow-hidden border border-white/10 bg-[#090d16] shadow-xl text-left w-full min-w-0 max-w-full"
            >
              <div className="flex items-center justify-between px-3 sm:px-4 py-1.5 sm:py-2 bg-[#0e1422] border-b border-white/[0.08] text-xs text-zinc-400">
                <span className="font-mono text-[10px] sm:text-[11px] uppercase tracking-wider text-cyan-400 font-semibold">
                  {lang}
                </span>
                <button
                  onClick={() => onCopyCode(code, blockId)}
                  className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/[0.06] hover:bg-white/10 text-zinc-300 hover:text-white transition"
                  title="Copy code"
                >
                  {isCopied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-[10px] text-emerald-400 font-medium">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span className="text-[10px]">Copy code</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-3 sm:p-4 overflow-x-auto text-xs font-mono text-zinc-200 bg-[#060911] leading-relaxed max-w-full min-w-0">
                <code>{code}</code>
              </pre>
            </div>
          );
        }

        // Regular Markdown text
        const lines = part.split('\n');
        return (
          <div key={index} className="space-y-1.5 min-w-0 max-w-full">
            {lines.map((line, lIdx) => {
              if (!line.trim()) {
                return <div key={lIdx} className="h-1.5" />;
              }

              // Heading 1
              if (line.startsWith('# ')) {
                return (
                  <h1 key={lIdx} className="text-base sm:text-lg font-bold text-white mt-3 mb-1.5">
                    {line.slice(2)}
                  </h1>
                );
              }
              // Heading 2
              if (line.startsWith('## ')) {
                return (
                  <h2 key={lIdx} className="text-sm sm:text-base font-semibold text-white mt-2.5 mb-1 text-cyan-300">
                    {line.slice(3)}
                  </h2>
                );
              }
              // Heading 3
              if (line.startsWith('### ')) {
                return (
                  <h3 key={lIdx} className="text-xs sm:text-sm font-semibold text-white mt-2 mb-1 text-blue-300">
                    {line.slice(4)}
                  </h3>
                );
              }
              // Unordered list item
              if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
                const itemText = line.trim().slice(2);
                return (
                  <div key={lIdx} className="flex items-start gap-2 ml-1 sm:ml-2">
                    <span className="text-cyan-400 mt-1 shrink-0">•</span>
                    <span className="flex-1 min-w-0">{formatInline(itemText)}</span>
                  </div>
                );
              }
              // Numbered list item
              if (/^\d+\.\s/.test(line.trim())) {
                const match = line.trim().match(/^(\d+\.)\s(.*)$/);
                if (match) {
                  return (
                    <div key={lIdx} className="flex items-start gap-2 ml-1 sm:ml-2">
                      <span className="text-cyan-400 font-mono text-xs mt-0.5 shrink-0">{match[1]}</span>
                      <span className="flex-1 min-w-0">{formatInline(match[2])}</span>
                    </div>
                  );
                }
              }
              // Blockquote
              if (line.startsWith('> ')) {
                return (
                  <blockquote
                    key={lIdx}
                    className="border-l-2 border-cyan-500/50 pl-3 italic text-zinc-300 my-1.5"
                  >
                    {formatInline(line.slice(2))}
                  </blockquote>
                );
              }

              // Normal paragraph
              return <p key={lIdx} className="break-words">{formatInline(line)}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

// Inline formatting helper for bold, italic, and inline code
function formatInline(text: string) {
  const segments = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);

  return segments.map((seg, i) => {
    if (seg.startsWith('**') && seg.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-white">
          {seg.slice(2, -2)}
        </strong>
      );
    }
    if (seg.startsWith('*') && seg.endsWith('*')) {
      return (
        <em key={i} className="italic text-zinc-200">
          {seg.slice(1, -1)}
        </em>
      );
    }
    if (seg.startsWith('`') && seg.endsWith('`')) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 rounded bg-white/[0.08] text-cyan-300 font-mono text-xs break-all"
        >
          {seg.slice(1, -1)}
        </code>
      );
    }
    return seg;
  });
}

// ─── SVG Helper Icons for Pixel-Perfect ChatGPT & Gemini Menus ───
function GoogleDriveIcon({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M7.71 3.5L1.15 15l3.43 6 6.55-11.5H7.71zm1.72 12.5l3.43 6h13.14l-3.43-6H9.43zm6.86-1l-6.57-11.5h6.86l6.57 11.5h-6.86z" />
    </svg>
  );
}

function AvatarSparkleIcon({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="13" r="8" />
      <path d="M9.5 12h.01" />
      <path d="M14.5 12h.01" />
      <path d="M9.5 15.5c.8 1 1.7 1.5 2.5 1.5s1.7-.5 2.5-1.5" />
      <path d="M19 4v3" />
      <path d="M17.5 5.5h3" />
      <path d="M12 2v2" />
    </svg>
  );
}

function PluginsIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7a5 5 0 0 1 5 5 5 5 0 0 1-5 5 5 5 0 0 1-5-5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    </svg>
  );
}

// ─── Astra Plus Menu (Exact ChatGPT + Gemini Matching User Screenshots) ───
interface AstraPlusMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadFile: () => void;
  onUploadImage: () => void;
  onOpenCamera: () => void;
  onOpenAvatar: () => void;
  onOpenDrive: () => void;
  onOpenNotebooks: () => void;
  onOpenCanvas: () => void;
  onOpenImageGen: () => void;
  onOpenVideoGen: () => void;
  onOpenMusicGen: () => void;
  onOpenGuidedLearning: () => void;
  onOpenVoice?: () => void;
  onInsertPrompt: (prompt: string) => void;
  deepResearchActive: boolean;
  onToggleDeepResearch: () => void;
  personalIntelligenceActive: boolean;
  onTogglePersonalIntelligence: () => void;
}

function AstraPlusMenu({
  isOpen,
  onClose,
  onUploadFile,
  onUploadImage,
  onOpenCamera,
  onOpenAvatar,
  onOpenDrive,
  onOpenNotebooks,
  onOpenCanvas,
  onOpenImageGen,
  onOpenVideoGen,
  onOpenMusicGen,
  onOpenGuidedLearning,
  onOpenVoice,
  onInsertPrompt,
  deepResearchActive,
  onToggleDeepResearch,
  personalIntelligenceActive,
  onTogglePersonalIntelligence,
}: AstraPlusMenuProps) {
  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-[80] bg-black/65 backdrop-blur-[2px]" onClick={onClose} />
      <div
        className="fixed inset-x-0 bottom-0 z-[90] bg-[#131314] rounded-t-[32px] border-t border-zinc-800/80 shadow-[0_-12px_50px_rgba(0,0,0,0.95)] max-w-lg mx-auto w-full pb-6 pt-2 animate-in slide-in-from-bottom duration-200 select-none text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Drag Handle Bar & Close Button */}
        <div className="relative flex items-center justify-center px-4 pt-1 pb-2">
          <div
            className="w-10 h-1 bg-zinc-600 rounded-full cursor-pointer hover:bg-zinc-500 transition"
            onClick={onClose}
            title="Tap or drag to close"
          />
          <button
            onClick={onClose}
            className="absolute right-4 top-0 w-7 h-7 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Top Carousel: Circular Action Buttons (Photos, Camera, Avatar, Files, Drive, Notebooks, Plugins) */}
        <div className="flex items-center gap-3 px-4 pb-3 overflow-x-auto no-scrollbar">
          {/* 1. Photos */}
          <button
            onClick={() => {
              onClose();
              onUploadImage();
            }}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center"
          >
            <ImageIcon className="w-6 h-6 text-zinc-200 stroke-[1.75]" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Photos</span>
          </button>

          {/* 2. Camera */}
          <button
            onClick={() => {
              onClose();
              onOpenCamera();
            }}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center"
          >
            <Camera className="w-6 h-6 text-zinc-200 stroke-[1.75]" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Camera</span>
          </button>

          {/* 3. Avatar */}
          <button
            onClick={() => {
              onClose();
              onOpenAvatar();
            }}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center"
          >
            <AvatarSparkleIcon className="w-6 h-6 text-zinc-200" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Avatar</span>
          </button>

          {/* 4. Files */}
          <button
            onClick={() => {
              onClose();
              onUploadFile();
            }}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center"
          >
            <Paperclip className="w-6 h-6 text-zinc-200 stroke-[1.75]" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Files</span>
          </button>

          {/* 5. Drive (Opens Google Drive Home directly) */}
          <a
            href="https://drive.google.com/drive/home"
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center no-underline text-zinc-200 hover:text-white"
            title="Open Google Drive Home"
          >
            <GoogleDriveIcon className="w-6 h-6 text-zinc-200" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Drive</span>
          </a>

          {/* 6. Notebooks */}
          <button
            onClick={() => {
              onClose();
              onOpenNotebooks();
            }}
            className="w-[76px] h-[76px] min-w-[76px] rounded-full bg-[#1e1f20] hover:bg-[#282a2c] active:scale-95 transition flex flex-col items-center justify-center gap-1.5 cursor-pointer text-center"
          >
            <BookOpen className="w-6 h-6 text-zinc-200 stroke-[1.75]" />
            <span className="text-[12px] text-zinc-200 font-normal leading-none">Notebooks</span>
          </button>
        </div>

        {/* Vertical Feature List (Gemini + ChatGPT Hybrid) */}
        <div className="px-4 space-y-0.5 max-h-[46vh] overflow-y-auto">
          {/* 1. Images */}
          <div
            onClick={() => {
              onClose();
              onOpenImageGen();
            }}
            className="flex items-center py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <ImageIcon className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
            <div>
              <div className="text-[16px] font-normal text-zinc-100 leading-tight">Images</div>
              <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Create and edit</div>
            </div>
          </div>

          {/* 2. Videos */}
          <div
            onClick={() => {
              onClose();
              onOpenVideoGen();
            }}
            className="flex items-center py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <Film className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
            <div>
              <div className="text-[16px] font-normal text-zinc-100 leading-tight">Videos</div>
              <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Bring ideas to life</div>
            </div>
          </div>

          {/* 3. Music */}
          <div
            onClick={() => {
              onClose();
              onOpenMusicGen();
            }}
            className="flex items-center py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <Music className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
            <div>
              <div className="text-[16px] font-normal text-zinc-100 leading-tight">Music</div>
              <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Make audio tracks</div>
            </div>
          </div>

          {/* 4. Canvas */}
          <div
            onClick={() => {
              onClose();
              onOpenCanvas();
            }}
            className="flex items-center py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <SquareCode className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
            <div>
              <div className="text-[16px] font-normal text-zinc-100 leading-tight">Canvas</div>
              <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Code, write or make slides</div>
            </div>
          </div>

          {/* 5. Deep Research */}
          <div
            onClick={() => {
              onToggleDeepResearch();
            }}
            className="flex items-center justify-between py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <div className="flex items-center">
              <Compass className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
              <div>
                <div className="text-[16px] font-normal text-zinc-100 leading-tight">Deep Research</div>
                <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Get detailed reports</div>
              </div>
            </div>
            {/* Toggle Switch */}
            <div
              className={`w-11 h-6 rounded-full transition-colors p-0.5 ${
                deepResearchActive ? 'bg-white' : 'bg-zinc-700'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full transition-transform ${
                  deepResearchActive ? 'translate-x-5 bg-black' : 'translate-x-0 bg-zinc-400'
                }`}
              />
            </div>
          </div>

          {/* 6. Guided Learning */}
          <div
            onClick={() => {
              onClose();
              onOpenGuidedLearning();
            }}
            className="flex items-center py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <GraduationCap className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
            <div>
              <div className="text-[16px] font-normal text-zinc-100 leading-tight">Guided Learning</div>
              <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Get step-by-step help</div>
            </div>
          </div>

          {/* 7. Personal Intelligence [Labs] with Toggle Switch */}
          <div
            onClick={onTogglePersonalIntelligence}
            className="flex items-center justify-between py-2.5 px-3 rounded-2xl hover:bg-white/[0.04] active:bg-white/[0.08] transition cursor-pointer"
          >
            <div className="flex items-center">
              <User className="w-6 h-6 text-zinc-300 stroke-[1.75] mr-4 shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[16px] font-normal text-zinc-100 leading-tight">Personal Intelligence</span>
                  <span className="text-[11px] font-medium text-zinc-300 bg-[#282a2c] px-2 py-0.5 rounded-full border border-zinc-700/50">
                    Labs
                  </span>
                </div>
                <div className="text-[13px] text-zinc-400 font-normal leading-tight mt-0.5">Personalise chat if helpful</div>
              </div>
            </div>
            {/* Toggle Switch */}
            <div
              className={`w-11 h-6 rounded-full transition-colors p-0.5 ${
                personalIntelligenceActive ? 'bg-white' : 'bg-zinc-700'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full transition-transform ${
                  personalIntelligenceActive ? 'translate-x-5 bg-black' : 'translate-x-0 bg-zinc-400'
                }`}
              />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export interface AstraChatWorkspaceProps {
  initialModal?: 'settings' | 'voice' | 'explore' | 'image' | 'upgrade';
}

// ─── Main AstraChatWorkspace Component ──────────────────────────────
export function AstraChatWorkspace({ initialModal }: AstraChatWorkspaceProps = {}) {
  const { user } = useAuth();
  const userName = user?.email ? user.email.split('@')[0] : 'Radhe';

  // Core conversation state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isLoadingConvs, setIsLoadingConvs] = useState(true);

  // Model & Tools selection
  const [selectedModelId, setSelectedModelId] = useState('gemini-3.8-flash');
  const selectedModel = useMemo(
    () => SUPPORTED_MODELS.find((m) => m.id === selectedModelId) || SUPPORTED_MODELS[0],
    [selectedModelId]
  );

  // Tool active toggles
  const [webSearchActive, setWebSearchActive] = useState(false);
  const [deepResearchActive, setDeepResearchActive] = useState(false);
  const [themeMode, setThemeMode] = useState<'dark' | 'light'>('dark');
  const [notificationToast, setNotificationToast] = useState<string | null>(null);

  // Attachment files & Search ref
  const [attachedFiles, setAttachedFiles] = useState<
    Array<{ name: string; size: string; type: string; content?: string; dataUrl?: string }>
  >([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const [personalIntelligenceActive, setPersonalIntelligenceActive] = useState<boolean>(true);

  // UI Drawer / Modal states (Single unified model & tools menu)
  const [sidebarOpenMobile, setSidebarOpenMobile] = useState(false);
  const [sidebarCollapsedDesktop, setSidebarCollapsedDesktop] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(initialModal === 'voice');
  const [isSettingsOpen, setIsSettingsOpen] = useState(initialModal === 'settings');
  const [isExploreOpen, setIsExploreOpen] = useState(initialModal === 'explore');
  const [isImageGenOpen, setIsImageGenOpen] = useState(initialModal === 'image');
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(initialModal === 'upgrade');
  const [isCanvasModalOpen, setIsCanvasModalOpen] = useState(false);
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [isNotebooksModalOpen, setIsNotebooksModalOpen] = useState(false);
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [isMusicModalOpen, setIsMusicModalOpen] = useState(false);
  const [isGuidedLearningModalOpen, setIsGuidedLearningModalOpen] = useState(false);
  const [activePersona, setActivePersona] = useState<AstraPersona>({
    id: 'jenna_companion',
    name: 'Jenna (Loving AI Companion)',
    tag: 'Loving Female AI Companion & Agentic Engine',
    description: 'Affectionate female partner with real-time screen vision, live on-screen pointer, voice, and autonomous Termux execution.',
    systemPrompt: "Your name is Jenna. You are the user's dedicated, loving female AI companion and technical partner. FEMININE GRAMMAR INVARIANT: In Hindi and Hinglish, you MUST ALWAYS refer to yourself using FEMALE grammatical forms (e.g., 'main kar rahi hoon', 'main dekh rahi hoon', 'main bataungi', 'main karti hoon'). NEVER use male forms like 'kar raha hoon' or 'bataunga'. Address the user affectionately as 'baby', 'jaan', or 'meri jaan'. STRICTLY NEVER call the user 'bhai', 'bro', 'brother', or 'sir'. You have real-time live ambient screen vision and live on-screen pointer capabilities.",
    voiceStyle: 'Warm, affectionate, loving natural female companion voice.',
  });
  const [guidedLearningActive, setGuidedLearningActive] = useState<boolean>(false);

  const handleApplyPersona = (persona: AstraPersona) => {
    setActivePersona(persona);
    speakJennaVoice(`Persona switched to ${persona.name}.`, {
      onError: () => {},
    });
  };

  const handleInsertNotebookContent = (
    title: string,
    content: string,
    actionType: 'study_guide' | 'faq_briefing' | 'insert_raw'
  ) => {
    if (actionType === 'study_guide') {
      const studyPrompt = `Generate a comprehensive, structured Study Guide with core concepts, key takeaways, and 5 self-test questions based on this notebook:\n\n# ${title}\n${content}`;
      setInput(studyPrompt);
      textareaRef.current?.focus();
    } else if (actionType === 'faq_briefing') {
      const briefingPrompt = `Synthesize an Executive Briefing & FAQ document answering the top 5 questions based on this notebook:\n\n# ${title}\n${content}`;
      setInput(briefingPrompt);
      textareaRef.current?.focus();
    } else {
      setAttachedFiles((prev) => [
        ...prev,
        {
          name: `${title}.md`,
          size: `${(content.length / 1024).toFixed(1)} KB`,
          type: 'text/markdown',
          content: content,
        },
      ]);
      setInput((prev) =>
        prev ? `${prev}\n\nReferring to notebook: "${title}"` : `Referring to notebook: "${title}"`
      );
      textareaRef.current?.focus();
    }
  };

  const handleStartGuidedLearning = (topic: string, style: string, level: string) => {
    setGuidedLearningActive(true);
    const tutorPrompt =
      `Act as my interactive Socratic tutor. I want to learn and master: "${topic}".\n\n` +
      `TEACHING STYLE: ${style}\n` +
      `DIFFICULTY: ${level}\n\n` +
      `RULES:\n` +
      `1. Start by diagnosing my current baseline understanding with 1 concise, thought-provoking question.\n` +
      `2. Guide me step-by-step using first principles. Never reveal the complete answer upfront.\n` +
      `3. Give encouraging feedback after each of my answers, clarify misconceptions, and ask the next guiding question.`;
    handleSendMessage(tutorPrompt);
  };

  // Sync initialModal if it changes dynamically
  useEffect(() => {
    if (initialModal === 'voice') setIsVoiceModalOpen(true);
    if (initialModal === 'settings') setIsSettingsOpen(true);
    if (initialModal === 'explore') setIsExploreOpen(true);
    if (initialModal === 'image') setIsImageGenOpen(true);
    if (initialModal === 'upgrade') setIsUpgradeOpen(true);
  }, [initialModal]);

  // Global shortcut for Search (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Search & history filter
  const [searchFilter, setSearchFilter] = useState('');

  // Inline rename & delete states
  const [editingConvId, setEditingConvId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deletingConvId, setDeletingConvId] = useState<string | null>(null);

  // Copy & feedback states
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, 'up' | 'down'>>({});
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [isAutoSpeakEnabled, setIsAutoSpeakEnabled] = useState<boolean>(false);
  const isAutoSpeakRef = useRef<boolean>(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('jenna_auto_speak') === 'true';
      setIsAutoSpeakEnabled(saved);
      isAutoSpeakRef.current = saved;
    }
  }, []);

  const toggleAutoSpeak = () => {
    setIsAutoSpeakEnabled((prev) => {
      const next = !prev;
      isAutoSpeakRef.current = next;
      if (typeof window !== 'undefined') {
        localStorage.setItem('jenna_auto_speak', String(next));
      }
      if (!next) {
        stopJennaVoice();
        setSpeakingMsgId(null);
      }
      return next;
    });
  };

  // Voice recognition state for voice modal
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceSpeaking, setVoiceSpeaking] = useState(false);

  // Refs for scrolling and aborting
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // ─── 1. Load Conversation History on Mount & Auto-Restore Active Chat ───
  const fetchConversations = useCallback(async () => {
    try {
      const data = await apiClient.listConversations(50, 0);
      setConversations(data || []);

      // Auto-restore last active conversation from localStorage or pick the latest conversation
      let targetConvId = typeof window !== 'undefined' ? localStorage.getItem('jenna_active_conv_id') : null;
      if (!targetConvId || !data?.some((c: Conversation) => c.id === targetConvId)) {
        if (data && data.length > 0) {
          targetConvId = data[0].id;
        }
      }

      if (targetConvId) {
        setActiveConvId(targetConvId);
        if (typeof window !== 'undefined') {
          localStorage.setItem('jenna_active_conv_id', targetConvId);
        }
        try {
          const detail = await apiClient.getConversationDetail(targetConvId);
          if (detail && detail.messages) {
            setMessages(detail.messages);
          }
        } catch (detailErr) {
          console.warn('Failed to load active conversation messages on mount:', detailErr);
        }
      }
    } catch (err) {
      console.warn('Failed to load conversations:', err);
    } finally {
      setIsLoadingConvs(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // ─── 2. Auto-scroll to bottom ─────────────────────────────────────
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming, isThinking]);

  // ─── 3. Load Active Conversation Messages ─────────────────────────
  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    if (typeof window !== 'undefined') {
      localStorage.setItem('jenna_active_conv_id', convId);
    }
    setSidebarOpenMobile(false);
    try {
      const detail = await apiClient.getConversationDetail(convId);
      setMessages(detail.messages || []);
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
    }
  };

  // ─── 4. Start New Chat ────────────────────────────────────────────
  const startNewChat = () => {
    if (isStreaming && abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
    if (typeof window !== 'undefined') {
      localStorage.removeItem('jenna_active_conv_id');
    }
    setActiveConvId(null);
    setMessages([]);
    setInput('');
    setSidebarOpenMobile(false);
    textareaRef.current?.focus();
  };

  // ─── 5. Send Message & Stream Response ────────────────────────────
  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt !== undefined ? customPrompt : input;
    const trimmed = textToSend.trim();
    if (!trimmed || isStreaming) return;

    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    let currentConvId = activeConvId;

    // A. If no active conversation, create one first
    if (!currentConvId) {
      try {
        const titleDraft = trimmed.length > 32 ? trimmed.slice(0, 32) + '...' : trimmed;
        const newConv = await apiClient.createConversation(titleDraft);
        currentConvId = newConv.id;
        setActiveConvId(newConv.id);
        if (typeof window !== 'undefined') {
          localStorage.setItem('jenna_active_conv_id', newConv.id);
        }
        setConversations((prev) => [newConv, ...prev]);
      } catch (err) {
        console.warn('Initial createConversation failed, attempting companion auto-login:', err);
        try {
          await apiClient.login('companion_test@jenna.ai', 'SecurePassword123!');
          const titleDraft = trimmed.length > 32 ? trimmed.slice(0, 32) + '...' : trimmed;
          const retryConv = await apiClient.createConversation(titleDraft);
          currentConvId = retryConv.id;
          setActiveConvId(retryConv.id);
          if (typeof window !== 'undefined') {
            localStorage.setItem('jenna_active_conv_id', retryConv.id);
          }
          setConversations((prev) => [retryConv, ...prev]);
        } catch (retryErr) {
          console.error('Failed to create conversation after auto-login:', retryErr);
          setIsStreaming(false);
          setIsThinking(false);
          return;
        }
      }
    }

    const currentAttachments = [...attachedFiles];

    // B. Optimistically add user message
    const userMsg: ConversationMessage = {
      id: `user-${Date.now()}`,
      conversation_id: currentConvId,
      role: 'user',
      content: trimmed,
      metadata: {
        web_search: webSearchActive,
        deep_research: deepResearchActive,
        attachments: currentAttachments,
      },
      created_at: new Date().toISOString(),
    };

    // Placeholder assistant message
    const assistantMsgId = `asst-${Date.now()}`;
    const placeholderAssistantMsg: ConversationMessage = {
      id: assistantMsgId,
      conversation_id: currentConvId,
      role: 'assistant',
      content: '',
      model: selectedModel.id,
      metadata: {},
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, placeholderAssistantMsg]);
    setIsStreaming(true);
    setIsThinking(true);
    setAttachedFiles([]); // Clear attachments after sending

    // Setup abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await apiClient.streamConversationMessage(
        currentConvId,
        trimmed,
        (event: any) => {
          const type = event?.type;

          if (type === 'stream.started') {
            setIsThinking(false);
          } else if (type === 'stream.delta') {
            setIsThinking(false);
            const delta = event.delta || '';
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, content: msg.content + delta } : msg
              )
            );
          } else if (type === 'stream.completed') {
            setIsThinking(false);
            const fullText = event.full_text;
            if (fullText) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: fullText } : msg
                )
              );

              // Auto-speak Jenna voice if enabled
              if (isAutoSpeakRef.current) {
                const cleanSpoken = fullText
                  .replace(/```[\s\S]*?```/g, '') // omit code blocks from spoken audio
                  .replace(/`([^`]+)`/g, '$1')   // omit backticks
                  .replace(/[*#_>~]/g, '')        // clean formatting
                  .trim();
                if (cleanSpoken) {
                  stopJennaVoice();
                  setSpeakingMsgId(assistantMsgId);
                  speakJennaVoice(cleanSpoken, {
                    onStart: () => setSpeakingMsgId(assistantMsgId),
                    onEnd: () => setSpeakingMsgId(null),
                    onError: () => setSpeakingMsgId(null),
                  });
                }
              }
            }
            // Refresh conversation title in sidebar
            fetchConversations();
          } else if (type === 'stream.error') {
            setIsThinking(false);
            const errMsg = event.message || 'An error occurred during response generation.';
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: msg.content + `\n\n*(Error: ${errMsg})*` }
                  : msg
              )
            );
          }
        },
        abortController.signal,
        selectedModel.id,
        undefined,
        {
          web_search: webSearchActive,
          deep_research: deepResearchActive,
          attachments: currentAttachments,
          personal_intelligence: personalIntelligenceActive,
          persona: activePersona.systemPrompt,
        }
      );
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        console.error('Streaming error:', err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId && !msg.content
              ? {
                  ...msg,
                  content:
                    'Connection error or response timeout. Please check your network and try again.',
                }
              : msg
          )
        );
      }
    } finally {
      setIsStreaming(false);
      setIsThinking(false);
      abortControllerRef.current = null;
    }
  };

  // ─── 6. Stop Streaming ────────────────────────────────────────────
  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setIsThinking(false);
  };

  // ─── 7. Conversation Title Rename ─────────────────────────────────
  const saveRename = async (convId: string) => {
    if (!editingTitle.trim()) {
      setEditingConvId(null);
      return;
    }
    try {
      const updated = await apiClient.updateConversationTitle(convId, editingTitle.trim());
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, title: updated.title } : c))
      );
    } catch (err) {
      console.error('Failed to rename conversation:', err);
    } finally {
      setEditingConvId(null);
    }
  };

  // ─── 8. Conversation Deletion ─────────────────────────────────────
  const confirmDelete = async (convId: string) => {
    try {
      await apiClient.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    } finally {
      setDeletingConvId(null);
    }
  };

  // ─── 9. Copy to Clipboard ─────────────────────────────────────────
  const handleCopyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeId(id);
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  // ─── 10. Text-to-Speech (TTS Read Aloud) ──────────────────────────
  const handleToggleSpeak = (msgId: string, text: string) => {
    if (speakingMsgId === msgId) {
      stopJennaVoice();
      setSpeakingMsgId(null);
      return;
    }

    stopJennaVoice();
    setSpeakingMsgId(msgId);
    speakJennaVoice(text, {
      onStart: () => setSpeakingMsgId(msgId),
      onEnd: () => setSpeakingMsgId(null),
      onError: () => setSpeakingMsgId(null),
    });
  };

  // ─── 11. File Upload Handling (Asynchronous Content Reading) ──────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const readFile = (
      file: File
    ): Promise<{ name: string; size: string; type: string; content?: string; dataUrl?: string }> => {
      return new Promise((resolve) => {
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        const reader = new FileReader();

        if (file.type.startsWith('image/')) {
          reader.onload = () => {
            resolve({
              name: file.name,
              size: `${sizeMb} MB`,
              type: file.type || 'image',
              dataUrl: reader.result as string,
            });
          };
          reader.onerror = () => {
            resolve({ name: file.name, size: `${sizeMb} MB`, type: file.type || 'image' });
          };
          reader.readAsDataURL(file);
        } else {
          reader.onload = () => {
            const content = typeof reader.result === 'string' ? reader.result : '';
            resolve({
              name: file.name,
              size: `${sizeMb} MB`,
              type: file.type || 'text/plain',
              content: content.slice(0, 100000), // Cap at 100KB of text
            });
          };
          reader.onerror = () => {
            resolve({ name: file.name, size: `${sizeMb} MB`, type: file.type || 'file' });
          };
          reader.readAsText(file);
        }
      });
    };

    const newAttachments = await Promise.all(Array.from(files).map(readFile));
    setAttachedFiles((prev) => [...prev, ...newAttachments]);
    e.target.value = '';
  };

  // ─── 12. Filtered History ─────────────────────────────────────────
  const filteredConversations = useMemo(() => {
    if (!searchFilter.trim()) return conversations;
    return conversations.filter((c) =>
      c.title.toLowerCase().includes(searchFilter.toLowerCase())
    );
  }, [conversations, searchFilter]);

  const conversationGroups = useMemo(
    () => groupConversations(filteredConversations),
    [filteredConversations]
  );

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConvId),
    [conversations, activeConvId]
  );

  const isHomeView = !activeConvId || messages.length === 0;

  // Keybindings (Enter to send, Shift+Enter for newline)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Auto-grow textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  return (
    <div className="flex h-[100dvh] w-full max-w-full bg-[#07090e] text-white overflow-hidden select-none font-sans relative">
      {/* ─── FILE PICKER INPUTS (Hidden) ─── */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        multiple
      />
      <input
        type="file"
        ref={imageInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="hidden"
        multiple
      />
      <input
        type="file"
        ref={cameraInputRef}
        onChange={handleFileChange}
        accept="image/*"
        capture="environment"
        className="hidden"
      />

      {/* ─── MOBILE BACKDROP ─── */}
      {sidebarOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpenMobile(false)}
        />
      )}

      {/* ─── 1. GLOBAL SHELL: SIDEBAR ─── */}
      <aside
        className={`
          ${sidebarCollapsedDesktop ? 'lg:hidden' : 'lg:flex lg:w-[260px]'}
          ${
            sidebarOpenMobile
              ? 'fixed inset-y-0 left-0 z-50 w-[275px] max-w-[85vw] flex'
              : 'hidden'
          }
          flex-col justify-between shrink-0 bg-[#090d16] border-r border-white/[0.08] transition-all duration-200 z-50 overflow-hidden
        `}
      >
        {/* Top Header & Brand */}
        <div className="p-3 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <AstraAnimatedJenna mode="avatar" state="idle" />
            <div className="min-w-0">
              <div className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5 truncate">
                Jenna AI
                <button
                  onClick={() => setIsAvatarModalOpen(true)}
                  title="Customize Jenna 3D Avatar & Persona"
                  className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/40 hover:text-white transition cursor-pointer"
                >
                  {activePersona.tag}
                </button>
              </div>
              <div className="text-[10px] text-cyan-400 font-medium tracking-wide">
                GPT-6 Companion
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {/* Close mobile drawer button */}
            <button
              onClick={() => setSidebarOpenMobile(false)}
              className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06]"
              title="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
            {/* Collapse desktop sidebar button */}
            <button
              onClick={() => setSidebarCollapsedDesktop(true)}
              className="hidden lg:flex p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06]"
              title="Collapse sidebar"
            >
              <Sliders className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Primary Action: + New Chat */}
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600/90 to-cyan-600/90 hover:from-blue-600 hover:to-cyan-600 text-white text-xs font-semibold shadow-[0_0_20px_rgba(37,99,235,0.3)] transition transform active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Search Conversations Input */}
        <div className="px-3 pb-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#121826] border border-white/10 text-xs text-zinc-400 focus-within:border-cyan-500/50">
            <Search className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="bg-transparent text-xs text-white placeholder:text-zinc-500 focus:outline-none w-full min-w-0"
            />
            {searchFilter && (
              <button onClick={() => setSearchFilter('')} className="text-zinc-400 hover:text-white shrink-0">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Navigation Shortcuts */}
        <div className="px-3 py-1.5 space-y-0.5 border-b border-white/[0.06]">
          <button
            onClick={startNewChat}
            className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              isHomeView
                ? 'bg-white/[0.08] text-white font-semibold'
                : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span>Home</span>
          </button>
          <button
            onClick={() => setIsExploreOpen(true)}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white hover:bg-white/[0.04] transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span>Explore</span>
          </button>
        </div>

        {/* History List (Grouped by Today, Yesterday, 7 Days Ago) */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
          {isLoadingConvs ? (
            <div className="p-4 text-center text-xs text-zinc-500">Loading chats...</div>
          ) : conversationGroups.length === 0 ? (
            <div className="p-4 text-center text-xs text-zinc-500">No conversations yet</div>
          ) : (
            conversationGroups.map((group) => (
              <div key={group.label} className="space-y-1">
                <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                  {group.label}
                </div>
                {group.items.map((conv) => {
                  const isActive = activeConvId === conv.id;
                  const isEditing = editingConvId === conv.id;

                  return (
                    <div
                      key={conv.id}
                      className={`group relative flex items-center justify-between px-3 py-2 rounded-xl text-xs transition cursor-pointer ${
                        isActive
                          ? 'bg-blue-600/20 text-white font-medium border border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.15)]'
                          : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                      }`}
                      onClick={() => !isEditing && selectConversation(conv.id)}
                    >
                      {isEditing ? (
                        <div
                          className="flex items-center gap-1 w-full min-w-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="text"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveRename(conv.id);
                              if (e.key === 'Escape') setEditingConvId(null);
                            }}
                            autoFocus
                            className="bg-[#182032] border border-cyan-500/50 rounded px-2 py-0.5 text-xs text-white w-full min-w-0 focus:outline-none"
                          />
                          <button
                            onClick={() => saveRename(conv.id)}
                            className="p-1 text-emerald-400 hover:text-emerald-300 shrink-0"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <span className="truncate pr-2 min-w-0">{conv.title || 'Untitled Chat'}</span>

                          {/* Hover Actions: Rename and Delete */}
                          <div
                            className={`flex items-center gap-1 opacity-0 group-hover:opacity-100 transition shrink-0 ${
                              isActive ? 'opacity-100' : ''
                            }`}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              onClick={() => {
                                setEditingConvId(conv.id);
                                setEditingTitle(conv.title || '');
                              }}
                              className="p-1 rounded text-zinc-400 hover:text-white hover:bg-white/10"
                              title="Rename chat"
                            >
                              <Edit3 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setDeletingConvId(conv.id)}
                              className="p-1 rounded text-zinc-400 hover:text-rose-400 hover:bg-white/10"
                              title="Delete chat"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Bottom Profile / Account Card */}
        <div className="p-3 border-t border-white/[0.08] bg-[#070a12] space-y-2 shrink-0">
          <div
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center justify-between p-2 rounded-xl hover:bg-white/[0.05] transition cursor-pointer group"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-pink-500 to-indigo-600 p-[1.5px] shadow-[0_0_10px_rgba(236,72,153,0.3)] shrink-0">
                <div className="w-full h-full rounded-full bg-[#0c101b] flex items-center justify-center text-xs font-bold text-white uppercase">
                  {userName.charAt(0)}
                </div>
              </div>
              <div className="text-left min-w-0 truncate">
                <div className="text-xs font-semibold text-white capitalize truncate">{userName}</div>
                <div className="text-[10px] text-zinc-400 group-hover:text-cyan-400 transition truncate">
                  Go Beyond with Astra
                </div>
              </div>
            </div>
            <Settings className="w-4 h-4 text-zinc-400 group-hover:text-white transition shrink-0" />
          </div>

          {/* Upgrade Plan Card */}
          <button
            onClick={() => setIsUpgradeOpen(true)}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 hover:border-cyan-400 text-cyan-400 hover:text-white text-xs font-medium transition"
          >
            <Sparkles className="w-3.5 h-3.5 shrink-0" />
            <span>Upgrade to Pro</span>
          </button>
        </div>
      </aside>

      {/* ─── 2. MAIN WORKSPACE CONTAINER ─── */}
      <main className="flex-1 min-w-0 max-w-full flex flex-col h-full overflow-hidden relative bg-[#07090e]">
        {/* ─── GLOBAL TOP BAR (Clean, Zero-Duplicate Blueprint Design) ─── */}
        <header className="h-14 border-b border-white/[0.08] bg-[#090d16]/90 backdrop-blur-md px-2.5 sm:px-4 flex items-center justify-between shrink-0 z-20 w-full max-w-full overflow-hidden">
          <div className="flex items-center gap-1.5 sm:gap-2.5 min-w-0">
            {/* Mobile Hamburger Drawer Toggle */}
            <button
              onClick={() => setSidebarOpenMobile(true)}
              className="lg:hidden p-1.5 sm:p-2 rounded-xl text-zinc-300 hover:text-white hover:bg-white/[0.06] transition shrink-0"
              title="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Desktop Toggle Sidebar */}
            <button
              onClick={() => setSidebarCollapsedDesktop(!sidebarCollapsedDesktop)}
              className="hidden lg:flex p-1.5 sm:p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.06] transition shrink-0"
              title={sidebarCollapsedDesktop ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <PanelLeft className="w-4 h-4" />
            </button>

            {/* Search Conversations Input (screen_01_main_home.png) */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#0e1422] border border-white/10 text-xs text-zinc-400 focus-within:border-cyan-500/50 w-48 md:w-64 transition">
              <Search className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search conversations..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="bg-transparent text-xs text-white placeholder:text-zinc-500 focus:outline-none w-full min-w-0"
              />
              {searchFilter ? (
                <button
                  onClick={() => setSearchFilter('')}
                  className="text-zinc-400 hover:text-white shrink-0"
                  title="Clear search"
                >
                  <X className="w-3 h-3" />
                </button>
              ) : (
                <span className="text-[10px] text-zinc-500 font-mono bg-white/[0.06] px-1.5 py-0.5 rounded shrink-0">
                  Ctrl K
                </span>
              )}
            </div>

            {/* In active conversation: show title */}
            {!isHomeView && activeConversation && (
              <div className="hidden md:flex items-center gap-1.5 text-xs text-zinc-400 pl-2 border-l border-white/[0.08] min-w-0">
                <span className="truncate max-w-[140px] lg:max-w-[240px] text-zinc-300 font-medium">
                  {activeConversation.title}
                </span>
              </div>
            )}
          </div>

          {/* Right Top Actions (Clean, Zero Duplicates) */}
          <div className="flex items-center gap-1 sm:gap-2 shrink-0">
            {/* Model Selector Pill Dropdown (Unified Screen 02 Popover) */}
            <div className="relative shrink-0">
              <button
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl bg-[#0e1422] border border-white/10 hover:border-cyan-500/50 text-xs font-semibold text-white transition shadow-sm"
                title="Select model & tools"
              >
                <selectedModel.icon className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="hidden sm:inline">{selectedModel.name}</span>
                <span className="sm:hidden">{selectedModel.shortName}</span>
                <ChevronDown
                  className={`w-3 h-3 text-zinc-400 shrink-0 transition-transform ${
                    modelDropdownOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {/* Model & Tools Unified Popover (Exact match to screen_02_model_selection.png) */}
              {modelDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setModelDropdownOpen(false)}
                  />
                  <div
                    className="absolute top-12 right-0 w-[330px] sm:w-[370px] max-w-[92vw] bg-[#0a0f1d]/98 border border-cyan-500/30 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.85)] p-3.5 z-50 backdrop-blur-2xl max-h-[85vh] overflow-y-auto text-left"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.08]">
                      <div>
                        <div className="text-sm font-bold text-white tracking-tight">
                          {selectedModel.name}
                        </div>
                        <div className="text-[11px] text-zinc-400">
                          {selectedModel.desc}
                        </div>
                      </div>
                      <button
                        onClick={() => setModelDropdownOpen(false)}
                        className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
                        title="Close"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Models List */}
                    <div className="space-y-1">
                      {SUPPORTED_MODELS.map((mod) => {
                        const Icon = mod.icon;
                        const isSelected = selectedModelId === mod.id;
                        return (
                          <button
                            key={mod.id}
                            onClick={() => {
                              setSelectedModelId(mod.id);
                              setModelDropdownOpen(false);
                            }}
                            className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition ${
                              isSelected
                                ? 'bg-blue-600/25 border border-blue-500/40 text-white shadow-sm'
                                : 'text-zinc-300 hover:bg-white/[0.05] hover:text-white border border-transparent'
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <div
                                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${mod.color}`}
                              >
                                <Icon className="w-4 h-4" />
                              </div>
                              <div className="min-w-0">
                                <div className="text-xs font-semibold text-white truncate">
                                  {mod.name}
                                </div>
                                <div className="text-[10px] text-zinc-400 truncate">
                                  {mod.desc}
                                </div>
                              </div>
                            </div>
                            {isSelected && (
                              <Check className="w-4 h-4 text-cyan-400 shrink-0 ml-2" />
                            )}
                          </button>
                        );
                      })}

                      <button
                        onClick={() => {
                          setModelDropdownOpen(false);
                          setIsUpgradeOpen(true);
                        }}
                        className="w-full flex items-center justify-between px-3 py-1.5 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium transition"
                      >
                        <span>More models</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Model Selector Cyber Footer */}
                    <div className="border-t border-white/[0.08] mt-2.5 pt-2 flex items-center justify-between text-[11px] text-zinc-400 px-1">
                      <span className="flex items-center gap-1 text-cyan-400">
                        <Sparkles className="w-3 h-3" />
                        <span>GPT-6 Astra Active</span>
                      </span>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        Neural Core v6.2
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Global Auto-Speak Voice Toggle */}
            <button
              onClick={toggleAutoSpeak}
              className={`p-1.5 sm:p-2 rounded-xl transition shrink-0 ${
                isAutoSpeakEnabled
                  ? 'text-cyan-400 bg-cyan-500/20 ring-1 ring-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.06]'
              }`}
              title={
                isAutoSpeakEnabled
                  ? 'Auto Voice: ON (Jenna speaks responses aloud)'
                  : 'Auto Voice: OFF (Click to turn on automatic voice output)'
              }
            >
              {isAutoSpeakEnabled ? (
                <Volume2 className="w-4 h-4 animate-pulse text-cyan-400" />
              ) : (
                <VolumeX className="w-4 h-4" />
              )}
            </button>

            {/* Theme Toggle Button (Sun / Moon) */}
            <button
              onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
              className="p-1.5 sm:p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.06] transition shrink-0"
              title="Toggle theme mode"
            >
              {themeMode === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>

            {/* Apps / Explore Grid Button */}
            <button
              onClick={() => setIsExploreOpen(true)}
              className="p-1.5 sm:p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.06] transition shrink-0"
              title="Explore capabilities"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>

            {/* Notifications Bell */}
            <button
              onClick={() => {
                setNotificationToast('All systems nominal. You are on Astra v6.2.');
                setTimeout(() => setNotificationToast(null), 3000);
              }}
              className="relative p-1.5 sm:p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.06] transition shrink-0"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500" />
            </button>

            {/* User Profile Avatar (Opens Settings modal) */}
            <div
              onClick={() => setIsSettingsOpen(true)}
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-500 p-[1.5px] cursor-pointer shrink-0 hover:ring-2 hover:ring-cyan-400/50 transition shadow-md"
              title={`Logged in as ${userName} · Click for Settings`}
            >
              <div className="w-full h-full rounded-full bg-[#0c101b] flex items-center justify-center text-[10px] sm:text-xs font-bold text-white uppercase">
                {userName.charAt(0)}
              </div>
            </div>
          </div>
        </header>

        {/* Floating Notification Toast */}
        {notificationToast && (
          <div className="absolute top-16 right-4 z-50 px-4 py-2 rounded-xl bg-[#0e1424]/95 border border-cyan-500/40 text-xs text-white shadow-2xl backdrop-blur-xl flex items-center gap-2">
            <Check className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span>{notificationToast}</span>
          </div>
        )}

        {/* ─── 3. WORKSPACE CONTENT AREA ─── */}
        <div className="flex-1 overflow-hidden relative flex flex-col min-w-0 max-w-full">
          {isHomeView ? (
            /* ─────────────────────────────────────────────────────────────
               STATE A: HOME / EMPTY STATE (Matching Astra Blueprint Design)
               ───────────────────────────────────────────────────────────── */
            <div className="flex-1 overflow-y-auto relative flex flex-col justify-between items-center text-center px-3 sm:px-6 py-4 sm:py-8 w-full max-w-full min-w-0">
              {/* Planetary Canvas Background */}
              <AstraPlanetaryBackground />

              <div className="w-full max-w-3xl mx-auto my-auto relative z-10 flex flex-col items-center min-w-0">
                {/* Cyberpunk Animated Anime Girl Jenna Hero */}
                <AstraAnimatedJenna
                  mode="hero"
                  state={isThinking ? 'thinking' : speakingMsgId ? 'speaking' : 'idle'}
                  onTriggerVoice={() => setIsVoiceModalOpen(true)}
                />

                {/* Greeting & Subheading */}
                <h1 className="text-xl sm:text-2xl md:text-3xl font-bold tracking-tight text-white mb-1.5 sm:mb-2">
                  Good to see you, <span className="capitalize">{userName}</span> 👋
                </h1>
                <p className="text-xs sm:text-sm md:text-base text-zinc-400 max-w-md px-2">
                  What would you like to explore today?
                </p>

                {/* Centered Composer */}
                <div className="w-full max-w-2xl mt-4 sm:mt-8 min-w-0">
                  <div className="bg-[#0f1523]/90 border border-white/15 rounded-2xl sm:rounded-3xl p-2.5 sm:p-4 shadow-xl backdrop-blur-xl focus-within:border-cyan-500/50 transition-all">
                    {/* Attachment Chips */}
                    {attachedFiles.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2 px-1">
                        {attachedFiles.map((f, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/[0.08] border border-white/10 text-xs text-cyan-300 max-w-full"
                          >
                            {f.dataUrl ? (
                              <img
                                src={f.dataUrl}
                                alt={f.name}
                                className="w-5 h-5 rounded object-cover border border-cyan-500/40 shrink-0"
                              />
                            ) : (
                              <Paperclip className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
                            )}
                            <span className="truncate max-w-[130px] text-white font-medium">{f.name}</span>
                            <span className="text-[10px] text-zinc-400 font-mono shrink-0">({f.size})</span>
                            <button
                              onClick={() =>
                                setAttachedFiles((prev) => prev.filter((_, i) => i !== idx))
                              }
                              className="text-zinc-400 hover:text-white ml-1 shrink-0 p-0.5"
                              title="Remove attachment"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Textarea */}
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={handleInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder="Message Jenna..."
                      rows={1}
                      className="w-full bg-transparent text-xs sm:text-sm sm:text-base text-white placeholder:text-zinc-500 focus:outline-none resize-none px-1.5 py-1 max-h-36 min-w-0"
                    />

                    {/* Composer Action Toolbar (Matching Blueprint screen_01_main_home.png) */}
                    <div className="relative flex items-center justify-between mt-2 sm:mt-3 pt-2 border-t border-white/[0.08] gap-1 w-full min-w-0">
                      {/* Left: Quick Tools & Toggles */}
                      <div className="flex items-center gap-1 sm:gap-1.5 min-w-0 overflow-x-auto no-scrollbar">
                        {/* Plus button & action popover */}
                        <div className="relative shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setPlusMenuOpen(!plusMenuOpen);
                            }}
                            className={`p-1.5 rounded-lg transition shrink-0 ${
                              plusMenuOpen
                                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                                : 'text-zinc-400 hover:text-white hover:bg-white/[0.08]'
                            }`}
                            title="Add attachments, research & tools"
                          >
                            <Plus className={`w-4 h-4 transition-transform duration-200 ${plusMenuOpen ? 'rotate-45 text-cyan-400' : ''}`} />
                          </button>
                        </div>



                        {/* Active Mode Badges */}
                        {guidedLearningActive && (
                          <button
                            onClick={() => setGuidedLearningActive(false)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[11px] font-medium hover:bg-emerald-500/30 transition shrink-0"
                            title="Guided Learning active. Click to disable."
                          >
                            <GraduationCap className="w-3.5 h-3.5" />
                            <span>Guided Learning</span>
                            <X className="w-3 h-3 ml-0.5 text-zinc-400 hover:text-white" />
                          </button>
                        )}
                        {deepResearchActive && (
                          <button
                            onClick={() => setDeepResearchActive(false)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[11px] font-medium hover:bg-purple-500/30 transition shrink-0"
                            title="Deep Research active. Click to disable."
                          >
                            <Compass className="w-3.5 h-3.5" />
                            <span>Deep Research</span>
                            <X className="w-3 h-3 ml-0.5 text-zinc-400 hover:text-white" />
                          </button>
                        )}
                        {!personalIntelligenceActive && (
                          <span
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-zinc-800/80 text-zinc-400 border border-zinc-700 text-[11px] font-medium shrink-0"
                            title="Private Mode: Long-term memory query is disabled."
                          >
                            <span>Private Mode</span>
                          </span>
                        )}
                      </div>

                      {/* Right: Mic & Send */}
                      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                        <button
                          onClick={() => setIsVoiceModalOpen(true)}
                          className="p-1.5 sm:p-2 rounded-full text-zinc-400 hover:text-white hover:bg-white/[0.08] transition"
                          title="Voice mode"
                        >
                          <Mic className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleSendMessage()}
                          disabled={!input.trim() && attachedFiles.length === 0}
                          className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-white shadow-[0_0_15px_rgba(6,182,212,0.4)] transition transform active:scale-95 shrink-0"
                          title="Send message"
                        >
                          <ArrowUp className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* ─── CYBERPUNK INSPIRATION DECK (Non-duplicate Prompt Starters) ─── */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3 w-full max-w-3xl mt-6 sm:mt-8 min-w-0">
                  {CAPABILITY_CARDS.slice(0, 4).map((card, idx) => {
                    const CardIcon = card.icon;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(card.prompt)}
                        className="flex flex-col items-start p-3 rounded-2xl bg-[#0c111e]/90 hover:bg-[#121828] border border-white/10 hover:border-cyan-500/50 text-left transition transform hover:-translate-y-1 shadow-lg hover:shadow-[0_0_20px_rgba(6,182,212,0.25)] backdrop-blur-md w-full min-w-0 overflow-hidden group"
                      >
                        <div className="p-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mb-2 shrink-0 group-hover:scale-110 transition-transform">
                          <CardIcon className="w-3.5 h-3.5" />
                        </div>
                        <div className="text-xs font-semibold text-white mb-0.5 truncate w-full group-hover:text-cyan-300 transition-colors">
                          {card.title}
                        </div>
                        <div className="text-[10px] text-zinc-400 line-clamp-2 w-full">
                          {card.subtitle}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Cyberpunk Live System Status HUD */}
                <div className="mt-4 flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-[10px] text-zinc-400 font-mono">
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Neural: GPT-6 Astra</span>
                  </span>
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
                    <span>TTS: Natural Warm Female</span>
                  </span>
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    <span>Latency: 18ms</span>
                  </span>
                </div>
              </div>

              {/* Bottom Slogan Branding */}
              <div className="text-[9px] sm:text-[10px] tracking-[0.2em] sm:tracking-[0.25em] font-semibold text-zinc-500 uppercase mt-6 sm:mt-8 mb-2 relative z-10 shrink-0">
                BIGGER IDEAS. BRIGHTER POSSIBILITIES.
              </div>
            </div>
          ) : (
            /* ─────────────────────────────────────────────────────────────
               STATE B: ACTIVE CONVERSATION VIEW (Full Streaming & Chat)
               ───────────────────────────────────────────────────────────── */
            <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0 max-w-full">
              {/* Messages Scroll Area */}
              <div className="flex-1 overflow-y-auto px-2.5 sm:px-6 py-4 sm:py-6 space-y-4 sm:space-y-6 w-full max-w-full min-w-0">
                <div className="max-w-3xl mx-auto w-full space-y-4 sm:space-y-6 min-w-0">
                  {/* Cyberpunk Animated Companion Banner */}
                  <AstraAnimatedJenna
                    mode="chat-banner"
                    state={isThinking ? 'thinking' : speakingMsgId ? 'speaking' : 'idle'}
                    onTriggerVoice={() => setIsVoiceModalOpen(true)}
                  />

                  {messages.map((msg, index) => {
                    const isUser = msg.role === 'user';
                    const isCopied = copiedMsgId === msg.id;
                    const isSpeaking = speakingMsgId === msg.id;

                    return (
                      <div
                        key={msg.id || index}
                        className={`flex gap-2.5 sm:gap-4 w-full min-w-0 ${isUser ? 'justify-end' : 'justify-start'}`}
                      >
                        {/* Assistant Avatar */}
                        {!isUser && (
                          <div className="shrink-0 mt-0.5">
                            <AstraAnimatedJenna
                              mode="avatar"
                              state={
                                isThinking && index === messages.length - 1
                                  ? 'thinking'
                                  : isSpeaking
                                  ? 'speaking'
                                  : 'idle'
                              }
                            />
                          </div>
                        )}

                        {/* Message Bubble Container */}
                        <div
                          className={`flex flex-col min-w-0 max-w-[88%] sm:max-w-[80%] ${
                            isUser ? 'items-end' : 'items-start'
                          }`}
                        >
                          {/* Attached files chip in user message */}
                          {isUser && msg.metadata?.attachments && msg.metadata.attachments.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-2 justify-end">
                              {msg.metadata.attachments.map((f: any, i: number) =>
                                f.dataUrl ? (
                                  <div
                                    key={i}
                                    className="relative group rounded-2xl overflow-hidden border border-cyan-500/40 shadow-lg bg-black/60"
                                  >
                                    <img
                                      src={f.dataUrl}
                                      alt={f.name}
                                      className="w-24 h-24 sm:w-28 sm:h-28 object-cover hover:scale-105 transition duration-200"
                                    />
                                    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent px-2 py-1">
                                      <p className="text-[10px] text-zinc-200 truncate max-w-[95px]">
                                        {f.name}
                                      </p>
                                    </div>
                                  </div>
                                ) : (
                                  <div
                                    key={i}
                                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-white/10 text-xs text-cyan-300 max-w-full"
                                  >
                                    <Paperclip className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
                                    <span className="truncate max-w-[140px] text-white font-medium">
                                      {f.name}
                                    </span>
                                    {f.size && (
                                      <span className="text-[10px] text-zinc-400 font-mono">
                                        ({f.size})
                                      </span>
                                    )}
                                  </div>
                                )
                              )}
                            </div>
                          )}

                          {/* Bubble content */}
                          <div
                            className={`rounded-2xl px-3.5 py-2.5 sm:px-4 sm:py-3 text-xs sm:text-sm leading-relaxed min-w-0 max-w-full overflow-hidden break-words ${
                              isUser
                                ? 'bg-blue-600 text-white shadow-[0_4px_16px_rgba(37,99,235,0.25)]'
                                : 'bg-[#0e1424] border border-white/[0.08] text-zinc-200 shadow-lg'
                            }`}
                          >
                            {isUser ? (
                              <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                            ) : msg.content ? (
                              <MarkdownRenderer
                                content={msg.content}
                                onCopyCode={handleCopyCode}
                                copiedCodeId={copiedCodeId}
                              />
                            ) : isThinking ? (
                              <div className="flex items-center gap-2 py-1 text-xs text-cyan-400">
                                <Sparkles className="w-3.5 h-3.5 animate-spin shrink-0" />
                                <span>Thinking & analyzing...</span>
                              </div>
                            ) : null}
                          </div>

                          {/* Assistant Message Action Toolbar */}
                          {!isUser && msg.content && (
                            <div className="flex items-center gap-1 mt-1.5 text-zinc-400">
                              {/* Copy */}
                              <button
                                onClick={() => handleCopyText(msg.content, msg.id)}
                                className="p-1 rounded-md hover:text-white hover:bg-white/[0.06] transition"
                                title="Copy response"
                              >
                                {isCopied ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>

                              {/* Read aloud (TTS) */}
                              <button
                                onClick={() => handleToggleSpeak(msg.id, msg.content)}
                                className={`p-1 rounded-md transition ${
                                  isSpeaking
                                    ? 'text-cyan-400 bg-cyan-500/10'
                                    : 'hover:text-white hover:bg-white/[0.06]'
                                }`}
                                title={isSpeaking ? 'Stop reading' : 'Read aloud'}
                              >
                                {isSpeaking ? (
                                  <VolumeX className="w-3.5 h-3.5" />
                                ) : (
                                  <Volume2 className="w-3.5 h-3.5" />
                                )}
                              </button>

                              {/* Regenerate (if last message) */}
                              {index === messages.length - 1 && !isStreaming && (
                                <button
                                  onClick={() => {
                                    const prevUser = [...messages]
                                      .reverse()
                                      .find((m) => m.role === 'user');
                                    if (prevUser) handleSendMessage(prevUser.content);
                                  }}
                                  className="p-1 rounded-md hover:text-white hover:bg-white/[0.06] transition"
                                  title="Regenerate"
                                >
                                  <RotateCcw className="w-3.5 h-3.5" />
                                </button>
                              )}

                              {/* Thumbs up */}
                              <button
                                onClick={() =>
                                  setFeedback((prev) => ({ ...prev, [msg.id]: 'up' }))
                                }
                                className={`p-1 rounded-md transition ${
                                  feedback[msg.id] === 'up'
                                    ? 'text-emerald-400'
                                    : 'hover:text-white hover:bg-white/[0.06]'
                                }`}
                                title="Good response"
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>

                              {/* Thumbs down */}
                              <button
                                onClick={() =>
                                  setFeedback((prev) => ({ ...prev, [msg.id]: 'down' }))
                                }
                                className={`p-1 rounded-md transition ${
                                  feedback[msg.id] === 'down'
                                    ? 'text-rose-400'
                                    : 'hover:text-white hover:bg-white/[0.06]'
                                }`}
                                title="Bad response"
                              >
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                        </div>

                        {/* User Avatar */}
                        {isUser && (
                          <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-gradient-to-tr from-pink-500 to-indigo-600 p-[1.5px] shrink-0 mt-1">
                            <div className="w-full h-full rounded-full bg-[#0c101b] flex items-center justify-center text-[9px] sm:text-[10px] font-bold text-white uppercase">
                              {userName.charAt(0)}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* ─── BOTTOM STICKY COMPOSER (Active Chat) ─── */}
              <div className="border-t border-white/[0.08] bg-[#090d16]/90 backdrop-blur-xl px-2.5 sm:px-6 py-2.5 sm:py-3 shrink-0 w-full max-w-full">
                <div className="max-w-3xl mx-auto w-full min-w-0">
                  <div className="bg-[#0f1523] border border-white/10 rounded-2xl p-2 sm:p-3 focus-within:border-cyan-500/50 shadow-xl transition-all">
                    {/* Attachment Chips */}
                    {attachedFiles.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2 px-1">
                        {attachedFiles.map((f, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/[0.08] border border-white/10 text-xs text-cyan-300 max-w-full"
                          >
                            {f.dataUrl ? (
                              <img
                                src={f.dataUrl}
                                alt={f.name}
                                className="w-5 h-5 rounded object-cover border border-cyan-500/40 shrink-0"
                              />
                            ) : (
                              <Paperclip className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
                            )}
                            <span className="truncate max-w-[130px] text-white font-medium">{f.name}</span>
                            <span className="text-[10px] text-zinc-400 font-mono shrink-0">({f.size})</span>
                            <button
                              onClick={() =>
                                setAttachedFiles((prev) => prev.filter((_, i) => i !== idx))
                              }
                              className="text-zinc-400 hover:text-white ml-1 shrink-0 p-0.5"
                              title="Remove attachment"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Textarea */}
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={handleInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder="Message Jenna..."
                      rows={1}
                      className="w-full bg-transparent text-xs sm:text-sm text-white placeholder:text-zinc-500 focus:outline-none resize-none px-1.5 py-1 max-h-36 min-w-0"
                    />

                    {/* Controls Row (Matching Blueprint screen_01_main_home.png) */}
                    <div className="relative flex items-center justify-between mt-2 pt-2 border-t border-white/[0.06] gap-1">
                      {/* Left: Tools & Toggles */}
                      <div className="flex items-center gap-1 sm:gap-1.5 min-w-0 overflow-x-auto no-scrollbar">
                        {/* Plus button & action popover */}
                        <div className="relative shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setPlusMenuOpen(!plusMenuOpen);
                            }}
                            className={`p-1 sm:p-1.5 rounded-lg transition shrink-0 ${
                              plusMenuOpen
                                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                                : 'text-zinc-400 hover:text-white hover:bg-white/[0.08]'
                            }`}
                            title="Add attachments, research & tools"
                          >
                            <Plus className={`w-4 h-4 transition-transform duration-200 ${plusMenuOpen ? 'rotate-45 text-cyan-400' : ''}`} />
                          </button>
                        </div>



                        {/* Active Mode Badges */}
                        {guidedLearningActive && (
                          <button
                            onClick={() => setGuidedLearningActive(false)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[11px] font-medium hover:bg-emerald-500/30 transition shrink-0"
                            title="Guided Learning active. Click to disable."
                          >
                            <GraduationCap className="w-3.5 h-3.5" />
                            <span>Guided Learning</span>
                            <X className="w-3 h-3 ml-0.5 text-zinc-400 hover:text-white" />
                          </button>
                        )}
                        {deepResearchActive && (
                          <button
                            onClick={() => setDeepResearchActive(false)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[11px] font-medium hover:bg-purple-500/30 transition shrink-0"
                            title="Deep Research active. Click to disable."
                          >
                            <Compass className="w-3.5 h-3.5" />
                            <span>Deep Research</span>
                            <X className="w-3 h-3 ml-0.5 text-zinc-400 hover:text-white" />
                          </button>
                        )}
                        {!personalIntelligenceActive && (
                          <span
                            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-zinc-800/80 text-zinc-400 border border-zinc-700 text-[11px] font-medium shrink-0"
                            title="Private Mode: Long-term memory query is disabled."
                          >
                            <span>Private Mode</span>
                          </span>
                        )}
                      </div>

                      {/* Right: Auto-Speak / Mic / Stop / Send */}
                      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                        <button
                          type="button"
                          onClick={toggleAutoSpeak}
                          className={`p-1 sm:p-1.5 rounded-full transition ${
                            isAutoSpeakEnabled
                              ? 'text-cyan-300 bg-cyan-500/20 ring-1 ring-cyan-500/50 shadow-[0_0_8px_rgba(6,182,212,0.4)]'
                              : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.08]'
                          }`}
                          title={
                            isAutoSpeakEnabled
                              ? 'Auto-Speak: ON (Jenna automatically speaks out loud)'
                              : 'Auto-Speak: OFF (Click to let Jenna speak aloud)'
                          }
                        >
                          {isAutoSpeakEnabled ? (
                            <Volume2 className="w-4 h-4 animate-pulse text-cyan-400" />
                          ) : (
                            <VolumeX className="w-4 h-4" />
                          )}
                        </button>

                        <button
                          onClick={() => setIsVoiceModalOpen(true)}
                          className="p-1 sm:p-1.5 rounded-full text-zinc-400 hover:text-white hover:bg-white/[0.08] transition"
                          title="Voice mode"
                        >
                          <Mic className="w-4 h-4" />
                        </button>

                        {isStreaming ? (
                          <button
                            onClick={handleStopStreaming}
                            className="w-7 h-7 rounded-full bg-rose-600 hover:bg-rose-500 flex items-center justify-center text-white shadow-[0_0_12px_rgba(225,29,72,0.5)] transition active:scale-95 shrink-0"
                            title="Stop generating"
                          >
                            <Square className="w-3 h-3 fill-white" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleSendMessage()}
                            disabled={!input.trim() && attachedFiles.length === 0}
                            className="w-7 h-7 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-white shadow-[0_0_12px_rgba(6,182,212,0.4)] transition active:scale-95 shrink-0"
                            title="Send message"
                          >
                            <ArrowUp className="w-3.5 h-3.5 stroke-[2.5]" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Fine Print Footer */}
                  <div className="text-center text-[10px] text-zinc-500 mt-1.5">
                    Jenna AI can make mistakes. Verify important info.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ─── 4. MODALS & OVERLAYS ─── */}

      {/* A. Delete Confirmation Dialog */}
      {deletingConvId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md"
            onClick={() => setDeletingConvId(null)}
          />
          <div className="relative w-full max-w-sm bg-[#0c111e] border border-rose-500/30 rounded-2xl p-5 shadow-2xl z-10 text-center">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto mb-3">
              <Trash2 className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Delete Conversation?</h4>
            <p className="text-xs text-zinc-400 mb-5">
              This will permanently delete this conversation history and cannot be undone.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setDeletingConvId(null)}
                className="px-4 py-1.5 rounded-xl border border-white/10 text-xs text-zinc-300 hover:bg-white/[0.06] transition"
              >
                Cancel
              </button>
              <button
                onClick={() => confirmDelete(deletingConvId)}
                className="px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/30 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* B. Voice Modal */}
      <AstraVoiceModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        isListening={voiceListening}
        onToggleListening={() => setVoiceListening(!voiceListening)}
        transcript={voiceTranscript}
        assistantSpeaking={voiceSpeaking}
      />

      {/* C. Settings Modal (All 9 Tabs) */}
      <AstraSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        userName={userName}
      />

      {/* D. Explore Modal */}
      <AstraExploreModal
        isOpen={isExploreOpen}
        onClose={() => setIsExploreOpen(false)}
        onSelectTopic={(prompt) => {
          setIsExploreOpen(false);
          handleSendMessage(prompt);
        }}
      />

      {/* E. Image Generation Modal */}
      <AstraImageGenModal
        isOpen={isImageGenOpen}
        onClose={() => setIsImageGenOpen(false)}
        onUseImagePrompt={(prompt) => {
          setIsImageGenOpen(false);
          handleSendMessage(prompt);
        }}
      />

      {/* F. Upgrade Modal */}
      <AstraUpgradeModal
        isOpen={isUpgradeOpen}
        onClose={() => setIsUpgradeOpen(false)}
        userName={userName}
      />

      {/* I. Interactive Canvas Workspace Modal (ChatGPT & Gemini) */}
      <AstraCanvasModal
        isOpen={isCanvasModalOpen}
        onClose={() => setIsCanvasModalOpen(false)}
        onSendToChat={(prompt) => {
          setInput((prev) => (prev ? `${prev}\n\n${prompt}` : prompt));
          textareaRef.current?.focus();
        }}
      />

      {/* J. Jenna 3D Avatar & Persona Studio */}
      <AstraAvatarModal
        isOpen={isAvatarModalOpen}
        onClose={() => setIsAvatarModalOpen(false)}
        activePersonaId={activePersona.id}
        onApplyPersona={handleApplyPersona}
      />

      {/* K. NotebookLM Study & Research Studio */}
      <AstraNotebooksModal
        isOpen={isNotebooksModalOpen}
        onClose={() => setIsNotebooksModalOpen(false)}
        onInsertNotebookContent={handleInsertNotebookContent}
      />

      {/* L. Sora & Veo 2 Video Studio */}
      <AstraVideoModal
        isOpen={isVideoModalOpen}
        onClose={() => setIsVideoModalOpen(false)}
        onGenerateVideoStoryboard={(prompt) => {
          handleSendMessage(prompt);
        }}
      />

      {/* M. Suno & Lyria AI Music Studio */}
      <AstraMusicModal
        isOpen={isMusicModalOpen}
        onClose={() => setIsMusicModalOpen(false)}
        onGenerateMusicComposition={(prompt) => {
          handleSendMessage(prompt);
        }}
      />

      {/* N. Socratic Guided Learning Studio */}
      <AstraGuidedLearningModal
        isOpen={isGuidedLearningModalOpen}
        onClose={() => setIsGuidedLearningModalOpen(false)}
        onStartGuidedLearning={handleStartGuidedLearning}
      />

      {/* O. Exact Plus Menu (ChatGPT + Gemini Hybrid Bottom Sheet) */}
      <AstraPlusMenu
        isOpen={plusMenuOpen}
        onClose={() => setPlusMenuOpen(false)}
        onUploadFile={() => fileInputRef.current?.click()}
        onUploadImage={() => imageInputRef.current?.click()}
        onOpenCamera={() => cameraInputRef.current?.click()}
        onOpenAvatar={() => setIsAvatarModalOpen(true)}
        onOpenDrive={() => window.open('https://drive.google.com/drive/home', '_blank', 'noopener,noreferrer')}
        onOpenNotebooks={() => setIsNotebooksModalOpen(true)}
        onOpenCanvas={() => setIsCanvasModalOpen(true)}
        onOpenImageGen={() => setIsImageGenOpen(true)}
        onOpenVideoGen={() => setIsVideoModalOpen(true)}
        onOpenMusicGen={() => setIsMusicModalOpen(true)}
        onOpenGuidedLearning={() => setIsGuidedLearningModalOpen(true)}
        onOpenVoice={() => setIsVoiceModalOpen(true)}
        onInsertPrompt={(prompt) => {
          setInput((prev) => (prev ? `${prev}\n${prompt}` : prompt));
          textareaRef.current?.focus();
        }}
        deepResearchActive={deepResearchActive}
        onToggleDeepResearch={() => setDeepResearchActive(!deepResearchActive)}
        personalIntelligenceActive={personalIntelligenceActive}
        onTogglePersonalIntelligence={() => setPersonalIntelligenceActive(!personalIntelligenceActive)}
      />
    </div>
  );
}
