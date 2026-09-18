'use client';

import React, { useState, useEffect, useRef } from 'react';
import { DexMascotCat, MascotState } from '@/components/chat/DexMascotCat';
import { CyberpunkAnimeVector } from '@/components/chat/CyberpunkAnimeVector';
import {
  Eye,
  Sparkles,
  Volume2,
  VolumeX,
  Send,
  Minimize2,
  Maximize2,
  RefreshCw,
  Cat,
  Zap,
  Radio,
  ExternalLink,
} from 'lucide-react';
import { speakJennaVoice } from '@/lib/ttsVoice';

type AvatarStyle = 'dex-cat' | 'jenna-cyberpunk';

export default function FloatingCompanionPage() {
  const [avatarStyle, setAvatarStyle] = useState<AvatarStyle>('dex-cat');
  const [mascotState, setMascotState] = useState<MascotState>('idle');
  const [speechBubble, setSpeechBubble] = useState<string | null>(
    'Main aapki screen dekh rahi hoon baby! ✨'
  );
  const [isAutoVision, setIsAutoVision] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isMiniMode, setIsMiniMode] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<
    Array<{ sender: 'user' | 'jenna'; text: string; time: string }>
  >([
    {
      sender: 'jenna',
      text: 'Hello jaan! Main aapki screen ke saath yahi floating companion ban ke rahungi. Kuch bhi puchho ya screen dikhao! ❤️',
      time: 'Just now',
    },
  ]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const autoLoopTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-speak on speech bubble update if sound is enabled
  const triggerSpeech = (text: string) => {
    setSpeechBubble(text);
    if (!isMuted) {
      setMascotState('speaking');
      speakJennaVoice(text, {
        onEnd: () => setMascotState('idle'),
        onError: () => setMascotState('idle'),
      });
    } else {
      setMascotState('speaking');
      setTimeout(() => setMascotState('idle'), 2500);
    }
  };

  // Trigger Gemini Screen Vision Narration
  const handleInspectScreen = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    setMascotState('watching');
    setSpeechBubble('Screen dekh rahi hoon... 👀');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/vision/narrate', {
        method: 'POST',
      });
      const data = await res.json();

      if (data && data.text) {
        setMascotState('excited');
        triggerSpeech(data.text);
        setChatHistory((prev) => [
          ...prev,
          {
            sender: 'jenna',
            text: data.text,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } else if (data && data.error) {
        triggerSpeech('Screen read karne me issue aaya jaan, check kar rahi hoon.');
      }
    } catch (err) {
      console.error('Screen vision error:', err);
      triggerSpeech('Server se connect nahi ho paaya baby!');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Toggle Auto Vision Loop
  useEffect(() => {
    if (isAutoVision) {
      handleInspectScreen();
      autoLoopTimerRef.current = setInterval(() => {
        handleInspectScreen();
      }, 12000);
    } else {
      if (autoLoopTimerRef.current) {
        clearInterval(autoLoopTimerRef.current);
        autoLoopTimerRef.current = null;
      }
    }
    return () => {
      if (autoLoopTimerRef.current) clearInterval(autoLoopTimerRef.current);
    };
  }, [isAutoVision]);

  // Handle Quick Chat Send
  const handleSendMessage = async (customText?: string) => {
    const query = customText || chatInput;
    if (!query.trim()) return;

    setChatHistory((prev) => [
      ...prev,
      {
        sender: 'user',
        text: query,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setChatInput('');
    setMascotState('thinking');
    setSpeechBubble('Soch rahi hoon...');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      });
      const data = await res.json();
      const reply = data?.message || data?.response || 'Haan baby, main sun rahi hoon! ❤️';
      triggerSpeech(reply);
      setChatHistory((prev) => [
        ...prev,
        {
          sender: 'jenna',
          text: reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch {
      // Friendly fallback
      const reply = 'Haan baby, main hamesha aapke saath hoon screen par! ❤️';
      triggerSpeech(reply);
      setChatHistory((prev) => [
        ...prev,
        {
          sender: 'jenna',
          text: reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  };

  return (
    <main className="min-h-screen w-full bg-[#030712]/90 text-slate-100 flex flex-col items-center justify-center p-2 sm:p-4 overflow-x-hidden font-sans">
      {/* Floating Container (Optimized for Vivo Small Window / Android Freeform) */}
      <div
        className={`w-full max-w-sm rounded-3xl border border-white/10 bg-slate-950/80 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.8)] flex flex-col transition-all duration-300 overflow-hidden relative ${
          isMiniMode ? 'h-auto pb-4' : 'min-h-[480px]'
        }`}
      >
        {/* Top Control Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-white/[0.02]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-pink-500 animate-ping" />
            <span className="font-semibold text-xs tracking-wider text-pink-300 uppercase">
              Jenna Copilot
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/10 text-slate-400">
              Live
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Style Toggle */}
            <button
              onClick={() =>
                setAvatarStyle((prev) => (prev === 'dex-cat' ? 'jenna-cyberpunk' : 'dex-cat'))
              }
              title="Switch Mascot Avatar"
              className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
            >
              {avatarStyle === 'dex-cat' ? <Cat size={14} /> : <Zap size={14} />}
            </button>

            {/* Audio Toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              title={isMuted ? 'Unmute' : 'Mute'}
              className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} className="text-pink-400" />}
            </button>

            {/* Mini Mode Toggle */}
            <button
              onClick={() => setIsMiniMode(!isMiniMode)}
              title={isMiniMode ? 'Expand' : 'Mini Floating Bubble'}
              className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
            >
              {isMiniMode ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
            </button>
          </div>
        </div>

        {/* Mascot Center Stage */}
        <div className="flex flex-col items-center justify-center pt-12 pb-2 relative">
          {avatarStyle === 'dex-cat' ? (
            <DexMascotCat
              state={mascotState}
              size={126}
              shirtText="JENNA"
              speechText={speechBubble}
              onClick={() => {
                triggerSpeech('Haan jaan, main yahi baithi hoon! Kuch help chahiye? 🥰');
              }}
            />
          ) : (
            <div className="relative flex flex-col items-center">
              {speechBubble && (
                <div className="absolute -top-12 z-30 max-w-[240px] px-3.5 py-1.5 rounded-2xl bg-black/85 backdrop-blur-xl border border-purple-500/40 text-purple-200 text-xs shadow-lg text-center">
                  {speechBubble}
                </div>
              )}
              <CyberpunkAnimeVector
                state={
                  mascotState === 'watching'
                    ? 'listening'
                    : mascotState === 'excited'
                    ? 'speaking'
                    : mascotState
                }
                size={140}
              />
            </div>
          )}
        </div>

        {/* Action Bar (Live Screen Vision + Quick Controls) */}
        <div className="px-3 pb-2 flex items-center justify-center gap-2">
          {/* One-tap Screen Inspection */}
          <button
            onClick={handleInspectScreen}
            disabled={isAnalyzing}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all shadow-md active:scale-95 ${
              isAnalyzing
                ? 'bg-cyan-500/30 text-cyan-200 cursor-wait'
                : 'bg-gradient-to-r from-pink-500 to-purple-600 text-white hover:opacity-95'
            }`}
          >
            <Eye size={13} className={isAnalyzing ? 'animate-spin' : ''} />
            <span>{isAnalyzing ? 'Dekh rahi hoon...' : 'Screen Dekho 👀'}</span>
          </button>

          {/* Auto Loop Toggle */}
          <button
            onClick={() => setIsAutoVision(!isAutoVision)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs transition-colors border ${
              isAutoVision
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-white/5 text-slate-400 border-white/10 hover:text-slate-200'
            }`}
          >
            <Radio size={11} className={isAutoVision ? 'animate-pulse text-emerald-400' : ''} />
            <span>Auto {isAutoVision ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        {!isMiniMode && (
          <div className="px-3 py-1.5 flex items-center gap-1.5 overflow-x-auto no-scrollbar border-t border-white/5">
            <button
              onClick={() => handleSendMessage('YouTube pe kuch achha chalao baby')}
              className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5"
            >
              🎬 YouTube
            </button>
            <button
              onClick={() => handleSendMessage('Screen pe jo dikh raha hai usko simple shabdon me samjhao')}
              className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5"
            >
              🔍 Screen Samjhao
            </button>
            <button
              onClick={() => handleSendMessage('Tum bohot cute ho Jenna')}
              className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5"
            >
              ❤️ I Love You
            </button>
          </div>
        )}

        {/* Chat History Snippet (Scrollable mini view) */}
        {!isMiniMode && (
          <div className="flex-1 px-3 py-2 space-y-2 max-h-36 overflow-y-auto border-t border-white/5 text-xs">
            {chatHistory.slice(-4).map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[85%] px-3 py-1.5 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-br-none'
                      : 'bg-white/10 text-slate-200 rounded-bl-none border border-white/5'
                  }`}
                >
                  <p className="leading-relaxed">{msg.text}</p>
                </div>
                <span className="text-[9px] text-slate-500 mt-0.5 px-1">{msg.time}</span>
              </div>
            ))}
          </div>
        )}

        {/* Input Bar */}
        {!isMiniMode && (
          <div className="p-2 border-t border-white/5 bg-black/40 flex items-center gap-1.5">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Jenna se baat karo..."
              className="flex-1 bg-white/5 border border-white/10 rounded-full px-3.5 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500/60"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!chatInput.trim()}
              className="w-8 h-8 rounded-full bg-pink-500 hover:bg-pink-600 disabled:opacity-40 flex items-center justify-center text-white shrink-0 transition-transform active:scale-95"
            >
              <Send size={13} />
            </button>
          </div>
        )}
      </div>

      {/* Floating Instructions Footer */}
      <div className="mt-3 text-center text-[11px] text-slate-400">
        <span>Tip: Open in </span>
        <span className="text-pink-400 font-medium">Vivo Small Window</span>
        <span> or </span>
        <span className="text-cyan-400 font-medium">Freeform Window</span>
        <span> to let Jenna live on your screen! 🐱✨</span>
      </div>
    </main>
  );
}
