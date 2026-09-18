'use client';

import React from 'react';

export type DexterState = 'idle' | 'watching' | 'thinking' | 'speaking' | 'excited' | 'chilling';

interface DexterCatExactProps {
  state?: DexterState;
  size?: number;
  className?: string;
  speechText?: string | null;
  onClick?: () => void;
  showShadow?: boolean;
}

export function DexterCatExact({
  state = 'idle',
  size = 150,
  className = '',
  speechText = null,
  onClick,
  showShadow = true,
}: DexterCatExactProps) {
  const isSpeaking = state === 'speaking';
  const isThinking = state === 'thinking';
  const isWatching = state === 'watching';
  const isExcited = state === 'excited';
  const isChilling = state === 'chilling';

  return (
    <div
      onClick={onClick}
      className={`relative select-none flex flex-col items-center justify-end cursor-pointer group transition-transform duration-200 active:scale-95 ${className}`}
      style={{ width: size, height: size * 1.15 }}
    >
      {/* Speech Bubble (Exact Dexter style from video) */}
      {speechText && (
        <div className="absolute -top-16 z-40 max-w-[280px] px-3.5 py-1.5 rounded-2xl bg-white text-slate-900 font-semibold text-xs tracking-tight shadow-[0_6px_25px_rgba(0,0,0,0.5)] border border-slate-200 animate-bounce-subtle pointer-events-none">
          <p className="line-clamp-2 leading-tight text-center">{speechText}</p>
          {/* Bubble Tail */}
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-r border-b border-slate-200 rotate-45" />
        </div>
      )}

      {/* Subtle Ground Shadow */}
      {showShadow && (
        <div className="absolute bottom-1 w-2/3 h-2.5 bg-black/40 rounded-full blur-[3px] pointer-events-none" />
      )}

      <svg
        viewBox="0 0 200 220"
        className={`w-full h-full overflow-visible ${
          isSpeaking ? 'animate-talk-bob' : isExcited ? 'animate-bounce-subtle' : ''
        }`}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Pure Clean White Cat Fill */}
          <linearGradient id="dexWhite" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#f3f4f6" />
          </linearGradient>

          {/* Jet Black Pitch Shirt Fill */}
          <linearGradient id="dexShirtBlack" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#111827" />
            <stop offset="100%" stopColor="#030712" />
          </linearGradient>
        </defs>

        {/* --- TAIL (Curving upwards on the right side) --- */}
        <g
          className="origin-[145px_175px]"
          style={{
            transformOrigin: '145px 175px',
            animation: isExcited ? 'tailFast 0.6s ease-in-out infinite' : 'tailSlow 2.5s ease-in-out infinite',
          }}
        >
          <path
            d="M 145 178 C 175 180, 192 150, 185 130 C 180 120, 168 124, 172 134 C 178 148, 162 166, 142 168 Z"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>

        {/* --- LOWER BODY / LEGS --- */}
        <g>
          {/* Left Foot */}
          <path
            d="M 72 196 C 72 206, 92 206, 92 196 Z"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
          />
          {/* Right Foot */}
          <path
            d="M 108 196 C 108 206, 128 206, 128 196 Z"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
          />
        </g>

        {/* --- BLACK T-SHIRT WITH 'dex' --- */}
        <g>
          {/* Shirt Main Body */}
          <path
            d="M 58 142 Q 100 150 142 142 L 146 195 Q 100 200 54 195 Z"
            fill="url(#dexShirtBlack)"
            stroke="#111827"
            strokeWidth="4"
            strokeLinejoin="round"
          />
          {/* Left Short Sleeve */}
          <path
            d="M 60 142 L 40 162 L 52 170 L 64 154 Z"
            fill="url(#dexShirtBlack)"
            stroke="#111827"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          {/* Right Short Sleeve */}
          <path
            d="M 140 142 L 160 162 L 148 170 L 136 154 Z"
            fill="url(#dexShirtBlack)"
            stroke="#111827"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />

          {/* Pure Bold White Lowercase 'dex' Logo */}
          <text
            x="100"
            y="178"
            textAnchor="middle"
            fill="#ffffff"
            fontFamily="'Inter', -apple-system, system-ui, BlinkMacSystemFont, sans-serif"
            fontWeight="900"
            fontSize="18"
            letterSpacing="-0.5"
            className="select-none"
          >
            dex
          </text>
        </g>

        {/* --- ARMS / PAWS --- */}
        {/* Left Arm (Resting on side/hip) */}
        <path
          d="M 42 164 C 36 178, 48 186, 56 178 Z"
          fill="url(#dexWhite)"
          stroke="#111827"
          strokeWidth="3.5"
        />
        {/* Right Arm (Resting on side/hip) */}
        <path
          d="M 158 164 C 164 178, 152 186, 144 178 Z"
          fill="url(#dexWhite)"
          stroke="#111827"
          strokeWidth="3.5"
        />

        {/* --- HEAD & FACE --- */}
        <g
          className="origin-[100px_90px]"
          style={{
            transform: isWatching ? 'rotate(-3deg)' : isChilling ? 'rotate(2deg)' : 'none',
            transition: 'transform 0.3s ease',
          }}
        >
          {/* EARS */}
          {/* Left Ear */}
          <polygon
            points="58,64 36,12 86,42"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
            strokeLinejoin="round"
          />
          {/* Left Inner Ear Crease */}
          <path d="M 52 38 L 48 26 L 68 38" fill="none" stroke="#111827" strokeWidth="2.5" strokeLinecap="round" />

          {/* Right Ear */}
          <polygon
            points="142,64 164,12 114,42"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
            strokeLinejoin="round"
          />
          {/* Right Inner Ear Crease */}
          <path d="M 148 38 L 152 26 L 132 38" fill="none" stroke="#111827" strokeWidth="2.5" strokeLinecap="round" />

          {/* Cat Head Base (Chubby white with cheek tufts) */}
          <path
            d="M 56 62 
               C 70 50, 130 50, 144 62 
               C 158 72, 168 85, 162 96
               L 174 102 L 158 108 L 170 116 L 152 122
               C 136 142, 64 142, 48 122
               L 30 116 L 42 108 L 26 102 L 38 96
               C 32 85, 42 72, 56 62 Z"
            fill="url(#dexWhite)"
            stroke="#111827"
            strokeWidth="4"
            strokeLinejoin="round"
          />

          {/* Tiny Nose */}
          <polygon points="97,100 103,100 100,104" fill="#111827" />

          {/* Cat Mouth (人 inverted Y) */}
          {isSpeaking ? (
            <path
              d="M 94 108 Q 100 120 106 108 Z"
              fill="#ef4444"
              stroke="#111827"
              strokeWidth="2"
            />
          ) : (
            <path
              d="M 93 107 Q 96 111 100 106 Q 104 111 107 107"
              fill="none"
              stroke="#111827"
              strokeWidth="3"
              strokeLinecap="round"
            />
          )}

          {/* --- SIGNATURE PITCH-BLACK ROUND SUNGLASSES --- */}
          <g>
            {/* Frame Top Connecting Bar */}
            <line x1="48" y1="78" x2="152" y2="78" stroke="#111827" strokeWidth="4.5" strokeLinecap="round" />

            {/* Left Round Glass */}
            <circle
              cx="74"
              cy="80"
              r="22"
              fill="#09090b"
              stroke="#111827"
              strokeWidth="4.5"
            />
            {/* Right Round Glass */}
            <circle
              cx="126"
              cy="80"
              r="22"
              fill="#09090b"
              stroke="#111827"
              strokeWidth="4.5"
            />

            {/* Subtle Glint Reflection */}
            <path
              d="M 64 70 A 16 16 0 0 1 84 70"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2.5"
              strokeLinecap="round"
              opacity="0.25"
            />
            <path
              d="M 116 70 A 16 16 0 0 1 136 70"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2.5"
              strokeLinecap="round"
              opacity="0.25"
            />
          </g>

          {/* Thinking / Watching Indicator */}
          {isWatching && (
            <circle cx="100" cy="30" r="5" fill="#38bdf8" className="animate-ping" />
          )}
          {isThinking && (
            <circle cx="100" cy="30" r="10" fill="none" stroke="#a855f7" strokeWidth="2.5" strokeDasharray="5 3" className="animate-spin" />
          )}
        </g>
      </svg>

      <style jsx>{`
        @keyframes tailSlow {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(14deg); }
        }
        @keyframes tailFast {
          0%, 100% { transform: rotate(-6deg); }
          50% { transform: rotate(20deg); }
        }
        @keyframes talkBob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }
        @keyframes bounceSubtle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-talk-bob {
          animation: talkBob 0.3s ease-in-out infinite;
        }
        .animate-bounce-subtle {
          animation: bounceSubtle 1.8s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
