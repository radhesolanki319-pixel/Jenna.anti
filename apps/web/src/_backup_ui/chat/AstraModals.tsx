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
} from 'lucide-react';

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
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-xl transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-md bg-[#0a0e19]/95 border border-cyan-500/30 rounded-3xl p-8 shadow-[0_0_50px_rgba(6,182,212,0.25)] flex flex-col items-center text-center z-10">
        {/* Top bar */}
        <div className="w-full flex items-center justify-between mb-8">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span className="text-xs font-semibold tracking-wider uppercase text-cyan-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            Voice Mode
          </span>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Central Glowing Visualizer Orb & Waves */}
        <div className="relative my-8 flex flex-col items-center justify-center">
          {/* Audio Wave Frequency Bars */}
          <div className="flex items-center gap-1.5 mb-6 h-12">
            <div className="w-1.5 bg-cyan-400 rounded-full animate-sound-1" />
            <div className="w-1.5 bg-blue-400 rounded-full animate-sound-2" />
            <div className="w-1.5 bg-indigo-400 rounded-full animate-sound-3" />
            <div className="w-1.5 bg-cyan-300 rounded-full animate-sound-4" />
            <div className="w-1.5 bg-purple-400 rounded-full animate-sound-5" />
            <div className="w-1.5 bg-cyan-400 rounded-full animate-sound-2" />
            <div className="w-1.5 bg-blue-300 rounded-full animate-sound-4" />
          </div>

          {/* Central Pulsing Mic Orb */}
          <div className="relative">
            <div className="w-28 h-28 rounded-full bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-[0_0_40px_rgba(6,182,212,0.5)] animate-astra-orb">
              <Mic className="w-12 h-12" />
            </div>
            <div className="absolute -inset-3 rounded-full border border-cyan-400/40 animate-astra-ring pointer-events-none" />
          </div>

          <p className="mt-8 text-lg font-medium text-white tracking-wide">
            {assistantSpeaking ? 'Astra is speaking...' : isListening ? 'Listening...' : 'Microphone paused'}
          </p>
          <p className="text-xs text-zinc-400 mt-1 max-w-xs">
            {transcript ? `"${transcript}"` : 'Speak naturally in English, Hindi, or Hinglish.'}
          </p>
        </div>

        {/* Bottom Control Actions */}
        <div className="flex items-center gap-6 mt-4">
          <button
            onClick={onToggleListening}
            className={`flex flex-col items-center gap-1.5 text-xs transition ${
              isListening ? 'text-zinc-300 hover:text-white' : 'text-amber-400'
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-white/[0.08] hover:bg-white/[0.15] border border-white/10 flex items-center justify-center text-white transition">
              {isListening ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5 text-amber-400" />}
            </div>
            <span>{isListening ? 'Mute' : 'Unmute'}</span>
          </button>

          <button
            onClick={onClose}
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

      <div className="relative w-full max-w-3xl h-[560px] bg-[#0c101b]/95 border border-white/10 rounded-2xl shadow-2xl flex overflow-hidden z-10">
        {/* Left Sidebar Tabs */}
        <aside className="w-56 border-r border-white/[0.08] bg-[#080c15] p-3 flex flex-col justify-between">
          <div>
            <div className="px-3 py-2 text-xs font-bold uppercase tracking-wider text-zinc-400">
              Settings
            </div>
            <nav className="space-y-0.5 mt-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 font-semibold border border-blue-500/30'
                        : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-2 border-t border-white/[0.06] text-[11px] text-zinc-500">
            Astra AI v6.2 · Radhe Edition
          </div>
        </aside>

        {/* Right Form Content */}
        <div className="flex-1 flex flex-col justify-between p-6 overflow-y-auto">
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
      onUseImagePrompt(`Generated image concept for: "${prompt}"`);
      onClose();
    }, 1200);
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
