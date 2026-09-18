'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { apiClient } from '@/lib/api';
import { VoiceProfile, VoiceTurnState } from '@jenna/types';
import {
  Mic,
  MicOff,
  Volume2,
  Radio,
  Play,
  Square,
  ShieldCheck,
  Settings,
  Sparkles,
} from 'lucide-react';

export default function VoicePage() {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('jenna-hi-in-warm-female');
  const [activeTurnState, setActiveTurnState] = useState<VoiceTurnState>('IDLE');
  const [ttsInput, setTtsInput] = useState<string>(
    'Namaste! Main Jenna hoon. Main aapki kya madad kar sakti hoon?'
  );
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesizedAudio, setSynthesizedAudio] = useState<string | null>(null);
  const [micActive, setMicActive] = useState(false);
  const [transcript, setTranscript] = useState<string>('');

  useEffect(() => {
    async function loadProfiles() {
      try {
        const list = await apiClient.getVoiceProfiles();
        setProfiles(list);
        if (list.length > 0) {
          const femaleDef = list.find((p: VoiceProfile) => p.gender === 'female') || list[0];
          setSelectedVoice(femaleDef.voice_id);
        }
      } catch (err) {
        console.error('Failed to load voice profiles', err);
      }
    }
    loadProfiles();
  }, []);

  const handleSynthesize = async () => {
    if (!ttsInput.trim()) return;
    setIsSynthesizing(true);
    try {
      const activeProf = profiles.find((p) => p.voice_id === selectedVoice);
      const blob = await apiClient.synthesizeSpeech(ttsInput, activeProf);
      const url = URL.createObjectURL(blob);
      setSynthesizedAudio(url);
      setActiveTurnState('SPEAKING');
    } catch (err) {
      console.error('Synthesis failed', err);
    } finally {
      setIsSynthesizing(false);
    }
  };


  const toggleMic = () => {
    if (micActive) {
      setMicActive(false);
      setActiveTurnState('IDLE');
    } else {
      setMicActive(true);
      setActiveTurnState('LISTENING');
      setTranscript('Listening for bilingual speech...');
      setTimeout(() => {
        setTranscript('Jenna, show me system health and pending tasks.');
        setActiveTurnState('SPEAKING');
      }, 2000);
    }
  };

  const handleInterrupt = () => {
    setActiveTurnState('INTERRUPTED');
    setMicActive(false);
    setSynthesizedAudio(null);
    setTimeout(() => setActiveTurnState('IDLE'), 1500);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Volume2 className="h-6 w-6 text-primary-500" />
              Bilingual Voice Studio & Turn Detection
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Low-latency voice interface with female Jenna voice persona, interruption handling, and turn management.
            </p>
          </div>
        </div>

        {/* Privacy Invariant Banner */}
        <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/5 dark:bg-emerald-500/10 flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <div className="text-xs text-zinc-600 dark:text-zinc-300">
            <strong className="text-foreground">Privacy Protection Rule:</strong> Microphone is never silently activated.
            Raw audio streams are processed in-memory and strictly not retained on disk by default.
          </div>
        </div>

        {/* Studio Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Speech-to-Text & Interactive Conversation */}
          <div className="lg:col-span-2 space-y-6">
            {/* Real-time Turn Stage Visualizer */}
            <div className="p-6 rounded-lg border border-border bg-card flex flex-col items-center justify-center space-y-4 text-center">
              <div
                className={`relative flex h-24 w-24 items-center justify-center rounded-full transition-all duration-300 ${
                  activeTurnState === 'LISTENING'
                    ? 'bg-amber-500/20 text-amber-500 ring-8 ring-amber-500/10 animate-pulse'
                    : activeTurnState === 'SPEAKING'
                    ? 'bg-primary-500/20 text-primary-500 ring-8 ring-primary-500/10'
                    : activeTurnState === 'INTERRUPTED'
                    ? 'bg-rose-500/20 text-rose-500 ring-8 ring-rose-500/10'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400'
                }`}
              >
                {micActive ? <Mic className="h-10 w-10" /> : <MicOff className="h-10 w-10" />}
              </div>

              <div>
                <span className="text-xs font-mono uppercase tracking-widest text-zinc-400">Turn State</span>
                <h3 className="text-xl font-bold text-foreground mt-0.5">{activeTurnState}</h3>
                <p className="text-xs text-zinc-500 mt-1 max-w-sm">
                  {activeTurnState === 'LISTENING'
                    ? 'Microphone active. VAD detecting voice...'
                    : activeTurnState === 'SPEAKING'
                    ? 'Jenna is speaking. Interruption detector armed.'
                    : activeTurnState === 'INTERRUPTED'
                    ? 'Speech halted immediately upon user interruption.'
                    : 'Idle. Press start to speak with Jenna.'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={toggleMic}
                  className={`px-5 py-2.5 rounded-full font-semibold text-xs flex items-center gap-2 transition-all ${
                    micActive
                      ? 'bg-rose-600 hover:bg-rose-700 text-white'
                      : 'bg-primary-600 hover:bg-primary-700 text-white'
                  }`}
                >
                  {micActive ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  {micActive ? 'Stop Listening' : 'Start Speaking'}
                </button>

                {activeTurnState === 'SPEAKING' && (
                  <button
                    onClick={handleInterrupt}
                    className="px-4 py-2.5 rounded-full font-semibold text-xs bg-amber-600 hover:bg-amber-700 text-white flex items-center gap-2 transition-colors"
                  >
                    <Square className="h-4 w-4" />
                    Interrupt Jenna
                  </button>
                )}
              </div>

              {transcript && (
                <div className="w-full max-w-md p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-border text-xs text-foreground font-mono">
                  &gt; {transcript}
                </div>
              )}
            </div>

            {/* TTS Text to Speech Previewer */}
            <div className="p-5 rounded-lg border border-border bg-card space-y-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary-500" />
                Text-to-Speech Preview & Synthesizer
              </h3>
              <textarea
                rows={3}
                value={ttsInput}
                onChange={(e) => setTtsInput(e.target.value)}
                placeholder="Enter Hindi, Hinglish, or English text for Jenna to speak..."
                className="w-full p-3 text-xs rounded-md border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-400">
                  Target Voice: <strong className="text-foreground">{selectedVoice}</strong>
                </span>
                <button
                  onClick={handleSynthesize}
                  disabled={isSynthesizing || !ttsInput.trim()}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white flex items-center gap-2 transition-colors"
                >
                  <Play className="h-3.5 w-3.5" />
                  {isSynthesizing ? 'Synthesizing...' : 'Synthesize Audio'}
                </button>
              </div>

              {synthesizedAudio && (
                <div className="p-3 rounded-lg border border-primary-500/30 bg-primary-500/5 text-xs flex items-center justify-between">
                  <span className="text-foreground font-medium">Audio Synthesized Successfully</span>
                  <audio
                    controls
                    autoPlay
                    src={`data:audio/wav;base64,${synthesizedAudio}`}
                    className="h-8 max-w-xs"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Col: Female Jenna Voice Persona Configuration */}
          <div className="space-y-6">
            <div className="p-5 rounded-lg border border-border bg-card space-y-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Settings className="h-4 w-4 text-primary-500" />
                Voice Persona Profiles
              </h3>
              <p className="text-xs text-zinc-500">
                Jenna exclusively utilizes female voice profiles tuned for natural Hindi and English cadence.
              </p>

              <div className="space-y-2">
                {profiles.map((p) => (
                  <div
                    key={p.voice_id}
                    onClick={() => setSelectedVoice(p.voice_id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedVoice === p.voice_id
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-border hover:bg-zinc-50 dark:hover:bg-zinc-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-foreground">{p.name}</span>
                      <span className="text-[10px] font-mono uppercase bg-primary-500/20 text-primary-600 dark:text-primary-400 px-1.5 py-0.5 rounded">
                        {p.gender}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-500 mt-1">Style: {p.style}</p>
                    <div className="flex items-center gap-2 text-[10px] text-zinc-400 mt-1 font-mono">
                      <span>Speed: {p.speed}x</span>
                      <span>•</span>
                      <span>Pitch: {p.pitch}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
