'use client';

import React from 'react';

export type CyberpunkState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface CyberpunkAnimeVectorProps {
  state?: CyberpunkState;
  size?: number;
  className?: string;
  showHoloRings?: boolean;
  showParticles?: boolean;
}

export function CyberpunkAnimeVector({
  state = 'idle',
  size = 180,
  className = '',
  showHoloRings = true,
  showParticles = true,
}: CyberpunkAnimeVectorProps) {
  const isListening = state === 'listening';
  const isThinking = state === 'thinking';
  const isSpeaking = state === 'speaking';

  return (
    <div
      className={`relative select-none flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 220 220"
        className="w-full h-full overflow-visible drop-shadow-[0_0_25px_rgba(168,85,247,0.45)]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Cyberpunk Skin Gradient */}
          <linearGradient id="skinGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fff5f0" />
            <stop offset="100%" stopColor="#fed7aa" />
          </linearGradient>

          {/* Hair Base Gradient (Deep Midnight Violet to Electric Purple) */}
          <linearGradient id="hairBaseGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1e1035" />
            <stop offset="50%" stopColor="#4c1d95" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>

          {/* Hair Neon Cyber Streaks (Cyan & Magenta) */}
          <linearGradient id="cyberStreakCyan" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.2" />
          </linearGradient>
          <linearGradient id="cyberStreakPink" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f43f5e" />
            <stop offset="100%" stopColor="#fb7185" stopOpacity="0.2" />
          </linearGradient>

          {/* Eye Iris Gradient */}
          <radialGradient id="eyeIrisGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#c084fc" />
            <stop offset="60%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#2e1065" />
          </radialGradient>

          {/* Mecha Headset Gradient */}
          <linearGradient id="mechaMetal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="50%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#090d16" />
          </linearGradient>

          {/* Core Arc Brooch Gradient */}
          <linearGradient id="coreArcGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="50%" stopColor="#a855f7" />
            <stop offset="100%" stopColor="#ec4899" />
          </linearGradient>

          {/* Holographic Radar Gradient */}
          <radialGradient id="holoGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.35" />
            <stop offset="70%" stopColor="#06b6d4" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
          </radialGradient>

          {/* Scanline clip */}
          <clipPath id="avatarClip">
            <circle cx="110" cy="110" r="95" />
          </clipPath>
        </defs>

        {/* ─── 1. BACKGROUND GLOW & HOLOGRAPHIC RINGS ─── */}
        <circle cx="110" cy="110" r="85" fill="url(#holoGlow)" />

        {showHoloRings && (
          <>
            {/* Outer Holographic HUD Ring (Clockwise) */}
            <g className="animate-cosmic-ring" style={{ transformOrigin: '110px 110px' }}>
              <circle
                cx="110"
                cy="110"
                r="102"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1"
                strokeDasharray="4 8 16 8"
                opacity="0.6"
              />
              {/* Technical HUD ticks */}
              <line x1="110" y1="5" x2="110" y2="12" stroke="#22d3ee" strokeWidth="2" />
              <line x1="110" y1="208" x2="110" y2="215" stroke="#22d3ee" strokeWidth="2" />
              <line x1="5" y1="110" x2="12" y2="110" stroke="#22d3ee" strokeWidth="2" />
              <line x1="208" y1="110" x2="215" y2="110" stroke="#22d3ee" strokeWidth="2" />
              <circle cx="110" cy="8" r="2" fill="#06b6d4" />
              <circle cx="182" cy="182" r="2" fill="#ec4899" />
              <circle cx="38" cy="182" r="2" fill="#a855f7" />
            </g>

            {/* Inner Counter-Rotating Hex Ring */}
            <g className="animate-cosmic-ring-rev" style={{ transformOrigin: '110px 110px' }}>
              <circle
                cx="110"
                cy="110"
                r="95"
                fill="none"
                stroke="#ec4899"
                strokeWidth="1.2"
                strokeDasharray="28 14 6 14"
                opacity="0.5"
              />
              <circle cx="110" cy="15" r="1.5" fill="#f43f5e" />
              <circle cx="15" cy="110" r="1.5" fill="#06b6d4" />
            </g>
          </>
        )}

        {/* ─── 2. SOUND WAVE RIPPLES (When Speaking or Listening) ─── */}
        {(isSpeaking || isListening) && (
          <g style={{ transformOrigin: '110px 110px' }}>
            <circle
              cx="110"
              cy="110"
              r="90"
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2"
              className="animate-ping opacity-35"
            />
            {isSpeaking && (
              <circle
                cx="110"
                cy="110"
                r="98"
                fill="none"
                stroke="#ec4899"
                strokeWidth="1.5"
                className="animate-ping opacity-25"
                style={{ animationDelay: '0.4s' }}
              />
            )}
          </g>
        )}

        {/* ─── 3. TWIN CYBER HAIR TAILS (Animated sway) ─── */}
        {/* Left Twin Tail */}
        <g
          className="animate-cyber-hair"
          style={{ transformOrigin: '55px 75px' }}
        >
          <path
            d="M 55 75 C 30 95, 18 135, 28 175 C 33 195, 45 185, 42 165 C 38 140, 52 110, 65 95 Z"
            fill="url(#hairBaseGrad)"
          />
          {/* Neon Cyan Highlight Streak */}
          <path
            d="M 50 85 C 32 105, 25 140, 32 170 C 33 162, 38 130, 52 100 Z"
            fill="url(#cyberStreakCyan)"
          />
          {/* Neon Pink Tip */}
          <path
            d="M 28 165 C 29 175, 33 182, 35 180 C 37 175, 36 165, 34 158 Z"
            fill="url(#cyberStreakPink)"
          />
        </g>

        {/* Right Twin Tail */}
        <g
          className="animate-cyber-hair-rev"
          style={{ transformOrigin: '165px 75px' }}
        >
          <path
            d="M 165 75 C 190 95, 202 135, 192 175 C 187 195, 175 185, 178 165 C 182 140, 168 110, 155 95 Z"
            fill="url(#hairBaseGrad)"
          />
          {/* Neon Cyan Highlight Streak */}
          <path
            d="M 170 85 C 188 105, 195 140, 188 170 C 187 162, 182 130, 168 100 Z"
            fill="url(#cyberStreakCyan)"
          />
          {/* Neon Pink Tip */}
          <path
            d="M 192 165 C 191 175, 187 182, 185 180 C 183 175, 184 165, 186 158 Z"
            fill="url(#cyberStreakPink)"
          />
        </g>

        {/* ─── 4. BACK HAIR VOLUME ─── */}
        <path
          d="M 60 70 C 60 25, 160 25, 160 70 C 175 105, 165 145, 155 160 C 135 170, 85 170, 65 160 C 55 145, 45 105, 60 70 Z"
          fill="#1e1035"
        />

        {/* ─── 5. MECHA COLLAR & TACTICAL SCHOOL UNIFORM ─── */}
        {/* Shoulders & Jacket */}
        <path
          d="M 55 175 Q 110 162 165 175 L 178 215 L 42 215 Z"
          fill="#0c111e"
          stroke="#1e293b"
          strokeWidth="1.5"
        />
        {/* Glowing Neon Cyan Seams on Collar */}
        <path
          d="M 68 178 L 110 206 L 152 178"
          fill="none"
          stroke="#06b6d4"
          strokeWidth="2.5"
          strokeLinecap="round"
          filter="drop-shadow(0 0 4px #06b6d4)"
        />
        {/* Neon Pink Lapel Accents */}
        <path
          d="M 78 185 L 110 214 L 142 185"
          fill="none"
          stroke="#ec4899"
          strokeWidth="1.5"
          strokeDasharray="6 3"
        />

        {/* Central Core Arc Reactor Brooch */}
        <g style={{ transformOrigin: '110px 202px' }}>
          <circle
            cx="110"
            cy="202"
            r="8"
            fill="#090d16"
            stroke="url(#coreArcGrad)"
            strokeWidth="2"
            className="animate-pulse"
          />
          <circle cx="110" cy="202" r="4.5" fill="url(#coreArcGrad)" />
          <circle
            cx="110"
            cy="202"
            r="2"
            fill="#ffffff"
            className={isThinking ? 'animate-ping' : ''}
          />
        </g>

        {/* ─── 6. NECK ─── */}
        <path
          d="M 98 138 L 98 168 Q 110 172 122 168 L 122 138 Z"
          fill="#fed7aa"
        />
        {/* Neck shadow */}
        <path
          d="M 98 138 Q 110 148 122 138 L 122 146 Q 110 154 98 146 Z"
          fill="#fcd5ce"
          opacity="0.8"
        />

        {/* ─── 7. ANIME FACE ─── */}
        <path
          d="M 68 85 C 68 120, 85 146, 110 152 C 135 146, 152 120, 152 85 C 152 50, 68 50, 68 85 Z"
          fill="url(#skinGrad)"
        />

        {/* Cyberpunk Barcode & Circuitry on Left Cheek */}
        <g opacity="0.85">
          <line x1="77" y1="112" x2="87" y2="112" stroke="#06b6d4" strokeWidth="1" />
          <line x1="77" y1="115" x2="89" y2="115" stroke="#06b6d4" strokeWidth="0.8" />
          <line x1="79" y1="118" x2="86" y2="118" stroke="#06b6d4" strokeWidth="1.2" />
          <circle cx="91" cy="115" r="1" fill="#ec4899" />
        </g>

        {/* Cute Blushing Cheeks */}
        <ellipse cx="83" cy="120" rx="9" ry="4.5" fill="#fb7185" opacity="0.45" />
        <ellipse cx="137" cy="120" rx="9" ry="4.5" fill="#fb7185" opacity="0.45" />

        {/* ─── 8. ANIME EYES & HOLOGRAPHIC OPTIC HUD ─── */}
        {/* Left Eye (Purple-Violet Anime Eye with Blinking Animation) */}
        <g className="animate-anime-blink" style={{ transformOrigin: '88px 105px' }}>
          {/* Eyeball White */}
          <ellipse cx="88" cy="105" rx="10" ry="12" fill="#ffffff" />
          {/* Violet Iris */}
          <ellipse cx="88" cy="105" rx="8" ry="10" fill="url(#eyeIrisGrad)" />
          {/* Deep Pupil */}
          <ellipse cx="88" cy="105" rx="4" ry="5.5" fill="#1e1b4b" />
          {/* Eye Star Reflections */}
          <circle cx="85" cy="101" r="2.8" fill="#ffffff" />
          <circle cx="91" cy="109" r="1.4" fill="#ffffff" opacity="0.85" />
          {/* Eyelash Top Curve */}
          <path
            d="M 76 98 Q 88 92 100 98"
            fill="none"
            stroke="#1e1035"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
          {/* Eyelash Wing */}
          <path d="M 98 97 L 102 94" stroke="#1e1035" strokeWidth="2" strokeLinecap="round" />
          {/* Eyebrow */}
          <path
            d="M 77 90 Q 88 86 98 90"
            fill="none"
            stroke="#7c3aed"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
        </g>

        {/* Right Eye (Cyber Optic HUD Eye) */}
        <g style={{ transformOrigin: '132px 105px' }}>
          {/* Base Eye with blinking */}
          <g className="animate-anime-blink" style={{ transformOrigin: '132px 105px' }}>
            <ellipse cx="132" cy="105" rx="10" ry="12" fill="#ffffff" />
            <ellipse cx="132" cy="105" rx="8" ry="10" fill="url(#eyeIrisGrad)" />
            <ellipse cx="132" cy="105" rx="4" ry="5.5" fill="#1e1b4b" />
            <circle cx="129" cy="101" r="2.8" fill="#ffffff" />
            <circle cx="135" cy="109" r="1.4" fill="#ffffff" opacity="0.85" />
            {/* Top Eyelash */}
            <path
              d="M 120 98 Q 132 92 144 98"
              fill="none"
              stroke="#1e1035"
              strokeWidth="3.2"
              strokeLinecap="round"
            />
            <path d="M 142 97 L 146 94" stroke="#1e1035" strokeWidth="2" strokeLinecap="round" />
            {/* Eyebrow */}
            <path
              d="M 122 90 Q 132 86 143 90"
              fill="none"
              stroke="#7c3aed"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
          </g>

          {/* Holographic Cyber Optic Reticle Overlay */}
          <g
            className={isThinking ? 'animate-cyber-hud' : 'animate-cyber-radar'}
            style={{ transformOrigin: '132px 105px' }}
          >
            <circle
              cx="132"
              cy="105"
              r="13.5"
              fill="none"
              stroke="#06b6d4"
              strokeWidth="1.2"
              strokeDasharray="4 3 8 3"
              opacity="0.85"
            />
            {/* Crosshair ticks */}
            <line x1="132" y1="90" x2="132" y2="93" stroke="#22d3ee" strokeWidth="1.5" />
            <line x1="132" y1="117" x2="132" y2="120" stroke="#22d3ee" strokeWidth="1.5" />
            <line x1="117" y1="105" x2="120" y2="105" stroke="#22d3ee" strokeWidth="1.5" />
            <line x1="144" y1="105" x2="147" y2="105" stroke="#22d3ee" strokeWidth="1.5" />
            <circle cx="132" cy="105" r="1.8" fill="#ec4899" />
          </g>
        </g>

        {/* Minimalist Anime Nose */}
        <circle cx="110" cy="122" r="1.2" fill="#e29578" />

        {/* ─── 9. ANIME MOUTH (Reactive to Speaking / Idle / Listening) ─── */}
        {isSpeaking ? (
          /* Animated Lip-Sync Mouth when Speaking */
          <g className="animate-anime-mouth" style={{ transformOrigin: '110px 136px' }}>
            <path
              d="M 103 133 Q 110 144 117 133 Q 110 140 103 133 Z"
              fill="#f43f5e"
              stroke="#be123c"
              strokeWidth="1.2"
            />
            {/* Teeth highlight */}
            <path d="M 105 134 Q 110 136 115 134" stroke="#ffffff" strokeWidth="1.2" />
          </g>
        ) : isListening ? (
          /* Sweet attentive calm smile */
          <path
            d="M 104 135 Q 110 140 116 135"
            fill="none"
            stroke="#e11d48"
            strokeWidth="2"
            strokeLinecap="round"
          />
        ) : isThinking ? (
          /* Thoughtful slightly rounded mouth */
          <ellipse
            cx="110"
            cy="135"
            rx="3.5"
            ry="2.5"
            fill="#f43f5e"
            stroke="#be123c"
            strokeWidth="1"
          />
        ) : (
          /* Default Cute Anime Smile */
          <path
            d="M 104 135 Q 110 141 116 135"
            fill="none"
            stroke="#e11d48"
            strokeWidth="2"
            strokeLinecap="round"
          />
        )}

        {/* ─── 10. FRONT HAIR BANGS & CYBER STREAKS ─── */}
        <g>
          {/* Main Bangs Shape */}
          <path
            d="M 65 72 C 72 50, 148 50, 155 72 C 158 92, 145 106, 138 98 C 130 90, 128 104, 118 96 C 110 90, 106 102, 98 94 C 88 86, 85 104, 76 96 C 70 90, 63 94, 65 72 Z"
            fill="url(#hairBaseGrad)"
          />
          {/* Cyber Streaks Highlights on Bangs */}
          <path
            d="M 85 58 Q 92 78 86 94"
            fill="none"
            stroke="#06b6d4"
            strokeWidth="2.5"
            strokeLinecap="round"
            filter="drop-shadow(0 0 3px #06b6d4)"
          />
          <path
            d="M 125 58 Q 118 78 126 94"
            fill="none"
            stroke="#ec4899"
            strokeWidth="2.2"
            strokeLinecap="round"
            filter="drop-shadow(0 0 3px #ec4899)"
          />
          <path
            d="M 105 54 Q 106 72 104 88"
            fill="none"
            stroke="#a855f7"
            strokeWidth="1.8"
            strokeLinecap="round"
          />

          {/* Cybernetic Geometric Hairpins */}
          <polygon
            points="70,68 76,64 74,78 68,76"
            fill="#06b6d4"
            stroke="#ffffff"
            strokeWidth="0.8"
            filter="drop-shadow(0 0 3px #06b6d4)"
          />
          <polygon
            points="150,68 144,64 146,78 152,76"
            fill="#ec4899"
            stroke="#ffffff"
            strokeWidth="0.8"
            filter="drop-shadow(0 0 3px #ec4899)"
          />
        </g>

        {/* ─── 11. MECHA HEADSET WITH INTEGRATED EQUALIZER ─── */}
        {/* Left Headset Ear Cup */}
        <g>
          <rect
            x="54"
            y="94"
            width="12"
            height="26"
            rx="6"
            fill="url(#mechaMetal)"
            stroke="#06b6d4"
            strokeWidth="1.5"
            filter="drop-shadow(0 0 4px #06b6d4)"
          />
          {/* Left Audio Equalizer Bars */}
          <g transform="translate(57, 100)">
            <rect x="0" y="0" width="1.5" height="14" fill="#06b6d4" className={isSpeaking ? 'animate-cyber-eq-1' : ''} />
            <rect x="2.5" y="2" width="1.5" height="10" fill="#22d3ee" className={isSpeaking ? 'animate-cyber-eq-2' : ''} />
            <rect x="5" y="4" width="1.5" height="8" fill="#a855f7" className={isSpeaking ? 'animate-cyber-eq-3' : ''} />
          </g>
        </g>

        {/* Right Headset Ear Cup */}
        <g>
          <rect
            x="154"
            y="94"
            width="12"
            height="26"
            rx="6"
            fill="url(#mechaMetal)"
            stroke="#ec4899"
            strokeWidth="1.5"
            filter="drop-shadow(0 0 4px #ec4899)"
          />
          {/* Right Audio Equalizer Bars */}
          <g transform="translate(157, 100)">
            <rect x="0" y="4" width="1.5" height="8" fill="#a855f7" className={isSpeaking ? 'animate-cyber-eq-3' : ''} />
            <rect x="2.5" y="2" width="1.5" height="10" fill="#f43f5e" className={isSpeaking ? 'animate-cyber-eq-2' : ''} />
            <rect x="5" y="0" width="1.5" height="14" fill="#ec4899" className={isSpeaking ? 'animate-cyber-eq-4' : ''} />
          </g>
        </g>

        {/* Headset Arc Band Over Head */}
        <path
          d="M 60 96 C 60 40, 160 40, 160 96"
          fill="none"
          stroke="#334155"
          strokeWidth="3.5"
        />
        <path
          d="M 75 66 C 90 52, 130 52, 145 66"
          fill="none"
          stroke="#06b6d4"
          strokeWidth="1.8"
          strokeDasharray="8 4"
          filter="drop-shadow(0 0 3px #06b6d4)"
        />

        {/* ─── 12. FLOATING NEON STARS & CYBER PARTICLES ─── */}
        {showParticles && (
          <g>
            {/* Top-Right Sparkle Star */}
            <g className="animate-cyber-sparkle" style={{ transformOrigin: '185px 45px' }}>
              <path
                d="M 185 37 L 187 43 L 193 45 L 187 47 L 185 53 L 183 47 L 177 45 L 183 43 Z"
                fill="#22d3ee"
                filter="drop-shadow(0 0 4px #22d3ee)"
              />
            </g>

            {/* Top-Left Sparkle Star */}
            <g
              className="animate-cyber-sparkle"
              style={{ transformOrigin: '35px 50px', animationDelay: '1.2s' }}
            >
              <path
                d="M 35 44 L 36.5 48.5 L 41 50 L 36.5 51.5 L 35 56 L 33.5 51.5 L 29 50 L 33.5 48.5 Z"
                fill="#f43f5e"
                filter="drop-shadow(0 0 4px #f43f5e)"
              />
            </g>

            {/* Bottom-Right Cyber Cube */}
            <rect
              x="180"
              y="150"
              width="5"
              height="5"
              fill="none"
              stroke="#a855f7"
              strokeWidth="1"
              className="animate-pulse"
            />

            {/* Bottom-Left Hex Star */}
            <circle
              cx="40"
              cy="145"
              r="2"
              fill="#06b6d4"
              className="animate-ping opacity-60"
            />
          </g>
        )}

        {/* ─── 13. HOLOGRAPHIC SCANNER BEAM SWEEP ─── */}
        <g clipPath="url(#avatarClip)" opacity="0.6">
          <line
            x1="0"
            y1="50"
            x2="220"
            y2="50"
            stroke="#22d3ee"
            strokeWidth="1.5"
            className="animate-cyber-scanline"
            filter="drop-shadow(0 0 4px #06b6d4)"
          />
        </g>
      </svg>
    </div>
  );
}
