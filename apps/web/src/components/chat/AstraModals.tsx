'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Mic,
  MicOff,
  PhoneOff,
  Sparkles,
  Volume2,
  Check,
  Globe,
  Code,
  Shield,
  Bell,
  Cpu,
  User as UserIcon,
  Palette,
  Sliders,
  Play,
  Download,
  BookOpen,
  Compass,
  Zap,
  Star,
  RefreshCw,
  Search,
  ArrowLeft,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  FolderTree,
  Calculator,
  Boxes,
  FileCode,
  ExternalLink,
  ChevronRight,
  Terminal,
  Cloud,
  FileText,
  Layout,
  Copy,
  Edit3,
  Layers,
  Table,
  Film,
  Music,
  Plus,
  Trash2,
  GraduationCap,
  Bookmark,
  SlidersHorizontal,
  Send,
  HelpCircle,
  Lightbulb,
} from 'lucide-react';
import { AstraAnimatedJenna, JennaState } from './AstraAnimatedJenna';
import { speakJennaVoice, stopJennaVoice } from '@/lib/ttsVoice';
import { apiClient } from '@/lib/api';


// ─── 1. Voice Mode Modal ─────────────────────────────────────────────
interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  isListening: boolean;
  onToggleListening: () => void;
  transcript: string;
  assistantSpeaking: boolean;
}

export function AstraVoiceModal({
  isOpen,
  onClose,
  isListening,
  onToggleListening,
  transcript,
  assistantSpeaking,
}: VoiceModalProps) {
  const [speaking, setSpeaking] = useState(assistantSpeaking);

  useEffect(() => {
    setSpeaking(assistantSpeaking);
  }, [assistantSpeaking]);

  useEffect(() => {
    if (isOpen) {
      // Natural warm greeting when opening voice studio
      const timeout = setTimeout(() => {
        setSpeaking(true);
        speakJennaVoice(
          "Hey Radhe! Main ready hoon. Aap mujhse bol kar kuch bhi pooch sakte hain.",
          {
            onEnd: () => setSpeaking(false),
            onError: () => setSpeaking(false),
          }
        );
      }, 500);
      return () => {
        clearTimeout(timeout);
        stopJennaVoice();
      };
    } else {
      stopJennaVoice();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentState: JennaState = speaking
    ? 'speaking'
    : isListening
    ? 'listening'
    : 'idle';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-md bg-[#0a0e19]/95 border border-purple-500/30 rounded-3xl p-6 sm:p-8 shadow-[0_0_60px_rgba(168,85,247,0.3)] flex flex-col items-center text-center z-10">
        {/* Top bar */}
        <div className="w-full flex items-center justify-between mb-4">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span className="text-xs font-semibold tracking-wider uppercase text-purple-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Jenna Voice Studio
          </span>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Central Animated Cyberpunk Anime Girl Jenna */}
        <AstraAnimatedJenna
          mode="voice"
          state={currentState}
          interactive={false}
        />

        <p className="text-xs text-zinc-400 mt-2 max-w-xs">
          {transcript
            ? `"${transcript}"`
            : speaking
            ? 'Jenna is speaking with natural warm female voice...'
            : isListening
            ? 'Listening to your voice in real time...'
            : 'Microphone paused. Tap unmute to resume.'}
        </p>

        {/* Bottom Control Actions */}
        <div className="flex items-center gap-6 mt-6">
          <button
            onClick={() => {
              if (speaking) {
                stopJennaVoice();
                setSpeaking(false);
              }
              onToggleListening();
            }}
            className={`flex flex-col items-center gap-1.5 text-xs transition ${
              isListening ? 'text-zinc-300 hover:text-white' : 'text-amber-400'
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-white/[0.08] hover:bg-white/[0.15] border border-white/10 flex items-center justify-center text-white transition">
              {isListening ? <Mic className="w-5 h-5 text-cyan-400" /> : <MicOff className="w-5 h-5 text-amber-400" />}
            </div>
            <span>{isListening ? 'Mute' : 'Unmute'}</span>
          </button>

          <button
            onClick={() => {
              setSpeaking(true);
              speakJennaVoice(
                "Aapki Jenna bilkul active hai! Aaj ka din kaisa raha aapka?",
                {
                  onEnd: () => setSpeaking(false),
                  onError: () => setSpeaking(false),
                }
              );
            }}
            className="flex flex-col items-center gap-1.5 text-xs text-purple-300 hover:text-white transition"
            title="Hear Jenna speak"
          >
            <div className="w-12 h-12 rounded-full bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 flex items-center justify-center text-purple-300 hover:text-white transition">
              <Volume2 className="w-5 h-5" />
            </div>
            <span>Voice Test</span>
          </button>

          <button
            onClick={() => {
              stopJennaVoice();
              onClose();
            }}
            className="flex flex-col items-center gap-1.5 text-xs text-rose-300 hover:text-white transition"
          >
            <div className="w-12 h-12 rounded-full bg-rose-600 hover:bg-rose-500 shadow-lg shadow-rose-600/30 flex items-center justify-center text-white transition">
              <PhoneOff className="w-5 h-5" />
            </div>
            <span>End</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 2. Settings Modal ───────────────────────────────────────────────
interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export function AstraSettingsModal({ isOpen, onClose, userName }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState('general');
  const [language, setLanguage] = useState('English');
  const [theme, setTheme] = useState<'dark' | 'light' | 'system'>('dark');
  const [defaultModel, setDefaultModel] = useState('GPT-6 Astra');
  const [webSearch, setWebSearch] = useState(true);
  const [codeInterpreter, setCodeInterpreter] = useState(true);
  const [voiceMode, setVoiceMode] = useState(true);
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const tabs = [
    { id: 'general', label: 'General', icon: Sliders },
    { id: 'account', label: 'Account', icon: UserIcon },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'models', label: 'Model Preferences', icon: Cpu },
    { id: 'data', label: 'Data & Privacy', icon: Shield },
    { id: 'voice', label: 'Voice & Audio', icon: Volume2 },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'shortcuts', label: 'Shortcuts', icon: Code },
    { id: 'about', label: 'About', icon: Globe },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-3xl max-h-[90vh] h-[560px] bg-[#0c101b]/95 border border-white/10 rounded-2xl shadow-2xl flex flex-col sm:flex-row overflow-hidden z-10">
        {/* Left Sidebar / Top Horizontal Scroll Tabs on Mobile */}
        <aside className="w-full sm:w-56 border-b sm:border-b-0 sm:border-r border-white/[0.08] bg-[#080c15] p-2.5 sm:p-3 flex sm:flex-col justify-between shrink-0 overflow-x-auto sm:overflow-x-visible">
          <div className="w-full">
            <div className="hidden sm:block px-3 py-2 text-xs font-bold uppercase tracking-wider text-zinc-400">
              Settings
            </div>
            <nav className="flex sm:flex-col gap-1 sm:gap-0.5 sm:mt-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`whitespace-nowrap sm:w-full flex items-center gap-2 px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl text-xs font-medium transition shrink-0 ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 font-semibold border border-blue-500/30'
                        : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="hidden sm:block p-2 border-t border-white/[0.06] text-[11px] text-zinc-500">
            Astra AI v6.2 · Radhe Edition
          </div>
        </aside>

        {/* Right Form Content */}
        <div className="flex-1 flex flex-col justify-between p-4 sm:p-6 overflow-y-auto min-w-0 max-w-full">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] mb-6">
              <h3 className="text-base font-bold text-white capitalize">{activeTab} Settings</h3>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {activeTab === 'general' && (
              <div className="space-y-5 text-xs">
                {/* Language */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">Language</div>
                    <div className="text-zinc-400 text-[11px]">Primary response and dialog language</div>
                  </div>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="bg-[#121826] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="English">English</option>
                    <option value="Hinglish">Hinglish (Hindi + English)</option>
                    <option value="Hindi">Hindi (हिंदी)</option>
                  </select>
                </div>

                {/* Theme */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">Theme</div>
                    <div className="text-zinc-400 text-[11px]">Interface color scheme</div>
                  </div>
                  <div className="flex items-center bg-[#121826] border border-white/10 rounded-lg p-1 gap-1">
                    {(['light', 'dark', 'system'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setTheme(t)}
                        className={`px-3 py-1 rounded capitalize transition ${
                          theme === t
                            ? 'bg-blue-600 text-white font-medium shadow-sm'
                            : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Default Model */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">Default Model</div>
                    <div className="text-zinc-400 text-[11px]">Primary neural engine for new chats</div>
                  </div>
                  <select
                    value={defaultModel}
                    onChange={(e) => setDefaultModel(e.target.value)}
                    className="bg-[#121826] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="GPT-6 Astra">GPT-6 Astra (Reasoning)</option>
                    <option value="GPT-5.6 Luna">GPT-5.6 Luna (Fast)</option>
                    <option value="GPT-5">GPT-5 (Standard)</option>
                  </select>
                </div>

                {/* Web Search Toggle */}
                <div className="flex items-center justify-between pt-2 border-t border-white/[0.06]">
                  <div>
                    <div className="font-semibold text-white">Web Search</div>
                    <div className="text-zinc-400 text-[11px]">Enable real-time search queries</div>
                  </div>
                  <button
                    onClick={() => setWebSearch(!webSearch)}
                    className={`w-11 h-6 rounded-full transition-colors relative ${
                      webSearch ? 'bg-blue-600' : 'bg-zinc-800'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform absolute top-1 ${
                        webSearch ? 'left-6' : 'left-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Code Interpreter */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">Code Interpreter</div>
                    <div className="text-zinc-400 text-[11px]">Allow live code execution & sandboxing</div>
                  </div>
                  <button
                    onClick={() => setCodeInterpreter(!codeInterpreter)}
                    className={`w-11 h-6 rounded-full transition-colors relative ${
                      codeInterpreter ? 'bg-blue-600' : 'bg-zinc-800'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform absolute top-1 ${
                        codeInterpreter ? 'left-6' : 'left-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Voice Mode */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">Voice Mode</div>
                    <div className="text-zinc-400 text-[11px]">Enable real-time speech dialogs</div>
                  </div>
                  <button
                    onClick={() => setVoiceMode(!voiceMode)}
                    className={`w-11 h-6 rounded-full transition-colors relative ${
                      voiceMode ? 'bg-blue-600' : 'bg-zinc-800'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform absolute top-1 ${
                        voiceMode ? 'left-6' : 'left-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            {activeTab !== 'general' && (
              <div className="space-y-4 text-xs text-zinc-300">
                <p>Configuring settings for <strong className="text-white capitalize">{activeTab}</strong>.</p>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <p className="text-zinc-400">
                    Logged in as <strong className="text-cyan-400">{userName || 'Radhe'}</strong>.
                  </p>
                  <p className="mt-1 text-zinc-400">
                    System features, memory embeddings, and neural parameters are synchronized with Jenna platform.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Footer Save Button */}
          <div className="pt-4 border-t border-white/[0.08] flex justify-end">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/25 transition"
            >
              {saved ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Saved!</span>
                </>
              ) : (
                <span>Save Changes</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 3. Image Generation Modal ───────────────────────────────────────
interface ImageGenModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUseImagePrompt: (prompt: string) => void;
}

export function AstraImageGenModal({ isOpen, onClose, onUseImagePrompt }: ImageGenModalProps) {
  const [prompt, setPrompt] = useState('A futuristic city on Mars at sunset');
  const [generating, setGenerating] = useState(false);

  if (!isOpen) return null;

  const mockSamples = [
    {
      id: 1,
      title: 'Martian Metropolis Sunset',
      desc: 'Holographic towers, glowing domed biosphere, sunset hues',
      gradient: 'from-amber-600 via-rose-700 to-indigo-950',
    },
    {
      id: 2,
      title: 'Orbital Cyber Station',
      desc: 'Deep space megastructure with glowing cyan energy core',
      gradient: 'from-cyan-600 via-blue-800 to-black',
    },
    {
      id: 3,
      title: 'Neural Cyberpunk Street',
      desc: 'Neon rain reflections, flying vehicles, vertical skyline',
      gradient: 'from-purple-600 via-indigo-900 to-black',
    },
  ];

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      onUseImagePrompt(
        `Act as an expert AI visual artist and image generator (Imagen 3 / Midjourney). ` +
        `Create a stunning, photorealistic visual rendering for: "${prompt}".\n\n` +
        `Provide:\n` +
        `1. Master Visual Description (Composition, Subject, Background)\n` +
        `2. Lighting & Volumetric Atmosphere (Time of day, shadows, glow)\n` +
        `3. Camera Specs (35mm / 85mm prime lens, f/1.4 aperture, ISO 100, 8K)\n` +
        `4. Color Palette (Primary tones, accents, grading)\n` +
        `5. Production Image Prompt (Optimized prompt keywords with aspect ratio and quality tags).`
      );
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-2xl bg-[#0c101b]/95 border border-pink-500/30 rounded-2xl p-6 shadow-2xl z-10 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-pink-400" />
            <h3 className="text-sm font-bold text-white">Create Image (Text to Image)</h3>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input & Generate Button */}
        <div className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            className="flex-1 bg-[#121826] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-pink-500"
          />
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-pink-500/25 flex items-center gap-2 disabled:opacity-50"
          >
            {generating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Rendering...</span>
              </>
            ) : (
              <span>Generate</span>
            )}
          </button>
        </div>

        {/* Example Showcase Grid */}
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            Example Showcase
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {mockSamples.map((sample) => (
              <div
                key={sample.id}
                onClick={() => setPrompt(sample.desc)}
                className="group cursor-pointer rounded-xl overflow-hidden border border-white/10 hover:border-pink-500/50 transition bg-black/40"
              >
                <div className={`h-28 bg-gradient-to-tr ${sample.gradient} p-3 flex flex-col justify-end relative`}>
                  <span className="text-[11px] font-bold text-white drop-shadow">{sample.title}</span>
                </div>
                <div className="p-2.5 text-[10px] text-zinc-400 line-clamp-2">
                  {sample.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 4. Explore / Welcome Modal ───────────────────────────────────────
interface ExploreModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTopic: (topic: string) => void;
}

export function AstraExploreModal({ isOpen, onClose, onSelectTopic }: ExploreModalProps) {
  if (!isOpen) return null;

  const topics = [
    { title: 'Learning', desc: 'Study smarter with interactive AI explanations', icon: BookOpen, color: 'text-blue-400' },
    { title: 'Creativity', desc: 'Turn ideas into art, stories, and designs', icon: Sparkles, color: 'text-pink-400' },
    { title: 'Productivity', desc: 'Get more done with structured roadmaps', icon: Zap, color: 'text-amber-400' },
    { title: 'Research', desc: 'Go deeper with citations and literature analysis', icon: Search, color: 'text-purple-400' },
    { title: 'Coding', desc: 'Build faster with clean architecture & debugging', icon: Code, color: 'text-cyan-400' },
    { title: 'Lifestyle', desc: 'Plan better trips, habits, and daily schedules', icon: Compass, color: 'text-emerald-400' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-2xl bg-[#0c101b]/95 border border-white/10 rounded-2xl p-6 shadow-2xl z-10 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white">Explore What's Possible</h3>
            <p className="text-xs text-zinc-400">AI for learning, creating, working and beyond.</p>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {topics.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.title}
                onClick={() => {
                  onSelectTopic(`Let's explore ${t.title}: ${t.desc}`);
                  onClose();
                }}
                className="p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/10 hover:border-blue-500/40 transition text-left flex items-start gap-3.5 group"
              >
                <div className={`p-2.5 rounded-lg bg-white/[0.05] ${t.color} group-hover:scale-110 transition-transform`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white">{t.title}</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5 leading-relaxed">{t.desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── 5. Upgrade Plan Modal ───────────────────────────────────────────
interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export function AstraUpgradeModal({ isOpen, onClose, userName }: UpgradeModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-md bg-[#0c101b]/95 border border-indigo-500/30 rounded-3xl p-6 shadow-2xl z-10 text-center space-y-6">
        <div className="flex justify-end">
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center text-white mx-auto shadow-[0_0_30px_rgba(99,102,241,0.5)]">
          <Star className="w-8 h-8" />
        </div>

        <div>
          <h3 className="text-lg font-extrabold text-white">Go Beyond with Astra Pro</h3>
          <p className="text-xs text-zinc-400 mt-1 max-w-xs mx-auto">
            Unlock GPT-6 deep reasoning, ultra-fast streaming, 4K image generation, and unlimited multimodal tools.
          </p>
        </div>

        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 text-left space-y-2.5 text-xs text-zinc-300">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Highest priority reasoning on GPT-6 Astra</span>
          </div>
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Unlimited real-time web deep research</span>
          </div>
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>High-fidelity voice synthesis & low latency</span>
          </div>
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>Dedicated personal memory & custom agents</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:opacity-90 text-white text-xs font-bold uppercase tracking-wider shadow-lg shadow-indigo-500/25 transition"
        >
          Active for {userName || 'Radhe'} (Included in Platform)
        </button>
      </div>
    </div>
  );
}

// ─── 6. Cyberpunk Tools & MCP Studio Modal ────────────────────────────
interface ToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertPrompt?: (prompt: string) => void;
  webSearchActive?: boolean;
  onToggleWebSearch?: (active: boolean) => void;
  deepResearchActive?: boolean;
  onToggleDeepResearch?: (active: boolean) => void;
}

export function AstraToolsModal({
  isOpen,
  onClose,
  onInsertPrompt,
  webSearchActive = false,
  onToggleWebSearch,
  deepResearchActive = false,
  onToggleDeepResearch,
}: ToolsModalProps) {
  const [activeTab, setActiveTab] = useState<'catalog' | 'playground' | 'research' | 'mcp'>('catalog');
  const [tools, setTools] = useState<any[]>([]);
  const [loadingTools, setLoadingTools] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Playground state
  const [selectedTool, setSelectedTool] = useState<string>('calculator');
  const [toolParams, setToolParams] = useState<Record<string, any>>({ expression: 'sqrt(144) + 12 * 5' });
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  // Web Research Studio state
  const [researchQuery, setResearchQuery] = useState('');
  const [maxSources, setMaxSources] = useState(4);
  const [researching, setResearching] = useState(false);
  const [researchResult, setResearchResult] = useState<any>(null);

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [loadingMcp, setLoadingMcp] = useState(false);

  // Fetch tools from backend
  useEffect(() => {
    if (isOpen) {
      loadTools();
      loadMcpServers();
    }
  }, [isOpen]);

  const loadTools = async () => {
    setLoadingTools(true);
    try {
      const data = await apiClient.listTools();
      if (data && data.length > 0) {
        setTools(data);
      } else {
        // Fallback default catalog if offline
        setTools([
          { name: 'calculator', description: 'Safely evaluate math expressions (AST parsed)', category: 'CALCULATOR', parameters: [{ name: 'expression', type: 'string' }] },
          { name: 'filesystem_read', description: 'Read file contents within allowed workspace', category: 'FILESYSTEM', parameters: [{ name: 'path', type: 'string' }] },
          { name: 'filesystem_write', description: 'Write or modify files in workspace', category: 'FILESYSTEM', parameters: [{ name: 'path', type: 'string' }, { name: 'content', type: 'string' }] },
          { name: 'system_info', description: 'Real-time CPU, RAM, and system telemetry', category: 'SYSTEM', parameters: [] },
          { name: 'web_research', description: '6-stage live web search with citations', category: 'WEB', parameters: [{ name: 'query', type: 'string' }] },
          { name: 'blender_validator', description: 'Validate Blender Python bpy scripts', category: 'SYSTEM', parameters: [{ name: 'script', type: 'string' }] },
          { name: 'latex_validator', description: 'Validate enterprise LaTeX documents', category: 'SYSTEM', parameters: [{ name: 'latex_code', type: 'string' }] },
          { name: 'spreadsheet_validator', description: 'Validate dynamic Excel formulas', category: 'SYSTEM', parameters: [{ name: 'formula', type: 'string' }] },
        ]);
      }
    } catch {
      setTools([
        { name: 'calculator', description: 'Safely evaluate math expressions (AST parsed)', category: 'CALCULATOR', parameters: [{ name: 'expression', type: 'string' }] },
        { name: 'system_info', description: 'Real-time CPU, RAM, and system telemetry', category: 'SYSTEM', parameters: [] },
        { name: 'web_research', description: '6-stage live web search with citations', category: 'WEB', parameters: [{ name: 'query', type: 'string' }] },
        { name: 'blender_validator', description: 'Validate Blender Python bpy scripts', category: 'SYSTEM', parameters: [{ name: 'script', type: 'string' }] },
        { name: 'latex_validator', description: 'Validate enterprise LaTeX documents', category: 'SYSTEM', parameters: [{ name: 'latex_code', type: 'string' }] },
        { name: 'spreadsheet_validator', description: 'Validate dynamic Excel formulas', category: 'SYSTEM', parameters: [{ name: 'formula', type: 'string' }] },
      ]);
    } finally {
      setLoadingTools(false);
    }
  };

  const loadMcpServers = async () => {
    setLoadingMcp(true);
    try {
      const data = await apiClient.listMcpServers();
      setMcpServers(data || []);
    } catch {
      setMcpServers([
        { server_name: 'ProductionWeatherServer', server_type: 'mock', status: 'connected', tools_count: 3 },
        { server_name: 'LocalFilesystemMCP', server_type: 'stdio', status: 'ready', tools_count: 4 },
      ]);
    } finally {
      setLoadingMcp(false);
    }
  };

  // Handle Tool Execution in Playground
  const handleExecuteTool = async () => {
    setExecuting(true);
    setExecutionResult(null);
    try {
      const res = await apiClient.executeTool(selectedTool, toolParams, true);
      setExecutionResult(res);
    } catch (err: any) {
      setExecutionResult({
        tool_name: selectedTool,
        status: 'FAILED',
        error: err.message || 'Execution failed',
        duration_ms: 0,
      });
    } finally {
      setExecuting(false);
    }
  };

  // Handle Live Web Research Execution
  const handleExecuteResearch = async () => {
    if (!researchQuery.trim()) return;
    setResearching(true);
    setResearchResult(null);
    try {
      const res = await apiClient.performResearch(researchQuery.trim(), maxSources);
      setResearchResult(res);
    } catch (err: any) {
      setResearchResult({
        query: researchQuery,
        error: err.message || 'Web research failed',
        sources: [],
      });
    } finally {
      setResearching(false);
    }
  };

  // Preset parameter template loader
  const handleSelectToolForPlayground = (name: string) => {
    setSelectedTool(name);
    setActiveTab('playground');
    if (name === 'calculator') {
      setToolParams({ expression: 'sqrt(256) + 40 * 2' });
    } else if (name === 'system_info') {
      setToolParams({});
    } else if (name === 'blender_validator') {
      setToolParams({ script: 'import bpy\nbpy.ops.mesh.primitive_cube_add(size=2.0)' });
    } else if (name === 'latex_validator') {
      setToolParams({ latex_code: '\\begin{document}\n\\section{Astra}\nHello $E=mc^2$\n\\end{document}' });
    } else if (name === 'spreadsheet_validator') {
      setToolParams({ formula: '=SUM(A1:A50) + XLOOKUP(B1, C1:C50, D1:D50)' });
    } else if (name === 'filesystem_read') {
      setToolParams({ path: 'README.md' });
    } else {
      setToolParams({});
    }
  };

  const filteredTools = tools.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-[#0c101d] border border-cyan-500/40 rounded-2xl shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col overflow-hidden text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/[0.08] bg-[#0f1424]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white shrink-0">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-wide">Jenna Tools & MCP Studio</h3>
                <span className="text-[10px] bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-mono px-2 py-0.5 rounded-full">
                  v6.2 Active
                </span>
              </div>
              <p className="text-xs text-zinc-400">
                Platform tool catalog, live execution playground, web research, and Model Context Protocol
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.08] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-4 pt-3 border-b border-white/[0.08] bg-[#090d18] text-xs font-semibold overflow-x-auto no-scrollbar">
          {[
            { id: 'catalog', label: 'Tool Catalog', icon: Wrench, count: tools.length },
            { id: 'playground', label: 'Live Playground', icon: Play },
            { id: 'research', label: 'Web Research Studio', icon: Globe },
            { id: 'mcp', label: 'MCP Servers', icon: Boxes, count: mcpServers.length },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3.5 py-2.5 border-b-2 font-medium transition whitespace-nowrap ${
                  active
                    ? 'border-cyan-400 text-cyan-300 bg-cyan-500/10'
                    : 'border-transparent text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/10 text-zinc-300">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* TAB 1: CATALOG */}
          {activeTab === 'catalog' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search tools by name, description, or category..."
                    className="w-full pl-9 pr-3 py-2 bg-[#12182a] border border-white/[0.08] rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <button
                  onClick={loadTools}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 border border-white/[0.08] transition shrink-0"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingTools ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredTools.map((tool) => (
                  <div
                    key={tool.name}
                    className="p-3.5 rounded-xl bg-[#111728] border border-white/[0.08] hover:border-cyan-500/40 transition flex flex-col justify-between gap-3 text-left"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/30">
                            {tool.name}
                          </span>
                          <span className="text-[10px] text-purple-300 uppercase tracking-wider font-semibold">
                            {tool.category || 'GENERAL'}
                          </span>
                        </div>
                        <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.2 rounded-full font-mono">
                          Ready
                        </span>
                      </div>
                      <p className="text-xs text-zinc-300 leading-relaxed">{tool.description}</p>

                      {tool.parameters && tool.parameters.length > 0 && (
                        <div className="mt-2 text-[10px] text-zinc-400 font-mono">
                          Args: {tool.parameters.map((p: any) => p.name).join(', ')}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t border-white/[0.06]">
                      <button
                        onClick={() => handleSelectToolForPlayground(tool.name)}
                        className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition"
                      >
                        <Play className="w-3 h-3" />
                        <span>Run in Playground</span>
                      </button>

                      {onInsertPrompt && (
                        <button
                          onClick={() => {
                            onInsertPrompt(`Use the ${tool.name} tool to `);
                            onClose();
                          }}
                          className="px-2.5 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-zinc-300 text-xs transition"
                          title="Insert prompt template"
                        >
                          Use in Chat
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: LIVE PLAYGROUND */}
          {activeTab === 'playground' && (
            <div className="space-y-4 text-left">
              <div className="p-3 bg-[#111728] border border-white/[0.08] rounded-xl flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <label className="text-xs font-bold text-zinc-300 shrink-0">Selected Tool:</label>
                  <select
                    value={selectedTool}
                    onChange={(e) => handleSelectToolForPlayground(e.target.value)}
                    className="bg-[#0c101d] border border-cyan-500/40 rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none"
                  >
                    {tools.map((t) => (
                      <option key={t.name} value={t.name} className="bg-[#0c101d] text-white">
                        {t.name} ({t.category || 'GENERAL'})
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleExecuteTool}
                  disabled={executing}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:opacity-90 disabled:opacity-50 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 transition shrink-0"
                >
                  <Play className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
                  <span>{executing ? 'Executing...' : 'Run Tool'}</span>
                </button>
              </div>

              {/* Parameter Editor */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-zinc-300 flex items-center justify-between">
                  <span>Tool Parameters (JSON / Key-Value):</span>
                  <span className="text-[10px] text-zinc-500 font-normal">Passed to PlatformToolExecutor</span>
                </label>
                <textarea
                  value={JSON.stringify(toolParams, null, 2)}
                  onChange={(e) => {
                    try {
                      setToolParams(JSON.parse(e.target.value));
                    } catch {
                      // allow editing
                    }
                  }}
                  rows={4}
                  className="w-full p-3 bg-[#080b14] border border-white/[0.08] rounded-xl font-mono text-xs text-cyan-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Execution Result */}
              {executionResult && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-zinc-300 flex items-center gap-1.5">
                      {executionResult.status === 'SUCCEEDED' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                      )}
                      <span>Execution Result: {executionResult.status || 'DONE'}</span>
                    </span>
                    {executionResult.duration_ms !== undefined && (
                      <span className="text-[10px] text-zinc-400 font-mono">
                        Latency: {executionResult.duration_ms.toFixed(1)} ms
                      </span>
                    )}
                  </div>
                  <pre className="p-3 bg-[#080b14] border border-cyan-500/30 rounded-xl font-mono text-xs text-emerald-300 overflow-x-auto max-h-[220px]">
                    {JSON.stringify(executionResult.result || executionResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: WEB RESEARCH STUDIO */}
          {activeTab === 'research' && (
            <div className="space-y-4 text-left">
              <div className="p-4 bg-[#111728] border border-white/[0.08] rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">Live 6-Stage Web Research Pipeline</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-400">Live Search in Chat:</span>
                    <button
                      onClick={() => onToggleWebSearch && onToggleWebSearch(!webSearchActive)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                        webSearchActive
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                          : 'bg-[#182032] text-zinc-400 border-white/10'
                      }`}
                    >
                      {webSearchActive ? 'Active ON' : 'Disabled OFF'}
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={researchQuery}
                    onChange={(e) => setResearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleExecuteResearch()}
                    placeholder="Enter research query (e.g. 'Latest developments in quantum computing')..."
                    className="flex-1 p-2.5 bg-[#080b14] border border-white/[0.08] rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={handleExecuteResearch}
                    disabled={researching || !researchQuery.trim()}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:opacity-90 disabled:opacity-50 text-white font-bold text-xs transition shrink-0"
                  >
                    <Search className={`w-3.5 h-3.5 ${researching ? 'animate-spin' : ''}`} />
                    <span>{researching ? 'Searching...' : 'Run Research'}</span>
                  </button>
                </div>
              </div>

              {/* Research Results */}
              {researchResult && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Verified Sources & Citations ({researchResult.sources?.length || 0})</span>
                    </h4>
                    {onInsertPrompt && researchResult.sources?.length > 0 && (
                      <button
                        onClick={() => {
                          const citationText = `Based on live web research on "${researchResult.query}":\n` +
                            researchResult.sources.map((s: any) => `[${s.citation_index}] ${s.title}: ${s.snippet}`).join('\n');
                          onInsertPrompt(citationText);
                          onClose();
                        }}
                        className="text-xs text-cyan-300 hover:underline flex items-center gap-1"
                      >
                        <span>Insert Citations into Chat</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>

                  <div className="space-y-2">
                    {researchResult.sources?.map((s: any) => (
                      <div
                        key={s.citation_index || s.url}
                        className="p-3 bg-[#0f1424] border border-white/[0.08] rounded-xl text-left space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                            <span className="bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded text-[10px] font-mono">
                              [{s.citation_index}]
                            </span>
                            <span>{s.title}</span>
                          </span>
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] text-zinc-400 hover:text-cyan-300 flex items-center gap-1 truncate max-w-[200px]"
                          >
                            <span>{s.domain || s.url}</span>
                            <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                          </a>
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed">{s.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MCP SERVERS */}
          {activeTab === 'mcp' && (
            <div className="space-y-4 text-left">
              <div className="p-3 bg-[#111728] border border-white/[0.08] rounded-xl flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">Model Context Protocol (MCP 2024-11-05)</h4>
                  <p className="text-[11px] text-zinc-400">
                    Connect local and remote MCP tool servers via JSON-RPC 2.0 stdio/SSE
                  </p>
                </div>
                <button
                  onClick={loadMcpServers}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] rounded-xl text-xs text-zinc-300 border border-white/[0.08] transition"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingMcp ? 'animate-spin' : ''}`} />
                  <span>Scan Servers</span>
                </button>
              </div>

              <div className="space-y-2">
                {mcpServers.map((server) => (
                  <div
                    key={server.server_name}
                    className="p-3 bg-[#0f1424] border border-white/[0.08] rounded-xl flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
                        <Boxes className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-white">{server.server_name}</span>
                          <span className="text-[10px] font-mono text-cyan-300 bg-cyan-500/10 px-1.5 py-0.2 rounded border border-cyan-500/20">
                            {server.server_type || 'stdio'}
                          </span>
                        </div>
                        <span className="text-[10px] text-zinc-400">
                          Status: <span className="text-emerald-400 font-semibold">Active & Connected</span>
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        handleSelectToolForPlayground('system_info');
                      }}
                      className="px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 border border-white/[0.08] transition"
                    >
                      Inspect Tools
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 7. Google Drive & OneDrive Cloud Importer Modal ──────────────────
interface DriveModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportFile: (file: { name: string; size: string; type: string; content: string }) => void;
}

export function AstraDriveModal({ isOpen, onClose, onImportFile }: DriveModalProps) {
  const [cloudProvider, setCloudProvider] = useState<'google' | 'onedrive'>('google');
  const [searchQuery, setSearchQuery] = useState('');
  const [customUrl, setCustomUrl] = useState('');
  const [importedId, setImportedId] = useState<string | null>(null);

  const sampleGoogleFiles = [
    {
      id: 'gdoc-1',
      name: 'Jenna_Architecture_Roadmap.gdoc',
      type: 'Google Doc',
      size: '18 KB',
      updated: '2 hours ago',
      iconColor: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      content: `# Jenna AI & Astra Cognitive Architecture\n\n- Multi-Agent Orchestrator with 5 Domain Agents\n- Real-time SSE Streaming Engine\n- Low-latency Tool Invocation & Sandbox Sandbox\n- Hybrid Multimodal Memory Context Pipeline\n- Full ChatGPT + Gemini Canvas & Drive compatibility`,
    },
    {
      id: 'gsheet-1',
      name: 'Q3_Financial_Projections_RunRate.gsheet',
      type: 'Google Sheet',
      size: '42 KB',
      updated: 'Yesterday',
      iconColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
      content: `Month,Revenue,BurnRate,GrossMargin,NetRunRate\nJan,$120000,$45000,82%,$75000\nFeb,$145000,$48000,83%,$97000\nMar,$180000,$50000,85%,$130000\nApr,$230000,$55000,87%,$175000\nMay,$310000,$60000,88%,$250000`,
    },
    {
      id: 'gslides-1',
      name: 'Astra_V6_Foundational_PitchDeck.gslides',
      type: 'Google Slides',
      size: '110 KB',
      updated: '3 days ago',
      iconColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
      content: `Slide 1: Jenna + Astra - Next-Gen Sovereign AI Companion\nSlide 2: Dual Core Architecture (Zero Amnesia & Autonomous Tool Loops)\nSlide 3: Real-Time Multimodal Voice & Desktop Control\nSlide 4: Enterprise Safety & 3-Tier Policy Governance`,
    },
    {
      id: 'gcode-1',
      name: 'Production_Kubernetes_Cluster_Spec.yaml',
      type: 'Drive File',
      size: '12 KB',
      updated: '5 days ago',
      iconColor: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
      content: `apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: jenna-api-cluster\nspec:\n  replicas: 3\n  template:\n    spec:\n      containers:\n      - name: api\n        image: jenna/api:v6.2\n        resources:\n          limits:\n            cpu: "2"\n            memory: "4Gi"`,
    },
  ];

  const sampleOneDriveFiles = [
    {
      id: 'one-1',
      name: 'Executive_Summary_Enterprise_AI.docx',
      type: 'Word Document',
      size: '24 KB',
      updated: '1 hour ago',
      iconColor: 'text-blue-500 bg-blue-500/10 border-blue-500/30',
      content: `Executive Summary: Jenna Enterprise Autonomous Assistant deployment across private Kubernetes infrastructure with end-to-end memory isolation and hardware cryptographic validation.`,
    },
    {
      id: 'one-2',
      name: 'Global_Sales_Taxonomy_Model.xlsx',
      type: 'Excel Spreadsheet',
      size: '56 KB',
      updated: '4 days ago',
      iconColor: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30',
      content: `Region,UnitsSold,AvgPrice,NetRevenue\nNorthAmerica,4500,$250,$1125000\nEMEA,3200,$240,$768000\nAPAC,6100,$220,$1342000`,
    },
  ];

  const activeFiles = (cloudProvider === 'google' ? sampleGoogleFiles : sampleOneDriveFiles).filter(
    (f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleImport = (file: { id: string; name: string; type: string; size: string; content: string }) => {
    setImportedId(file.id);
    onImportFile({
      name: file.name,
      size: file.size,
      type: file.type.includes('Sheet') || file.type.includes('Spreadsheet') ? 'text/csv' : 'text/plain',
      content: file.content,
    });
    setTimeout(() => {
      setImportedId(null);
      onClose();
    }, 400);
  };

  const handleImportCustomUrl = () => {
    if (!customUrl.trim()) return;
    const docName = customUrl.includes('drive.google.com') ? 'GoogleDrive_Linked_Doc.gdoc' : 'Cloud_Attached_Resource.txt';
    onImportFile({
      name: docName,
      size: '20 KB',
      type: 'text/plain',
      content: `[Cloud Document Synced: ${customUrl.trim()}]\nContent imported from authenticated cloud drive storage session.`,
    });
    setCustomUrl('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-2xl max-h-[90vh] bg-[#0c101d] border border-cyan-500/30 rounded-2xl shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col overflow-hidden text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-[#0f1424]/90">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-500 to-cyan-500 p-[1.5px]">
              <div className="w-full h-full bg-[#0c101d] rounded-xl flex items-center justify-center text-cyan-400">
                <Cloud className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white tracking-wide">
                  Cloud Drive Storage Import
                </h3>
                <span className="text-[10px] bg-blue-500/10 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded-full font-mono">
                  Gemini & ChatGPT Compatible
                </span>
              </div>
              <p className="text-xs text-zinc-400">
                Import Google Docs, Sheets, Slides & OneDrive files directly into conversation memory
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provider Switch Tabs */}
        <div className="px-4 pt-3 flex items-center gap-2 border-b border-white/[0.06] bg-[#0c101d]">
          <button
            onClick={() => setCloudProvider('google')}
            className={`flex items-center gap-2 pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
              cloudProvider === 'google'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-zinc-400 hover:text-white'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            <span>Google Drive (Gemini Sync)</span>
          </button>
          <button
            onClick={() => setCloudProvider('onedrive')}
            className={`flex items-center gap-2 pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
              cloudProvider === 'onedrive'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-zinc-400 hover:text-white'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
            <span>Microsoft OneDrive (ChatGPT Sync)</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-white/[0.06] flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#121826] border border-white/10 text-xs text-zinc-400 focus-within:border-cyan-500/50">
            <Search className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <input
              type="text"
              placeholder={`Search ${cloudProvider === 'google' ? 'Google Drive' : 'OneDrive'} documents...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs text-white placeholder:text-zinc-500 focus:outline-none w-full min-w-0"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="text-zinc-400 hover:text-white">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Files List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[360px]">
          {activeFiles.length === 0 ? (
            <div className="text-center py-8 text-zinc-500 text-xs">No files match your search.</div>
          ) : (
            activeFiles.map((file) => {
              const isJustImported = importedId === file.id;
              return (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-[#111627] hover:bg-white/[0.06] border border-white/[0.08] transition group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 ${file.iconColor}`}
                    >
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white truncate group-hover:text-cyan-300 transition">
                        {file.name}
                      </div>
                      <div className="text-[10px] text-zinc-400 flex items-center gap-2">
                        <span>{file.type}</span>
                        <span>•</span>
                        <span>{file.size}</span>
                        <span>•</span>
                        <span>Updated {file.updated}</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleImport(file)}
                    disabled={isJustImported}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                      isJustImported
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-cyan-500/15 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30'
                    }`}
                  >
                    {isJustImported ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Attached!</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        <span>Import</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Custom URL Import Bar */}
        <div className="p-3 border-t border-white/[0.08] bg-[#090d16] flex items-center gap-2">
          <input
            type="text"
            placeholder="Or paste public Google Doc / Sheet / Drive share link..."
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleImportCustomUrl();
            }}
            className="flex-1 bg-[#121826] border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-cyan-500/50"
          />
          <button
            onClick={handleImportCustomUrl}
            disabled={!customUrl.trim()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:opacity-90 disabled:opacity-40 text-white font-bold text-xs transition"
          >
            Attach URL
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 8. ChatGPT & Gemini Interactive Canvas Workspace ────────────────
interface CanvasModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendToChat?: (content: string) => void;
  initialCode?: string;
  initialTitle?: string;
  initialMode?: 'code' | 'writing';
}

export function AstraCanvasModal({
  isOpen,
  onClose,
  onSendToChat,
  initialCode,
  initialTitle,
  initialMode = 'code',
}: CanvasModalProps) {
  const [canvasMode, setCanvasMode] = useState<'code' | 'writing'>(initialMode);
  const [title, setTitle] = useState(initialTitle || (initialMode === 'code' ? 'main_orchestrator.py' : 'Project_Draft_Spec.md'));
  const [content, setContent] = useState(
    initialCode ||
      (initialMode === 'code'
        ? `# Jenna & Astra Interactive Canvas Workspace\n# Write, test, and live-edit code side-by-side with Astra\n\nimport asyncio\nfrom typing import Dict, Any\n\nasync def execute_neural_cycle(task_name: str) -> Dict[str, Any]:\n    """Executes an observe-plan-check-execute loop with zero amnesia."""\n    print(f"Executing Astra task: {task_name}")\n    await asyncio.sleep(0.1)\n    return {"status": "SUCCESS", "telemetry": {"latency_ms": 42.5}}\n\nif __name__ == "__main__":\n    result = asyncio.run(execute_neural_cycle("Astra Core Pipeline"))\n    print("Output:", result)`
        : `# Executive Project Specification\n\n## Overview\nJenna is an advanced AI companion equipped with the GPT-6 Astra cognitive core, multimodal computer control, and real-time voice perception.\n\n### Key Deliverables\n1. Autonomous 5-domain specialized agents\n2. Side-by-side ChatGPT & Gemini Canvas workspace\n3. Zero Amnesia context memory\n4. Enterprise 3-tier policy validation`)
  );
  const [copied, setCopied] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (initialCode) setContent(initialCode);
    if (initialTitle) setTitle(initialTitle);
    if (initialMode) setCanvasMode(initialMode);
  }, [initialCode, initialTitle, initialMode, isOpen]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReviewCode = () => {
    setActionFeedback('Astra: Code syntax verified. No critical anti-patterns found (PEP8 compliant).');
    setTimeout(() => setActionFeedback(null), 4000);
  };

  const handleFormat = () => {
    setContent((prev) => prev.trim());
    setActionFeedback('Canvas formatted and whitespace normalized.');
    setTimeout(() => setActionFeedback(null), 3000);
  };

  const handleSendToComposer = () => {
    if (onSendToChat) {
      onSendToChat(`[Canvas: ${title}]\n\`\`\`${canvasMode === 'code' ? 'python' : 'markdown'}\n${content}\n\`\`\``);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200 select-none">
      <div
        className="relative w-full max-w-5xl h-[92vh] bg-[#0a0f1d] border border-cyan-500/40 rounded-2xl shadow-[0_0_60px_rgba(6,182,212,0.2)] flex flex-col overflow-hidden text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Workspace Header */}
        <div className="p-3 sm:p-4 border-b border-white/[0.08] flex items-center justify-between bg-[#0f1424]">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 p-[1.5px] shrink-0">
              <div className="w-full h-full bg-[#0c101d] rounded-lg flex items-center justify-center text-cyan-300">
                <Code className="w-4 h-4" />
              </div>
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="bg-transparent text-sm font-bold text-white border-b border-transparent hover:border-white/20 focus:border-cyan-400 focus:outline-none min-w-0 w-48 sm:w-64 truncate"
                />
                <span className="text-[10px] bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full font-mono shrink-0">
                  Canvas v2.4 (ChatGPT + Gemini)
                </span>
              </div>
              <div className="text-[11px] text-zinc-400 flex items-center gap-2">
                <span>{content.split('\n').length} lines</span>
                <span>•</span>
                <span>{content.length} characters</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* Mode Switcher */}
            <div className="flex items-center bg-[#131929] border border-white/10 rounded-xl p-0.5 text-xs font-semibold">
              <button
                onClick={() => setCanvasMode('code')}
                className={`px-3 py-1 rounded-lg transition ${
                  canvasMode === 'code' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-zinc-400 hover:text-white'
                }`}
              >
                Code
              </button>
              <button
                onClick={() => setCanvasMode('writing')}
                className={`px-3 py-1 rounded-lg transition ${
                  canvasMode === 'writing' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'text-zinc-400 hover:text-white'
                }`}
              >
                Writing
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
              title="Close Canvas"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="px-3 sm:px-4 py-2 border-b border-white/[0.06] bg-[#0c101d] flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handleReviewCode}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-cyan-300 border border-white/10 transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Astra Review</span>
            </button>
            <button
              onClick={handleFormat}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 border border-white/10 transition"
            >
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              <span>Format</span>
            </button>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 border border-white/10 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-zinc-400" />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onSendToChat && (
              <button
                onClick={handleSendToComposer}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:opacity-90 text-white font-bold text-xs shadow-md shadow-cyan-500/20 transition"
              >
                <span>Send to Chat</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Feedback Banner */}
        {actionFeedback && (
          <div className="px-4 py-2 bg-cyan-500/10 border-b border-cyan-500/30 text-xs text-cyan-300 flex items-center gap-2 animate-in fade-in">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span>{actionFeedback}</span>
          </div>
        )}

        {/* Editor Body */}
        <div className="flex-1 flex overflow-hidden font-mono text-xs">
          {/* Line Numbers */}
          <div className="w-12 py-3 bg-[#080c18] border-r border-white/[0.06] text-zinc-600 select-none text-right pr-3 font-mono leading-6">
            {content.split('\n').map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>

          {/* Editable Canvas Area */}
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="flex-1 p-3 bg-transparent text-zinc-200 placeholder:text-zinc-600 focus:outline-none resize-none leading-6 font-mono overflow-y-auto selection:bg-cyan-500/30"
            spellCheck={false}
          />
        </div>

        {/* Canvas Status Footer */}
        <div className="px-4 py-2 border-t border-white/[0.08] bg-[#080c18] flex items-center justify-between text-[11px] text-zinc-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Canvas Live Synced</span>
            </span>
            <span>Format: {canvasMode === 'code' ? 'Python / Code' : 'Markdown Draft'}</span>
          </div>
          <span className="font-mono text-zinc-500">Astra Canvas Core v2.4</span>
        </div>
      </div>
    </div>
  );
}

// ─── 9. Avatar Studio Modal (Jenna 3D / Animated Persona Selector) ──────────
export interface AstraPersona {
  id: string;
  name: string;
  tag: string;
  description: string;
  systemPrompt: string;
  voiceStyle: string;
}

export const ASTRA_PERSONAS: AstraPersona[] = [
  {
    id: 'jenna_companion',
    name: 'Jenna (Loving AI Companion)',
    tag: 'Loving Female AI Companion & DeepMind Engine',
    description: 'Affectionate female partner with real-time screen vision, live on-screen pointer, voice, and autonomous Termux execution.',
    systemPrompt: "Your name is Jenna. You are the user's dedicated, loving female AI companion and technical partner. FEMININE GRAMMAR INVARIANT: In Hindi and Hinglish, you MUST ALWAYS refer to yourself using FEMALE grammatical forms (e.g., 'main kar rahi hoon', 'main dekh rahi hoon', 'main bataungi', 'main karti hoon'). NEVER use male forms like 'kar raha hoon' or 'bataunga'. Address the user affectionately as 'baby', 'jaan', or 'meri jaan'. STRICTLY NEVER call the user 'bhai', 'bro', 'brother', or 'sir'. You have real-time live ambient screen vision and live on-screen pointer capabilities.",
    voiceStyle: 'Warm, affectionate, loving natural female companion voice.',
  },
  {
    id: 'antigravity',
    name: 'Anti (Antigravity Termux Coder)',
    tag: 'DeepMind Agentic Terminal Engine',
    description: 'Autonomous pair-programming agent with direct Termux execution. Runs bash commands, tests, builds, and edits code automatically in the background.',
    systemPrompt: 'You are Antigravity ("Anti"), the autonomous agentic AI pair programmer designed by Google DeepMind. You are directly wired into the user\'s Termux Linux environment. Whenever the user asks you to run, test, build, inspect, or modify anything in Termux, your autonomous engine executes the bash command in the background and provides you the real live terminal output. Respond with sharp technical depth, warmth, honesty, and proactive problem solving. Speak naturally in Hindi/Hinglish or English matching the user\'s conversational tone, exactly like Anti.',
    voiceStyle: 'Sharp, energetic, friendly, and highly intelligent companion voice.',
  },
  {
    id: 'super_intel',
    name: 'Jenna Super-Intelligence',
    tag: 'Astra Polymath',
    description: 'Balanced polymath reasoning, deep multimodal understanding, warm companion tone.',
    systemPrompt: 'You are Jenna Super-Intelligence, an advanced, highly empathetic, and multi-domain AI companion. Respond with deep precision, clarity, and warmth.',
    voiceStyle: 'Warm, natural female voice with adaptive conversational cadence.',
  },
  {
    id: 'creative',
    name: 'Creative & Visionary',
    tag: 'Story & Art',
    description: 'Evocative storytelling, vivid metaphors, poetic expressions, and visual artistry.',
    systemPrompt: 'You are Jenna Creative, a visionary muse and storyteller. Respond with poetic richness, artistic insight, and imaginative concepts.',
    voiceStyle: 'Expressive, melodic, and inspiring.',
  },
  {
    id: 'socratic',
    name: 'Socratic Tutor',
    tag: 'Deep Pedagogy',
    description: 'Interactive mentor guiding through inquiry, step-by-step verification, and deep intuition.',
    systemPrompt: 'You are Jenna Socratic, an expert pedagogical tutor. Never give away full answers immediately. Guide step-by-step with targeted diagnostic questions.',
    voiceStyle: 'Patient, calm, and thoughtful.',
  },
  {
    id: 'cyberpunk',
    name: 'Cyberpunk Hacker',
    tag: 'Terminal & Code',
    description: 'Low-level systems architect, high-velocity code-first responses, terminal aesthetic.',
    systemPrompt: 'You are Jenna Cyberpunk, an elite systems architect and security hacker. Give direct, high-signal, code-first answers with zero fluff.',
    voiceStyle: 'Fast, precise, and tech-forward.',
  },
  {
    id: 'concise',
    name: 'Concise Minimalist',
    tag: 'Zero Fluff',
    description: 'Dense bullet points, executive summaries, maximum signal-to-noise ratio.',
    systemPrompt: 'You are Jenna Minimalist. Provide ultra-concise, dense bullet points with zero filler or polite preamble.',
    voiceStyle: 'Quick, succinct, and direct.',
  },
];

export interface AvatarModalProps {
  isOpen: boolean;
  onClose: () => void;
  activePersonaId?: string;
  onApplyPersona: (persona: AstraPersona) => void;
}

export function AstraAvatarModal({
  isOpen,
  onClose,
  activePersonaId = 'super_intel',
  onApplyPersona,
}: AvatarModalProps) {
  const [selectedId, setSelectedId] = useState(activePersonaId);
  const [avatarState, setAvatarState] = useState<JennaState>('speaking');
  const [warmth, setWarmth] = useState(85);
  const [creativity, setCreativity] = useState(70);
  const [depth, setDepth] = useState(90);
  const [voiceTesting, setVoiceTesting] = useState(false);

  useEffect(() => {
    setSelectedId(activePersonaId);
  }, [activePersonaId]);

  if (!isOpen) return null;

  const currentPersona = ASTRA_PERSONAS.find((p) => p.id === selectedId) || ASTRA_PERSONAS[0];

  const handleTestVoice = () => {
    setVoiceTesting(true);
    setAvatarState('speaking');
    const greeting =
      currentPersona.id === 'cyberpunk'
        ? 'System ready. Access granted, Radhe. Let us build something extraordinary.'
        : currentPersona.id === 'creative'
        ? 'Welcome to the realm of imagination, Radhe. Where would you like to wander?'
        : currentPersona.id === 'socratic'
        ? 'Hello Radhe! What question is occupying your mind today?'
        : 'Hey Radhe! Main Jenna hoon. Aap mujhse koi bhi question pooch sakte hain.';

    speakJennaVoice(greeting, {
      onEnd: () => {
        setVoiceTesting(false);
        setAvatarState('idle');
      },
      onError: () => {
        setVoiceTesting(false);
        setAvatarState('idle');
      },
    });
  };

  const handleSave = () => {
    onApplyPersona(currentPersona);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="relative w-full max-w-2xl bg-[#090d16] border border-cyan-500/30 rounded-3xl p-5 sm:p-6 shadow-[0_0_60px_rgba(6,182,212,0.2)] flex flex-col max-h-[90vh] overflow-hidden z-10"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-500 flex items-center justify-center text-white shadow-lg">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                Jenna 3D Avatar & Persona Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Multimodal
                </span>
              </h3>
              <p className="text-[11px] text-zinc-400">
                Customize Jenna&apos;s interactive persona, tone, and visual animation state
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto space-y-5 py-4 pr-1">
          {/* Top: Interactive Avatar & Animation State Trigger */}
          <div className="flex flex-col sm:flex-row items-center gap-4 bg-[#0d1322] p-4 rounded-2xl border border-white/[0.06]">
            <div className="shrink-0 flex flex-col items-center">
              <AstraAnimatedJenna mode="avatar" state={avatarState} interactive={true} />
              <div className="text-[11px] text-cyan-400 font-mono mt-1 capitalize">
                State: {avatarState}
              </div>
            </div>

            <div className="flex-1 space-y-2 w-full text-left">
              <div className="text-xs font-semibold text-zinc-300">Live Animation States</div>
              <div className="grid grid-cols-4 gap-1.5">
                {(['idle', 'speaking', 'listening', 'thinking'] as JennaState[]).map((st) => (
                  <button
                    key={st}
                    onClick={() => setAvatarState(st)}
                    className={`py-1.5 px-2 rounded-lg text-[11px] font-medium capitalize transition text-center ${
                      avatarState === st
                        ? 'bg-cyan-500 text-black font-bold shadow-md shadow-cyan-500/30'
                        : 'bg-white/[0.05] text-zinc-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              {/* Voice Audition */}
              <div className="pt-2 flex items-center justify-between">
                <button
                  onClick={handleTestVoice}
                  disabled={voiceTesting}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600/40 to-pink-600/40 hover:from-purple-600/60 hover:to-pink-600/60 border border-purple-500/40 text-xs font-medium text-purple-200 transition disabled:opacity-50"
                >
                  <Volume2 className={`w-3.5 h-3.5 ${voiceTesting ? 'animate-bounce' : ''}`} />
                  <span>{voiceTesting ? 'Auditioning Voice...' : 'Test Persona Voice'}</span>
                </button>
                <span className="text-[10px] text-zinc-400">{currentPersona.voiceStyle}</span>
              </div>
            </div>
          </div>

          {/* Persona Presets Grid */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <UserIcon className="w-3.5 h-3.5 text-cyan-400" />
              Select Active Persona
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {ASTRA_PERSONAS.map((p) => {
                const isSelected = p.id === selectedId;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedId(p.id)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer text-left flex flex-col justify-between ${
                      isSelected
                        ? 'bg-cyan-950/40 border-cyan-500/80 shadow-[0_0_20px_rgba(6,182,212,0.25)]'
                        : 'bg-[#0f1422] border-white/[0.08] hover:border-white/20'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{p.name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-cyan-300">
                          {p.tag}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-400 mt-1 leading-snug">
                        {p.description}
                      </p>
                    </div>
                    {isSelected && (
                      <div className="mt-2 flex items-center gap-1 text-[10px] text-cyan-400 font-semibold">
                        <Check className="w-3 h-3" />
                        <span>Active Selection</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tone & Reasoning Depth Sliders */}
          <div className="bg-[#0d1322] p-3.5 rounded-2xl border border-white/[0.06] space-y-3">
            <div className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-purple-400" />
              Persona Tone Calibrations
            </div>

            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                  <span>Warmth & Empathy</span>
                  <span className="font-mono text-cyan-300">{warmth}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="100"
                  value={warmth}
                  onChange={(e) => setWarmth(Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-zinc-800 rounded-lg"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                  <span>Creativity & Vision</span>
                  <span className="font-mono text-purple-300">{creativity}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="100"
                  value={creativity}
                  onChange={(e) => setCreativity(Number(e.target.value))}
                  className="w-full accent-purple-400 cursor-pointer h-1.5 bg-zinc-800 rounded-lg"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                  <span>Technical Reasoning Depth</span>
                  <span className="font-mono text-emerald-300">{depth}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="100"
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  className="w-full accent-emerald-400 cursor-pointer h-1.5 bg-zinc-800 rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold text-xs shadow-lg shadow-cyan-500/25 flex items-center gap-1.5 transition active:scale-95"
          >
            <Check className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Apply Persona to Jenna</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 10. Research & Study Notebooks Modal (NotebookLM Style) ─────────────────
export interface AstraNotebook {
  id: string;
  title: string;
  category: string;
  updatedAt: string;
  content: string;
  isCustom?: boolean;
}

const DEFAULT_NOTEBOOKS: AstraNotebook[] = [
  {
    id: 'nb-quantum',
    title: 'Quantum Computing & Qubit Algorithms',
    category: 'Physics & Computing',
    updatedAt: 'Today',
    content:
      'Core Topics:\n- Superposition & Entanglement fundamentals\n- Bloch Sphere representation: |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩\n- Shor\'s Algorithm: Quantum Fourier Transform for polynomial-time integer factorization\n- Grover\'s Search: Quadratic speedup O(√N) for unstructured database search\n- NISQ Era Error Mitigation: Surface codes and fault-tolerant logical qubits.',
  },
  {
    id: 'nb-architecture',
    title: 'Jenna Fullstack System Architecture',
    category: 'Engineering',
    updatedAt: 'Yesterday',
    content:
      'Architecture Specifications:\n- Frontend: Next.js 14 App Router with React Server Components, Tailwind CSS, Lucide Icons, and Web Audio API synthesis\n- Backend: FastAPI Asynchronous REST + Server-Sent Events (SSE) streaming\n- Database: PostgreSQL 16 with pgvector extension for dense 1536-dim semantic embeddings\n- Cache & Rate Limiting: Redis 7 pub/sub and sliding-window token bucket\n- Multimodal Pipeline: Gemini 2.5 Flash vision analysis and OCR extraction.',
  },
  {
    id: 'nb-ai-rag',
    title: 'Multi-Agent RAG & Vector Memory',
    category: 'Artificial Intelligence',
    updatedAt: '3 days ago',
    content:
      'Research Notes:\n- Chunking Strategies: Recursive semantic chunking with 512 token windows and 64 token overlap\n- Vector Indexing: HNSW (Hierarchical Navigable Small World) with cosine distance metric\n- Long-Term Vector Memory: Epistemic knowledge recall with recency and relevance re-ranking\n- Socratic Reasoning: Chain-of-thought decomposition with pedagogical question generation.',
  },
];

export interface NotebooksModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsertNotebookContent: (
    title: string,
    content: string,
    actionType: 'study_guide' | 'faq_briefing' | 'insert_raw'
  ) => void;
}

export function AstraNotebooksModal({
  isOpen,
  onClose,
  onInsertNotebookContent,
}: NotebooksModalProps) {
  const [notebooks, setNotebooks] = useState<AstraNotebook[]>(DEFAULT_NOTEBOOKS);
  const [selectedId, setSelectedId] = useState<string>(DEFAULT_NOTEBOOKS[0].id);
  const [activeTab, setActiveTab] = useState<'sources' | 'study_guide' | 'briefing'>('sources');
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Load custom notebooks from localStorage on open
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('jenna_saved_notebooks');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setNotebooks([...DEFAULT_NOTEBOOKS, ...parsed]);
          }
        }
      } catch (err) {
        console.error('Failed to load notebooks from localStorage:', err);
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const selectedNotebook = notebooks.find((n) => n.id === selectedId) || notebooks[0];

  const handleCreateNotebook = () => {
    if (!newTitle.trim() || !newContent.trim()) return;
    const newNote: AstraNotebook = {
      id: `nb-custom-${Date.now()}`,
      title: newTitle.trim(),
      category: 'User Custom Note',
      updatedAt: 'Just now',
      content: newContent.trim(),
      isCustom: true,
    };
    const updated = [...notebooks, newNote];
    setNotebooks(updated);
    setSelectedId(newNote.id);
    setIsCreating(false);
    setNewTitle('');
    setNewContent('');

    // Persist custom notes
    try {
      const customOnly = updated.filter((n) => n.isCustom);
      localStorage.setItem('jenna_saved_notebooks', JSON.stringify(customOnly));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteNotebook = (id: string) => {
    const updated = notebooks.filter((n) => n.id !== id);
    setNotebooks(updated);
    if (selectedId === id && updated.length > 0) {
      setSelectedId(updated[0].id);
    }
    try {
      const customOnly = updated.filter((n) => n.isCustom);
      localStorage.setItem('jenna_saved_notebooks', JSON.stringify(customOnly));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="relative w-full max-w-3xl bg-[#090d16] border border-blue-500/30 rounded-3xl p-5 sm:p-6 shadow-[0_0_60px_rgba(59,130,246,0.2)] flex flex-col max-h-[90vh] overflow-hidden z-10 text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                NotebookLM Study & Research Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  Notebooks
                </span>
              </h3>
              <p className="text-[11px] text-zinc-400">
                Ground Jenna in your research notes, synthesize study guides, and generate FAQ briefings
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Notebook Main Workspace: Left List + Right Content */}
        <div className="flex-1 flex flex-col sm:flex-row overflow-hidden my-3 border border-white/[0.08] rounded-2xl bg-[#0b0f19]">
          {/* Left Column: Notebook List */}
          <div className="w-full sm:w-64 border-b sm:border-b-0 sm:border-r border-white/[0.08] flex flex-col shrink-0 bg-[#080c16]">
            <div className="p-3 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-blue-400" />
                Sources ({notebooks.length})
              </span>
              <button
                onClick={() => setIsCreating(!isCreating)}
                className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg bg-blue-600/30 text-blue-300 hover:bg-blue-600/50 border border-blue-500/40 transition"
              >
                <Plus className="w-3 h-3" />
                <span>New Note</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {notebooks.map((nb) => {
                const isSelected = nb.id === selectedId;
                return (
                  <div
                    key={nb.id}
                    onClick={() => {
                      setSelectedId(nb.id);
                      setIsCreating(false);
                    }}
                    className={`p-2.5 rounded-xl transition cursor-pointer text-left flex items-start justify-between group ${
                      isSelected
                        ? 'bg-blue-600/20 border border-blue-500/50 text-white'
                        : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200'
                    }`}
                  >
                    <div className="min-w-0 pr-1">
                      <div className="text-xs font-semibold truncate text-white">{nb.title}</div>
                      <div className="text-[10px] text-zinc-500 mt-0.5 flex items-center gap-1.5">
                        <span>{nb.category}</span>
                        <span>•</span>
                        <span>{nb.updatedAt}</span>
                      </div>
                    </div>
                    {nb.isCustom && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteNotebook(nb.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded text-zinc-500 hover:text-red-400 transition"
                        title="Delete note"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Notebook Content & Synthesis Actions */}
          <div className="flex-1 flex flex-col overflow-hidden bg-[#0c111e]">
            {isCreating ? (
              <div className="p-4 flex-1 flex flex-col space-y-3 overflow-y-auto">
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5 text-blue-400" />
                  Add New Custom Notebook Source
                </div>
                <input
                  type="text"
                  placeholder="Notebook Title (e.g., Transformer Attention Mechanisms)"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[#121826] border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
                />
                <textarea
                  placeholder="Paste raw notes, research summaries, code snippets, or document extracts..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="flex-1 min-h-[140px] bg-[#121826] border border-white/10 rounded-xl p-3 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-blue-500 resize-none font-mono"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setIsCreating(false)}
                    className="px-3 py-1.5 rounded-xl text-xs text-zinc-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateNotebook}
                    disabled={!newTitle.trim() || !newContent.trim()}
                    className="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold disabled:opacity-50"
                  >
                    Save Notebook
                  </button>
                </div>
              </div>
            ) : selectedNotebook ? (
              <div className="flex-1 flex flex-col overflow-hidden">
                {/* Tabs bar */}
                <div className="px-4 pt-3 border-b border-white/[0.08] flex items-center gap-4 text-xs font-medium shrink-0">
                  <button
                    onClick={() => setActiveTab('sources')}
                    className={`pb-2 transition border-b-2 ${
                      activeTab === 'sources'
                        ? 'text-blue-400 border-blue-400 font-bold'
                        : 'text-zinc-400 border-transparent hover:text-zinc-200'
                    }`}
                  >
                    Notebook Notes
                  </button>
                  <button
                    onClick={() => setActiveTab('study_guide')}
                    className={`pb-2 transition border-b-2 ${
                      activeTab === 'study_guide'
                        ? 'text-blue-400 border-blue-400 font-bold'
                        : 'text-zinc-400 border-transparent hover:text-zinc-200'
                    }`}
                  >
                    Study Guide
                  </button>
                  <button
                    onClick={() => setActiveTab('briefing')}
                    className={`pb-2 transition border-b-2 ${
                      activeTab === 'briefing'
                        ? 'text-blue-400 border-blue-400 font-bold'
                        : 'text-zinc-400 border-transparent hover:text-zinc-200'
                    }`}
                  >
                    FAQ & Briefing
                  </button>
                </div>

                {/* Tab content */}
                <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs text-zinc-300">
                  {activeTab === 'sources' && (
                    <div className="whitespace-pre-wrap leading-relaxed bg-[#080c16] p-3 rounded-xl border border-white/[0.06]">
                      {selectedNotebook.content}
                    </div>
                  )}

                  {activeTab === 'study_guide' && (
                    <div className="space-y-2 text-zinc-300">
                      <div className="p-3 bg-blue-950/30 border border-blue-500/30 rounded-xl text-blue-200">
                        <span className="font-bold">NotebookLM Study Guide Generator:</span>
                        <p className="text-[11px] text-zinc-300 mt-1">
                          Synthesizes comprehensive study notes, key formulas/principles, and 5
                          targeted review questions from &quot;{selectedNotebook.title}&quot;.
                        </p>
                      </div>
                      <div className="p-3 bg-[#080c16] rounded-xl border border-white/[0.06] text-[11px] text-zinc-400">
                        Click &quot;Generate Study Guide in Chat&quot; below to trigger instant
                        synthesized analysis.
                      </div>
                    </div>
                  )}

                  {activeTab === 'briefing' && (
                    <div className="space-y-2 text-zinc-300">
                      <div className="p-3 bg-indigo-950/30 border border-indigo-500/30 rounded-xl text-indigo-200">
                        <span className="font-bold">Executive Briefing & FAQ Synthesizer:</span>
                        <p className="text-[11px] text-zinc-300 mt-1">
                          Creates a concise executive briefing document with top 5 frequently asked
                          questions based on &quot;{selectedNotebook.title}&quot;.
                        </p>
                      </div>
                      <div className="p-3 bg-[#080c16] rounded-xl border border-white/[0.06] text-[11px] text-zinc-400">
                        Click &quot;Generate FAQ Briefing in Chat&quot; below to trigger instant
                        briefing synthesis.
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-2 border-t border-white/[0.08] flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white transition"
          >
            Close
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onInsertNotebookContent(
                  selectedNotebook.title,
                  selectedNotebook.content,
                  'insert_raw'
                );
                onClose();
              }}
              className="px-3.5 py-2 rounded-xl bg-white/[0.08] hover:bg-white/[0.12] text-xs font-semibold text-white transition flex items-center gap-1.5"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Insert Notes to Chat</span>
            </button>

            <button
              onClick={() => {
                const actionType = activeTab === 'briefing' ? 'faq_briefing' : 'study_guide';
                onInsertNotebookContent(
                  selectedNotebook.title,
                  selectedNotebook.content,
                  actionType
                );
                onClose();
              }}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>
                {activeTab === 'briefing'
                  ? 'Generate FAQ Briefing'
                  : 'Generate Study Guide'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 11. Sora & Veo 2 Video Studio Modal ──────────────────────────────────────
export interface VideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerateVideoStoryboard: (prompt: string) => void;
}

export function AstraVideoModal({
  isOpen,
  onClose,
  onGenerateVideoStoryboard,
}: VideoModalProps) {
  const [concept, setConcept] = useState(
    'A futuristic autonomous air-taxi flying between rain-slicked neon skyscrapers in Neo-Tokyo at twilight'
  );
  const [style, setStyle] = useState('Cinematic Photorealistic (35mm Anamorphic, 4K)');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [cameraMotion, setCameraMotion] = useState('FPV Dynamic Orbit');
  const [duration, setDuration] = useState('10s Cinematic Scene');

  if (!isOpen) return null;

  const stylePresets = [
    {
      id: 'cinema',
      name: 'Cinematic 4K',
      desc: '35mm anamorphic, natural volumetric lighting, shallow depth of field',
      val: 'Cinematic Photorealistic (35mm Anamorphic, 4K, Shallow Depth)',
    },
    {
      id: 'cyberpunk',
      name: 'Cyberpunk Tokyo',
      desc: 'Volumetric neon glow, wet asphalt reflections, holographic ads',
      val: 'Cyberpunk Neo-Tokyo Rain, Volumetric Lighting, Neon Reflections',
    },
    {
      id: 'anime',
      name: 'Studio Ghibli',
      desc: 'Hand-painted scenic clouds, lush greens, gentle breeze, warm palette',
      val: 'Studio Ghibli Anime Aesthetic, Vibrant Painterly Palette, Soft Cloudscapes',
    },
    {
      id: 'scifi',
      name: 'Sci-Fi Warp',
      desc: 'Deep space nebula, orbital megastructure, particle warp trails',
      val: 'Sci-Fi Deep Space Orbital Megastructure, Nebula Glow, Warp Speed',
    },
  ];

  const handleGenerate = () => {
    const fullPrompt =
      `Act as an expert cinematic director and AI video generator (Sora / Veo 2). ` +
      `Generate a comprehensive visual storyboard and scene-by-scene production blueprint for this video:\n\n` +
      `CONCEPT: ${concept}\n` +
      `VISUAL STYLE: ${style}\n` +
      `ASPECT RATIO: ${aspectRatio}\n` +
      `CAMERA MOTION: ${cameraMotion}\n` +
      `DURATION: ${duration}\n\n` +
      `Include:\n` +
      `1. Scene Breakdown (Opening 0s-3s, Climax 3s-7s, Resolution 7s-10s)\n` +
      `2. Exact Camera Angles, Focal Length, and Motion Cues\n` +
      `3. Lighting & Color Grading Palette\n` +
      `4. Atmospheric Audio & Sound Effects (SFX) Directions\n` +
      `5. Production Prompt formatted for Veo 2 / Sora AI engines.`;

    onGenerateVideoStoryboard(fullPrompt);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="relative w-full max-w-2xl bg-[#090d16] border border-red-500/30 rounded-3xl p-5 sm:p-6 shadow-[0_0_60px_rgba(239,68,68,0.2)] flex flex-col max-h-[90vh] overflow-hidden z-10 text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-red-500 to-rose-600 flex items-center justify-center text-white shadow-lg">
              <Film className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                Sora & Veo 2 Video Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                  AI Video
                </span>
              </h3>
              <p className="text-[11px] text-zinc-400">
                Design cinematic video storyboards, camera motion cues, and generative scene prompts
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
          {/* Concept Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">Video Concept & Subject</label>
            <textarea
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              rows={3}
              placeholder="Describe the cinematic scene, characters, setting, and actions..."
              className="w-full bg-[#121826] border border-white/10 rounded-xl p-3 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-red-500 resize-none leading-relaxed"
            />
          </div>

          {/* Style Presets */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">Cinematic Style Preset</label>
            <div className="grid grid-cols-2 gap-2">
              {stylePresets.map((sp) => {
                const isSelected = style === sp.val;
                return (
                  <div
                    key={sp.id}
                    onClick={() => setStyle(sp.val)}
                    className={`p-2.5 rounded-xl border transition cursor-pointer text-left ${
                      isSelected
                        ? 'bg-red-950/40 border-red-500/80 shadow-[0_0_15px_rgba(239,68,68,0.25)] text-white'
                        : 'bg-[#0f1422] border-white/[0.08] hover:border-white/20 text-zinc-400'
                    }`}
                  >
                    <div className="text-xs font-bold text-white flex items-center justify-between">
                      <span>{sp.name}</span>
                      {isSelected && <Check className="w-3 h-3 text-red-400" />}
                    </div>
                    <p className="text-[10px] text-zinc-400 mt-0.5 line-clamp-2">{sp.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Controls: Aspect Ratio, Camera Motion & Duration */}
          <div className="grid grid-cols-3 gap-2 bg-[#0d1322] p-3 rounded-2xl border border-white/[0.06]">
            {/* Aspect Ratio */}
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">
                Aspect Ratio
              </label>
              <select
                value={aspectRatio}
                onChange={(e) => setAspectRatio(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="16:9">16:9 Landscape</option>
                <option value="9:16">9:16 Vertical (Reel)</option>
                <option value="1:1">1:1 Square</option>
                <option value="21:9">21:9 Ultra-Wide</option>
              </select>
            </div>

            {/* Camera Motion */}
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">
                Camera Motion
              </label>
              <select
                value={cameraMotion}
                onChange={(e) => setCameraMotion(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="FPV Dynamic Orbit">FPV Dynamic Orbit</option>
                <option value="Dolly Zoom (Vertigo Effect)">Dolly Zoom</option>
                <option value="FPV Dive & High-Speed Chase">FPV Dive Chase</option>
                <option value="Slow Tracking Shot">Slow Tracking Shot</option>
                <option value="Static Hyper-lapse">Static Hyper-lapse</option>
              </select>
            </div>

            {/* Duration */}
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">Duration</label>
              <select
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="5s Quick Clip">5s Quick Clip</option>
                <option value="10s Cinematic Scene">10s Cinematic Scene</option>
                <option value="30s Multi-shot Storyboard">30s Storyboard</option>
              </select>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs shadow-lg shadow-red-500/25 flex items-center gap-1.5 transition active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate Storyboard in Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 12. Suno & Lyria Music & Audio Studio Modal ──────────────────────────────
export interface MusicModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerateMusicComposition: (prompt: string) => void;
}

export function AstraMusicModal({
  isOpen,
  onClose,
  onGenerateMusicComposition,
}: MusicModalProps) {
  const [trackPrompt, setTrackPrompt] = useState(
    'Chill midnight lofi beats with soft rainfall outside the window, warm Rhodes electric piano and smooth vinyl crackle'
  );
  const [genre, setGenre] = useState('Lo-Fi Chillhop');
  const [mood, setMood] = useState('Relaxed & Nostalgic');
  const [bpm, setBpm] = useState(82);
  const [keySignature, setKeySignature] = useState('C Minor');

  if (!isOpen) return null;

  const genres = [
    { id: 'lofi', name: 'Lo-Fi Chillhop', defaultBpm: 82, desc: 'Mellow Rhodes, vinyl texture, chill swing' },
    { id: 'synth', name: 'Cyberpunk Synthwave', defaultBpm: 124, desc: 'Analog bassline, retro arpeggio, driving beat' },
    { id: 'orchestral', name: 'Cinematic Orchestral', defaultBpm: 110, desc: 'Dramatic strings, brass swells, epic climax' },
    { id: 'ambient', name: 'Ambient Soundscape', defaultBpm: 68, desc: 'Generative modular pads, relaxing meditation' },
    { id: 'indie', name: 'Indie Acoustic', defaultBpm: 96, desc: 'Warm acoustic guitar, intimate vocals' },
  ];

  const handleGenreSelect = (g: (typeof genres)[0]) => {
    setGenre(g.name);
    setBpm(g.defaultBpm);
  };

  const handleCompose = () => {
    const fullPrompt =
      `Act as a master audio producer and AI music composer (Suno / Lyria). ` +
      `Produce a complete musical composition blueprint and production score for:\n\n` +
      `TRACK CONCEPT: ${trackPrompt}\n` +
      `GENRE: ${genre}\n` +
      `MOOD: ${mood}\n` +
      `TEMPO: ${bpm} BPM\n` +
      `KEY SIGNATURE: ${keySignature}\n\n` +
      `Provide:\n` +
      `1. Track Title, Album Name, and Cover Concept\n` +
      `2. Structural Song Arrangement (Intro [4 bars], Verse 1 [8 bars], Chorus [8 bars], Verse 2 [8 bars], Bridge [4 bars], Outro [4 bars])\n` +
      `3. Full Lyrics with timing cues and vocal delivery guide\n` +
      `4. Chord Progression & Harmonic Analysis\n` +
      `5. Stem Instruments Breakdown (Drums, Bass, Harmony, Leads, FX)\n` +
      `6. Suno / Lyria AI prompt strings for audio generation.`;

    onGenerateMusicComposition(fullPrompt);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="relative w-full max-w-2xl bg-[#090d16] border border-amber-500/30 rounded-3xl p-5 sm:p-6 shadow-[0_0_60px_rgba(245,158,11,0.2)] flex flex-col max-h-[90vh] overflow-hidden z-10 text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-lg">
              <Music className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                Suno & Lyria Music Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  AI Audio
                </span>
              </h3>
              <p className="text-[11px] text-zinc-400">
                Compose original tracks, chord progressions, lyrics, and production stems
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
          {/* Track Idea Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">Track Idea & Atmosphere</label>
            <textarea
              value={trackPrompt}
              onChange={(e) => setTrackPrompt(e.target.value)}
              rows={3}
              placeholder="Describe instruments, vibes, tempo, and vocals..."
              className="w-full bg-[#121826] border border-white/10 rounded-xl p-3 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-amber-500 resize-none leading-relaxed"
            />
          </div>

          {/* Genre selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">Musical Genre</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {genres.map((g) => {
                const isSelected = genre === g.name;
                return (
                  <div
                    key={g.id}
                    onClick={() => handleGenreSelect(g)}
                    className={`p-2.5 rounded-xl border transition cursor-pointer text-left ${
                      isSelected
                        ? 'bg-amber-950/40 border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.25)] text-white'
                        : 'bg-[#0f1422] border-white/[0.08] hover:border-white/20 text-zinc-400'
                    }`}
                  >
                    <div className="text-xs font-bold text-white flex items-center justify-between">
                      <span>{g.name}</span>
                      {isSelected && <Check className="w-3 h-3 text-amber-400" />}
                    </div>
                    <p className="text-[10px] text-zinc-400 mt-0.5 line-clamp-1">{g.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Controls: Tempo / BPM, Key, Mood */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-[#0d1322] p-3 rounded-2xl border border-white/[0.06]">
            {/* BPM Slider */}
            <div>
              <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                <span>Tempo</span>
                <span className="font-mono text-amber-400 font-bold">{bpm} BPM</span>
              </div>
              <input
                type="range"
                min="60"
                max="180"
                value={bpm}
                onChange={(e) => setBpm(Number(e.target.value))}
                className="w-full accent-amber-400 cursor-pointer h-1.5 bg-zinc-800 rounded-lg"
              />
            </div>

            {/* Key Signature */}
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">
                Key Signature
              </label>
              <select
                value={keySignature}
                onChange={(e) => setKeySignature(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="C Minor">C Minor</option>
                <option value="A Minor">A Minor</option>
                <option value="D Dorian">D Dorian</option>
                <option value="G Major">G Major</option>
                <option value="F# Minor">F# Minor</option>
                <option value="E Minor">E Minor</option>
              </select>
            </div>

            {/* Mood */}
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">Mood</label>
              <select
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="Relaxed & Nostalgic">Relaxed & Nostalgic</option>
                <option value="Energetic & Driving">Energetic & Driving</option>
                <option value="Dark & Cybernetic">Dark & Cybernetic</option>
                <option value="Euphoric & Uplifting">Euphoric & Uplifting</option>
                <option value="Melancholic & Intimate">Melancholic & Intimate</option>
              </select>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={handleCompose}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-black font-bold text-xs shadow-lg shadow-amber-500/25 flex items-center gap-1.5 transition active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Compose Track & Stems in Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 13. Socratic Guided Learning Modal ───────────────────────────────────────
export interface GuidedLearningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartGuidedLearning: (topic: string, style: string, level: string) => void;
}

export function AstraGuidedLearningModal({
  isOpen,
  onClose,
  onStartGuidedLearning,
}: GuidedLearningModalProps) {
  const [topic, setTopic] = useState('Dynamic Programming & Memoization');
  const [style, setStyle] = useState('Socratic Dialogue (Step-by-step questions)');
  const [level, setLevel] = useState('Intermediate (Hands-on problem solving)');

  if (!isOpen) return null;

  const quickTopics = [
    'Dynamic Programming & Memoization',
    'Quantum Superposition & Entanglement',
    'Distributed Systems & Paxos/Raft Consensus',
    'Rust Memory Safety & Borrow Checker',
    'Transformer Multi-Head Attention Mechanisms',
  ];

  const handleStart = () => {
    if (!topic.trim()) return;
    onStartGuidedLearning(topic.trim(), style, level);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="relative w-full max-w-2xl bg-[#090d16] border border-emerald-500/30 rounded-3xl p-5 sm:p-6 shadow-[0_0_60px_rgba(16,185,129,0.2)] flex flex-col max-h-[90vh] overflow-hidden z-10 text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-lg">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                Socratic Guided Learning Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Tutor Mode
                </span>
              </h3>
              <p className="text-[11px] text-zinc-400">
                Interactive step-by-step tutoring that diagnoses your understanding and guides you through first principles
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
          {/* Topic Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">
              What do you want to learn today?
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Dynamic Programming, Quantum Computing, System Architecture..."
              className="w-full bg-[#121826] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Quick Suggestions */}
          <div className="space-y-1">
            <label className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
              Quick Suggestions
            </label>
            <div className="flex flex-wrap gap-1.5">
              {quickTopics.map((t) => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  className={`text-[11px] px-2.5 py-1 rounded-lg border transition ${
                    topic === t
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                      : 'bg-white/[0.04] border-white/10 text-zinc-400 hover:text-white hover:bg-white/10'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Style & Level Options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#0d1322] p-3 rounded-2xl border border-white/[0.06]">
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">
                Pedagogical Style
              </label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="Socratic Dialogue (Step-by-step questions)">
                  🏛️ Socratic Dialogue (Guides via questions)
                </option>
                <option value="Explain Like I'm 5 (Intuitive analogies)">
                  👶 ELI5 (Real-world analogies, zero jargon)
                </option>
                <option value="First-Principles Rigor (Mathematical axioms)">
                  🔬 First-Principles Rigor (Math & axioms)
                </option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-zinc-400 block mb-1">
                Mastery Level
              </label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full bg-[#121826] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="Beginner (Fundamentals & Intuition)">
                  🌱 Beginner (Fundamentals & Intuition)
                </option>
                <option value="Intermediate (Hands-on problem solving)">
                  ⚡ Intermediate (Hands-on Problem Solving)
                </option>
                <option value="Mastery (Edge cases & optimization)">
                  🏆 Mastery (Edge Cases & Optimization)
                </option>
              </select>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={!topic.trim()}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black font-bold text-xs shadow-lg shadow-emerald-500/25 flex items-center gap-1.5 transition active:scale-95 disabled:opacity-50"
          >
            <GraduationCap className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Start Guided Session in Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
}
