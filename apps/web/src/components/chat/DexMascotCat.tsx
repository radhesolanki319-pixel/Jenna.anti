'use client';

import React from 'react';

export type MascotState = 'idle' | 'watching' | 'thinking' | 'speaking' | 'excited';

interface DexMascotCatProps {
  state?: MascotState;
  size?: number;
  className?: string;
  shirtText?: string;
  speechText?: string | null;
  onClick?: () => void;
}

export function DexMascotCat({
  state = 'idle',
  size = 140,
  className = '',
  shirtText = 'JENNA',
  speechText = null,
  onClick,
}: DexMascotCatProps) {
  const isSpeaking = state === 'speaking';
  const isThinking = state === 'thinking';
  const isWatching = state === 'watching';
  const isExcited = state === 'excited';

  return (
    <div
      onClick={onClick}
      className={`relative select-none flex flex-col items-center justify-end cursor-pointer group transition-transform duration-300 hover:scale-105 active:scale-95 ${className}`}
      style={{ width: size, height: size * 1.1 }}
    >
      {/* Dynamic Speech Bubble */}
      {speechText && (
        <div className="absolute -top-16 z-30 max-w-[260px] px-3.5 py-2 rounded-2xl bg-black/85 backdrop-blur-xl border border-pink-500/40 text-pink-100 text-xs shadow-[0_4px_20px_rgba(236,72,153,0.35)] animate-bounce-subtle pointer-events-none">
          <p className="line-clamp-3 leading-tight font-medium text-center">{speechText}</p>
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-black/85 border-r border-b border-pink-500/40 rotate-45" />
        </div>
      )}

      {/* Floating Aura Halo */}
      <div
        className={`absolute inset-0 rounded-full blur-2xl transition-opacity duration-700 pointer-events-none ${
          isSpeaking
            ? 'bg-pink-500/30 opacity-100 animate-pulse'
            : isWatching
            ? 'bg-cyan-500/25 opacity-90'
            : isThinking
            ? 'bg-purple-500/30 opacity-80 animate-spin-slow'
            : 'bg-emerald-500/15 opacity-60'
        }`}
      />

      <svg
        viewBox="0 0 200 220"
        className={`w-full h-full overflow-visible drop-shadow-[0_8px_16px_rgba(0,0,0,0.6)] ${
          isSpeaking ? 'animate-wiggle-soft' : isExcited ? 'animate-bounce-subtle' : ''
        }`}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Fur Gradient */}
          <linearGradient id="catFur" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#e2e8f0" />
          </linearGradient>

          {/* Ear Inner Pink Gradient */}
          <linearGradient id="earPink" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f472b6" />
            <stop offset="100%" stopColor="#db2777" />
          </linearGradient>

          {/* Sunglasses Mirror Gradient */}
          <linearGradient id="sunglassGlint" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="40%" stopColor="#0f172a" />
            <stop offset="45%" stopColor="#38bdf8" />
            <stop offset="60%" stopColor="#020617" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>

          {/* Shirt Gradient */}
          <linearGradient id="shirtGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#18181b" />
            <stop offset="100%" stopColor="#09090b" />
          </linearGradient>

          {/* Neon Glow Filter */}
          <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#f43f5e" floodOpacity="0.7" />
          </filter>
        </defs>

        {/* --- TAIL (Animated Swish) --- */}
        <g
          className="origin-[155px_175px]"
          style={{
            transformOrigin: '155px 175px',
            animation: isExcited ? 'swishFast 0.8s ease-in-out infinite' : 'swishSlow 3s ease-in-out infinite',
          }}
        >
          <path
            d="M 155 175 C 185 170, 195 130, 175 110 C 165 100, 150 115, 158 125 C 170 138, 160 160, 145 168 Z"
            fill="url(#catFur)"
            stroke="#0f172a"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>

        {/* --- BODY (Sitting Pose) --- */}
        <ellipse cx="100" cy="165" rx="46" ry="42" fill="url(#catFur)" stroke="#0f172a" strokeWidth="3.5" />

        {/* --- SHIRT (Black T-shirt with Logo) --- */}
        <path
          d="M 62 145 Q 100 152 138 145 L 142 195 Q 100 202 58 195 Z"
          fill="url(#shirtGrad)"
          stroke="#0f172a"
          strokeWidth="3.5"
        />
        {/* Shirt Collar V-cut */}
        <path d="M 86 148 Q 100 158 114 148" fill="none" stroke="#27272a" strokeWidth="2.5" strokeLinecap="round" />
        {/* Shirt Logo Text */}
        <text
          x="100"
          y="176"
          textAnchor="middle"
          fill="#f8fafc"
          fontFamily="system-ui, -apple-system, sans-serif"
          fontWeight="900"
          fontSize="14"
          letterSpacing="1.5"
          className="select-none"
        >
          {shirtText}
        </text>

        {/* --- BACK PAWS --- */}
        <ellipse cx="60" cy="198" rx="14" ry="9" fill="url(#catFur)" stroke="#0f172a" strokeWidth="3" />
        <ellipse cx="140" cy="198" rx="14" ry="9" fill="url(#catFur)" stroke="#0f172a" strokeWidth="3" />

        {/* --- FRONT PAWS (Resting forward / Hanging over edge) --- */}
        <g
          className="transition-transform duration-300"
          style={{ transform: isSpeaking ? 'translateY(-2px)' : 'none' }}
        >
          {/* Left Paw */}
          <path
            d="M 72 178 C 72 195, 84 195, 84 178 Z"
            fill="url(#catFur)"
            stroke="#0f172a"
            strokeWidth="3"
          />
          {/* Paw Claws */}
          <path d="M 75 192 L 75 195 M 78 192 L 78 196 M 81 192 L 81 195" stroke="#cbd5e1" strokeWidth="1.5" strokeLinecap="round" />

          {/* Right Paw */}
          <path
            d="M 116 178 C 116 195, 128 195, 128 178 Z"
            fill="url(#catFur)"
            stroke="#0f172a"
            strokeWidth="3"
          />
          <path d="M 119 192 L 119 195 M 122 192 L 122 196 M 125 192 L 125 195" stroke="#cbd5e1" strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* --- HEAD GROUP --- */}
        <g className="origin-[100px_90px]">
          {/* EARS */}
          {/* Left Ear */}
          <polygon
            points="58,68 38,18 84,48"
            fill="url(#catFur)"
            stroke="#0f172a"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          {/* Left Inner Pink */}
          <polygon points="60,62 46,26 80,48" fill="url(#earPink)" />

          {/* Right Ear */}
          <polygon
            points="142,68 162,18 116,48"
            fill="url(#catFur)"
            stroke="#0f172a"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          {/* Right Inner Pink */}
          <polygon points="140,62 154,26 120,48" fill="url(#earPink)" />

          {/* Cat Head Base */}
          <ellipse cx="100" cy="85" rx="55" ry="46" fill="url(#catFur)" stroke="#0f172a" strokeWidth="3.5" />

          {/* Cheek Tufts (Cute fur tufts on sides) */}
          <path d="M 46 88 L 36 94 L 48 98 L 38 104 L 54 105" fill="url(#catFur)" stroke="#0f172a" strokeWidth="2.5" />
          <path d="M 154 88 L 164 94 L 152 98 L 162 104 L 146 105" fill="url(#catFur)" stroke="#0f172a" strokeWidth="2.5" />

          {/* Whiskers */}
          <g stroke="#64748b" strokeWidth="2" strokeLinecap="round">
            <line x1="42" y1="102" x2="16" y2="98" />
            <line x1="40" y1="107" x2="14" y2="108" />
            <line x1="158" y1="102" x2="184" y2="98" />
            <line x1="160" y1="107" x2="186" y2="108" />
          </g>

          {/* Nose */}
          <polygon points="96,104 104,104 100,109" fill="#f472b6" stroke="#db2777" strokeWidth="1" />

          {/* Mouth (Animated when speaking) */}
          {isSpeaking ? (
            <path
              d="M 94 111 Q 100 124 106 111 Z"
              fill="#e11d48"
              stroke="#0f172a"
              strokeWidth="2"
              className="animate-pulse"
            />
          ) : (
            <path
              d="M 92 110 Q 96 115 100 110 Q 104 115 108 110"
              fill="none"
              stroke="#0f172a"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          )}

          {/* --- SUNGLASSES (Dex signature look) --- */}
          <g className="cursor-pointer" filter="url(#shadow)">
            {/* Sunglasses Frame Bar */}
            <path
              d="M 52 74 Q 100 68 148 74"
              stroke="#0f172a"
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
            {/* Left Glass Lens */}
            <ellipse
              cx="74"
              cy="84"
              rx="22"
              ry="17"
              fill="url(#sunglassGlint)"
              stroke="#0f172a"
              strokeWidth="3.5"
            />
            {/* Left Glint Reflection */}
            <path
              d="M 64 74 L 78 74 L 68 94 L 56 94 Z"
              fill="#ffffff"
              opacity="0.35"
            />

            {/* Right Glass Lens */}
            <ellipse
              cx="126"
              cy="84"
              rx="22"
              ry="17"
              fill="url(#sunglassGlint)"
              stroke="#0f172a"
              strokeWidth="3.5"
            />
            {/* Right Glint Reflection */}
            <path
              d="M 116 74 L 130 74 L 120 94 L 108 94 Z"
              fill="#ffffff"
              opacity="0.35"
            />

            {/* Center Bridge */}
            <line x1="94" y1="81" x2="106" y2="81" stroke="#0f172a" strokeWidth="4" strokeLinecap="round" />
          </g>

          {/* Thinking Holographic Ring / Light */}
          {isThinking && (
            <circle
              cx="100"
              cy="40"
              r="14"
              fill="none"
              stroke="#a855f7"
              strokeWidth="3"
              strokeDasharray="6 4"
              className="animate-spin"
            />
          )}

          {/* Watching Cyan Radar Icon */}
          {isWatching && (
            <circle
              cx="100"
              cy="40"
              r="6"
              fill="#06b6d4"
              className="animate-ping"
            />
          )}
        </g>
      </svg>

      <style jsx>{`
        @keyframes swishSlow {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(18deg); }
        }
        @keyframes swishFast {
          0%, 100% { transform: rotate(-5deg); }
          50% { transform: rotate(24deg); }
        }
        @keyframes bounceSubtle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
        @keyframes wiggleSoft {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-2deg); }
          75% { transform: rotate(2deg); }
        }
        .animate-bounce-subtle {
          animation: bounceSubtle 1.8s ease-in-out infinite;
        }
        .animate-wiggle-soft {
          animation: wiggleSoft 0.4s ease-in-out infinite;
        }
        .animate-spin-slow {
          animation: spin 6s linear infinite;
        }
      `}</style>
    </div>
  );
}
