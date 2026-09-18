'use client';

import React, { useState } from 'react';
import { Sparkles, Mic, Volume2, ShieldCheck, Zap } from 'lucide-react';
import { CyberpunkAnimeVector, CyberpunkState } from './CyberpunkAnimeVector';
import { speakJennaVoice } from '@/lib/ttsVoice';

export type JennaState = CyberpunkState;

interface AstraAnimatedJennaProps {
  mode?: 'hero' | 'voice' | 'chat-banner' | 'avatar';
  state?: JennaState;
  onTriggerVoice?: () => void;
  interactive?: boolean;
  className?: string;
}

export function AstraAnimatedJenna({
  mode = 'hero',
  state = 'idle',
  onTriggerVoice,
  interactive = true,
  className = '',
}: AstraAnimatedJennaProps) {
  const [localSpeaking, setLocalSpeaking] = useState(false);
  const [speechBubbleText, setSpeechBubbleText] = useState<string | null>(null);

  const currentState: JennaState = localSpeaking ? 'speaking' : state;

  const handleHeroClick = () => {
    if (!interactive) return;
    setLocalSpeaking(true);
    setSpeechBubbleText('Hello! Main Jenna hoon, aapki Cyberpunk AI Companion! ✨');
    speakJennaVoice(
      'Hello! Main Jenna hoon, aapki Cyberpunk AI Companion. Aaj hum kya explore karein?',
      {
        onEnd: () => {
          setLocalSpeaking(false);
          setTimeout(() => setSpeechBubbleText(null), 2500);
        },
        onError: () => {
          setLocalSpeaking(false);
          setSpeechBubbleText(null);
        },
      }
    );
  };

  // ─── 1. AVATAR MODE (For Assistant Messages & Topbar) ────────────────
  if (mode === 'avatar') {
    return (
      <div
        className={`relative w-8 h-8 sm:w-9 sm:h-9 rounded-2xl p-[1.5px] bg-gradient-to-tr from-cyan-500 via-purple-600 to-pink-500 shadow-[0_0_15px_rgba(168,85,247,0.45)] shrink-0 select-none group transition-transform hover:scale-105 ${className}`}
        title="Jenna AI · Cyberpunk"
      >
        <div className="w-full h-full rounded-[14px] bg-[#090d16] flex items-center justify-center overflow-hidden relative">
          <CyberpunkAnimeVector
            state={currentState}
            size={34}
            showHoloRings={false}
            showParticles={false}
          />
          {/* Status Indicator Dot */}
          <span
            className={`absolute bottom-0.5 right-0.5 w-2 h-2 rounded-full border border-[#090d16] ${
              currentState === 'speaking'
                ? 'bg-pink-400 animate-ping'
                : currentState === 'thinking'
                ? 'bg-cyan-400 animate-spin'
                : 'bg-emerald-400'
            }`}
          />
        </div>
      </div>
    );
  }

  // ─── 2. CHAT BANNER COMPANION (Top of Active Chat Stream) ─────────────
  if (mode === 'chat-banner') {
    return (
      <div
        className={`w-full max-w-3xl mx-auto mb-4 p-3 rounded-2xl bg-gradient-to-r from-purple-950/40 via-[#0a0f1d]/90 to-cyan-950/40 border border-purple-500/30 backdrop-blur-xl flex items-center justify-between shadow-[0_4px_25px_rgba(0,0,0,0.5)] select-none relative overflow-hidden ${className}`}
      >
        {/* Ambient Neon Backlight */}
        <div className="absolute -left-10 top-0 w-32 h-32 bg-purple-600/20 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -right-10 bottom-0 w-32 h-32 bg-cyan-600/20 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center gap-3 min-w-0 relative z-10">
          <div
            onClick={handleHeroClick}
            className="cursor-pointer transition-transform hover:scale-105 shrink-0"
            title="Click to talk with Jenna"
          >
            <CyberpunkAnimeVector
              state={currentState}
              size={52}
              showHoloRings={true}
              showParticles={false}
            />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs sm:text-sm font-bold text-white tracking-wide">
                Jenna AI
              </span>
              <span className="text-[9px] font-semibold text-cyan-300 bg-cyan-500/15 border border-cyan-500/30 px-1.5 py-0.2 rounded-full flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5" />
                Cyberpunk Companion
              </span>
            </div>
            <div className="text-[10px] sm:text-[11px] text-zinc-400 flex items-center gap-1.5 truncate mt-0.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  currentState === 'speaking'
                    ? 'bg-pink-400 animate-ping'
                    : currentState === 'thinking'
                    ? 'bg-cyan-400 animate-ping'
                    : 'bg-emerald-400 animate-pulse'
                }`}
              />
              <span className="truncate">
                {currentState === 'speaking'
                  ? 'Speaking with Natural Warm Voice...'
                  : currentState === 'thinking'
                  ? 'Analyzing neural thoughts...'
                  : 'Neural Core Online · Ready to assist'}
              </span>
            </div>
          </div>
        </div>

        {onTriggerVoice && (
          <button
            onClick={onTriggerVoice}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600/40 to-cyan-600/40 hover:from-purple-600/60 hover:to-cyan-600/60 border border-purple-400/40 text-cyan-300 hover:text-white text-xs font-semibold transition shadow-[0_0_15px_rgba(6,182,212,0.3)] shrink-0 relative z-10"
          >
            <Mic className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Voice Studio</span>
          </button>
        )}
      </div>
    );
  }

  // ─── 3. VOICE STUDIO MODE (Full Interactive Modal Centerpiece) ────────
  if (mode === 'voice') {
    return (
      <div className={`relative flex flex-col items-center justify-center my-3 select-none ${className}`}>
        {/* Floating Cyber Hologram Stage */}
        <div className="relative w-52 h-52 sm:w-60 sm:h-60 flex items-center justify-center">
          {/* Radial Neon Backlight Aura */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-purple-600/30 via-cyan-500/25 to-pink-500/30 blur-3xl animate-pulse" />

          {/* Central Cyberpunk Anime Vector Illustration */}
          <div className="relative z-10 animate-anime-float">
            <CyberpunkAnimeVector
              state={currentState}
              size={210}
              showHoloRings={true}
              showParticles={true}
            />
          </div>
        </div>

        {/* Dynamic State Indicator */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs sm:text-sm font-bold tracking-wider uppercase bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
            {currentState === 'listening'
              ? '● Listening to your voice...'
              : currentState === 'thinking'
              ? '● Jenna is thinking...'
              : currentState === 'speaking'
              ? '● Jenna Speaking (Natural Voice)...'
              : '● Jenna Ready'}
          </span>
        </div>

        {/* Live Audio Frequency Waves */}
        <div className="flex items-center gap-1.5 mt-3 h-6">
          <div
            className={`w-1.5 bg-cyan-400 rounded-full ${
              currentState === 'speaking' || currentState === 'listening'
                ? 'animate-cyber-eq-1'
                : 'h-2'
            }`}
          />
          <div
            className={`w-1.5 bg-purple-400 rounded-full ${
              currentState === 'speaking' || currentState === 'listening'
                ? 'animate-cyber-eq-2'
                : 'h-3'
            }`}
          />
          <div
            className={`w-1.5 bg-pink-400 rounded-full ${
              currentState === 'speaking' || currentState === 'listening'
                ? 'animate-cyber-eq-3'
                : 'h-1.5'
            }`}
          />
          <div
            className={`w-1.5 bg-cyan-300 rounded-full ${
              currentState === 'speaking' || currentState === 'listening'
                ? 'animate-cyber-eq-4'
                : 'h-4'
            }`}
          />
          <div
            className={`w-1.5 bg-purple-300 rounded-full ${
              currentState === 'speaking' || currentState === 'listening'
                ? 'animate-cyber-eq-2'
                : 'h-2'
            }`}
          />
        </div>
      </div>
    );
  }

  // ─── 4. HERO MODE (Centerpiece on Home Dashboard) ─────────────────────
  return (
    <div className={`flex flex-col items-center justify-center my-2 sm:my-4 relative z-10 select-none ${className}`}>
      {/* Speech Bubble on click or talk */}
      {speechBubbleText && (
        <div className="animate-in fade-in zoom-in-95 duration-200 mb-2 px-3.5 py-1.5 rounded-2xl bg-[#0e1424]/95 border border-cyan-500/50 text-xs text-white shadow-[0_0_25px_rgba(6,182,212,0.4)] backdrop-blur-xl flex items-center gap-2 max-w-xs text-center z-20">
          <Volume2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 animate-bounce" />
          <span>{speechBubbleText}</span>
        </div>
      )}

      {/* Centerpiece Vector Container */}
      <div
        onClick={handleHeroClick}
        className="cursor-pointer group relative flex items-center justify-center transition transform hover:scale-[1.03] active:scale-[0.98]"
        title="Click to talk with Jenna ✨"
      >
        {/* Outer Radiant Glow */}
        <div className="absolute -inset-4 rounded-full bg-gradient-to-tr from-purple-600/25 via-pink-500/20 to-cyan-500/25 blur-2xl group-hover:blur-3xl transition-all duration-300" />

        {/* Animated Cyberpunk Anime Girl Vector */}
        <div className="relative z-10 animate-anime-float">
          <CyberpunkAnimeVector
            state={currentState}
            size={180}
            showHoloRings={true}
            showParticles={true}
          />
        </div>

        {/* Hover Micro Badge */}
        <div className="absolute -bottom-2 px-2.5 py-0.5 rounded-full bg-[#0a0e19]/90 border border-purple-500/40 text-[9px] font-semibold text-purple-300 tracking-wider uppercase shadow-lg backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity z-20 flex items-center gap-1">
          <Mic className="w-2.5 h-2.5 text-cyan-400" />
          <span>Tap to speak</span>
        </div>
      </div>
    </div>
  );
}
