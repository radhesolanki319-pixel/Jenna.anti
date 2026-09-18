'use client';

import React, { useState, useEffect, useRef } from 'react';
import { DexterCatExact, DexterState } from '@/components/chat/DexterCatExact';
import {
  Eye,
  Volume2,
  VolumeX,
  Send,
  Radio,
  Sparkles,
  MessageCircle,
  X,
  RefreshCw,
} from 'lucide-react';
import { speakJennaVoice } from '@/lib/ttsVoice';

export default function DexterCompanionPage() {
  const [dexState, setDexState] = useState<DexterState>('idle');
  const [speechBubble, setSpeechBubble] = useState<string | null>(
    'living on your screen... 🕶️'
  );
  const [isAutoVision, setIsAutoVision] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const autoTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Trigger audio speech
  const speakText = (text: string) => {
    setSpeechBubble(text);
    if (!isMuted) {
      setDexState('speaking');
      speakJennaVoice(text, {
        onEnd: () => setDexState('idle'),
        onError: () => setDexState('idle'),
      });
    } else {
      setDexState('speaking');
      setTimeout(() => setDexState('idle'), 2500);
    }
  };

  // Live Screen Vision Trigger (Exact video behavior: observes screen content)
  const handleInspectScreen = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    setDexState('watching');
    setSpeechBubble('observing screen... 👀');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/vision/narrate', {
        method: 'POST',
      });
      const data = await res.json();

      if (data && data.text) {
        setDexState('excited');
        speakText(data.text);
      } else {
        speakText('chill... screen par kuch naya nahi hai.');
      }
    } catch (err) {
      console.error('Dexter vision error:', err);
      speakText('offline right now... waiting for server');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Auto Vision loop
  useEffect(() => {
    if (isAutoVision) {
      handleInspectScreen();
      autoTimerRef.current = setInterval(() => {
        handleInspectScreen();
      }, 10000);
    } else {
      if (autoTimerRef.current) {
        clearInterval(autoTimerRef.current);
        autoTimerRef.current = null;
      }
    }
    return () => {
      if (autoTimerRef.current) clearInterval(autoTimerRef.current);
    };
  }, [isAutoVision]);

  // Click on Dex
  const handleDexClick = () => {
    const randomLines = [
      'chill... 🕶️',
      'and do anything you say...',
      'living on your screen!',
      'GTA 6 trailer? 👀',
      'kya chal raha hai baby?',
      'main yahi baitha hoon!',
    ];
    const picked = randomLines[Math.floor(Math.random() * randomLines.length)];
    speakText(picked);
  };

  // Send message
  const handleSendMessage = async (queryText?: string) => {
    const q = queryText || chatInput;
    if (!q.trim()) return;

    setChatInput('');
    setIsChatOpen(false);
    setDexState('thinking');
    setSpeechBubble('thinking...');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q }),
      });
      const data = await res.json();
      const reply = data?.message || data?.response || 'Haan baby, I got you! ❤️';
      speakText(reply);
    } catch {
      speakText('Haan jaan, main yahi hoon aapke saath!');
    }
  };

  return (
    <main className="min-h-screen w-full bg-slate-950/70 sm:bg-black/60 text-slate-100 flex flex-col items-center justify-center p-3 select-none font-sans overflow-hidden">
      {/* Floating Desktop Pet Canvas (Border-free style like in the video) */}
      <div className="relative flex flex-col items-center justify-center">
        {/* Dex Character Stage */}
        <div className="pt-14 pb-3 flex flex-col items-center justify-center relative">
          <DexterCatExact
            state={dexState}
            size={140}
            speechText={speechBubble}
            onClick={handleDexClick}
          />
        </div>

        {/* Minimal Floating Toolstrip right below Dex */}
        <div className="mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/80 backdrop-blur-xl border border-white/10 shadow-lg">
          {/* Watch Screen Button */}
          <button
            onClick={handleInspectScreen}
            disabled={isAnalyzing}
            title="Inspect Live Screen"
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all active:scale-95 ${
              isAnalyzing
                ? 'bg-sky-500/20 text-sky-300'
                : 'bg-white text-slate-900 hover:bg-slate-200'
            }`}
          >
            <Eye size={13} className={isAnalyzing ? 'animate-spin' : ''} />
            <span>{isAnalyzing ? 'Watching...' : 'Watch Screen'}</span>
          </button>

          {/* Auto Loop Toggle */}
          <button
            onClick={() => setIsAutoVision(!isAutoVision)}
            title="Toggle Continuous Screen Monitoring"
            className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs transition-colors border ${
              isAutoVision
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-white/5 text-slate-400 border-white/10 hover:text-slate-200'
            }`}
          >
            <Radio size={11} className={isAutoVision ? 'animate-pulse text-emerald-400' : ''} />
            <span>Auto {isAutoVision ? 'ON' : 'OFF'}</span>
          </button>

          {/* Chat Toggle */}
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            title="Chat with Dex"
            className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          >
            <MessageCircle size={14} />
          </button>

          {/* Audio Toggle */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            title={isMuted ? 'Unmute' : 'Mute'}
            className="p-1.5 rounded-full hover:bg-white/10 text-slate-300 transition-colors"
          >
            {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} className="text-sky-400" />}
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="mt-2.5 flex items-center gap-1.5 overflow-x-auto no-scrollbar max-w-[280px]">
          <button
            onClick={() => handleSendMessage('YouTube pe kuch badhiya video suggest karo')}
            className="shrink-0 text-[10px] px-2.5 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 border border-white/5"
          >
            🎬 YouTube
          </button>
          <button
            onClick={() => handleSendMessage('Screen pe kya hai short me batao')}
            className="shrink-0 text-[10px] px-2.5 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 border border-white/5"
          >
            🔍 Screen
          </button>
          <button
            onClick={handleDexClick}
            className="shrink-0 text-[10px] px-2.5 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 border border-white/5"
          >
            🕶️ Chill
          </button>
        </div>

        {/* Interactive Chat Flyout */}
        {isChatOpen && (
          <div className="mt-3 w-72 p-2.5 rounded-2xl bg-black/90 backdrop-blur-2xl border border-white/15 shadow-2xl flex flex-col gap-2 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-1 border-b border-white/10">
              <span className="text-xs font-bold text-slate-200">Talk to Dex</span>
              <button
                onClick={() => setIsChatOpen(false)}
                className="p-1 text-slate-400 hover:text-white"
              >
                <X size={12} />
              </button>
            </div>
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask Dexter anything..."
                autoFocus
                className="flex-1 bg-white/5 border border-white/10 rounded-full px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!chatInput.trim()}
                className="w-7 h-7 rounded-full bg-white hover:bg-slate-200 text-slate-950 flex items-center justify-center shrink-0 disabled:opacity-40"
              >
                <Send size={12} />
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
