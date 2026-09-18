'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Eye,
  Camera,
  Monitor,
  Upload,
  ShieldCheck,
  AlertTriangle,
  Volume2,
  Square,
  Play,
  Loader2,
  CheckCircle2,
  Layers,
  FileText,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type { VisionAnalysisResult, CameraContext, VoiceProfile } from '@jenna/types';

export default function VisionPage() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string>('image/jpeg');
  const [userPrompt, setUserPrompt] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<VisionAnalysisResult | null>(null);
  const [cameraContext, setCameraContext] = useState<CameraContext | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Voice playback state
  const [isPlayingVoice, setIsPlayingVoice] = useState<boolean>(false);
  const [voiceProfiles, setVoiceProfiles] = useState<VoiceProfile[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('jenna-female-natural');
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    // Load initial camera status & voice profiles
    apiClient.getCameraStatus()
      .then(setCameraContext)
      .catch(() => setCameraContext({ is_active: false, resolution: '1080p', framerate: 30, permission_granted: false }));

    apiClient.getVoiceProfiles()
      .then(setVoiceProfiles)
      .catch(() => {});
  }, []);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setMimeType(file.type || 'image/jpeg');

    const reader = new FileReader();
    reader.onload = () => {
      setImagePreview(reader.result as string);
      setAnalysisResult(null);
    };
    reader.readAsDataURL(file);
  };

  const handleScreenCaptureMock = () => {
    setError(null);
    // Create a mock canvas screenshot
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 360;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, 640, 360);
      ctx.fillStyle = '#38bdf8';
      ctx.font = '22px sans-serif';
      ctx.fillText('Jenna AI — Screen Capture Sample', 40, 60);
      ctx.fillStyle = '#94a3b8';
      ctx.font = '14px sans-serif';
      ctx.fillText('Status: Active Workspace [Confidential]', 40, 100);
      ctx.fillStyle = '#22c55e';
      ctx.fillRect(40, 140, 140, 40);
      ctx.fillStyle = '#ffffff';
      ctx.font = '16px sans-serif';
      ctx.fillText('Submit Order', 60, 166);
    }
    const dataUrl = canvas.toDataURL('image/png');
    setImagePreview(dataUrl);
    setMimeType('image/png');
    setAnalysisResult(null);
  };

  const handleAnalyze = async () => {
    if (!imagePreview) {
      setError('Please upload an image or capture a screen first.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      // Extract raw base64 without data URI prefix
      const base64Data = imagePreview.includes(',')
        ? imagePreview.split(',')[1]
        : imagePreview;

      const result = await apiClient.analyzeImage(
        base64Data,
        mimeType,
        userPrompt || undefined,
        true
      );
      setAnalysisResult(result);
    } catch (err: any) {
      setError(err?.message || 'Visual analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSpeakDescription = async () => {
    if (!analysisResult?.description) return;

    if (isPlayingVoice) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setIsPlayingVoice(false);
      return;
    }

    try {
      setIsPlayingVoice(true);
      const profile = voiceProfiles.find((v) => v.voice_id === selectedVoice);
      const audioBlob = await apiClient.synthesizeSpeech(
        analysisResult.description,
        profile
      );
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        audioRef.current.onended = () => setIsPlayingVoice(false);
      }
    } catch (err: any) {
      setError(`Speech playback failed: ${err.message}`);
      setIsPlayingVoice(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Hidden audio element for TTS playback */}
      <audio ref={audioRef} className="hidden" />

      {/* Header & Security Guarantees */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
              <Eye className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                Jenna Vision & Multimodal Engine
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Part 6 Live
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Visual inspection, UI bounding box extraction, OCR text synthesis, and Jenna Voice narration.
              </p>
            </div>
          </div>
        </div>

        {/* Security / Privacy badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Never Silent Activate</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Untrusted OCR Fence</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}

      {/* Main Grid: Upload & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Canvas & Inputs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-violet-400" />
                Visual Input Viewport
              </h2>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleScreenCaptureMock}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 flex items-center gap-1.5 transition-colors"
                >
                  <Monitor className="w-3.5 h-3.5 text-sky-400" />
                  Capture Screen
                </button>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs font-medium text-white flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Upload Image
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </div>
            </div>

            {/* Canvas / Preview Container */}
            <div className="relative aspect-video rounded-xl bg-slate-950 border border-dashed border-slate-800 flex items-center justify-center overflow-hidden">
              {imagePreview ? (
                <div className="relative w-full h-full flex items-center justify-center">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-full max-w-full object-contain"
                  />
                  {/* Overlay bounding boxes if available */}
                  {analysisResult?.detected_elements?.map((elem, idx) => (
                    <div
                      key={idx}
                      className="absolute border-2 border-emerald-400 bg-emerald-500/10 pointer-events-none rounded transition-all"
                      style={{
                        left: `${elem.x * 100}%`,
                        top: `${elem.y * 100}%`,
                        width: `${elem.width * 100}%`,
                        height: `${elem.height * 100}%`,
                      }}
                    >
                      <span className="absolute -top-5 left-0 bg-emerald-600 text-white text-[10px] px-1 py-0.5 rounded font-mono shadow">
                        {elem.label || 'elem'} ({Math.round(elem.confidence * 100)}%)
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center p-6 space-y-2 text-slate-500">
                  <Camera className="w-10 h-10 mx-auto text-slate-600" />
                  <p className="text-sm font-medium">No image loaded</p>
                  <p className="text-xs text-slate-600">
                    Upload a JPEG, PNG, or WEBP file or simulate screen capture.
                  </p>
                </div>
              )}
            </div>

            {/* Prompt input */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">
                Instruction / Question (Optional)
              </label>
              <input
                type="text"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="e.g., Identify interactive buttons, transcribe text, summarize chart..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              />
            </div>

            {/* Analyze trigger button */}
            <button
              type="button"
              disabled={isAnalyzing || !imagePreview}
              onClick={handleAnalyze}
              className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm text-white flex items-center justify-center gap-2 shadow-lg shadow-violet-900/20 transition-all"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Scene & OCR...
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4" />
                  Analyze with Jenna Vision
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Structured Results & Voice Narration (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                Analysis Output
              </h2>
              {analysisResult && (
                <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Conf: {Math.round(analysisResult.confidence * 100)}%
                </span>
              )}
            </div>

            {analysisResult ? (
              <div className="space-y-4">
                {/* Description */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Scene Understanding
                  </h3>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                    {analysisResult.description}
                  </div>
                </div>

                {/* Jenna Voice Narration */}
                <div className="p-3.5 rounded-xl bg-violet-950/20 border border-violet-800/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-violet-300 flex items-center gap-1.5">
                      <Volume2 className="w-4 h-4" />
                      Jenna Voice Playback
                    </span>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2 py-1"
                    >
                      {voiceProfiles.map((vp) => (
                        <option key={vp.voice_id} value={vp.voice_id}>
                          {vp.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={handleSpeakDescription}
                    className="w-full py-2 rounded-lg bg-violet-600/80 hover:bg-violet-600 text-xs font-medium text-white flex items-center justify-center gap-2 transition-all"
                  >
                    {isPlayingVoice ? (
                      <>
                        <Square className="w-3.5 h-3.5 fill-current" />
                        Stop Jenna Speaking
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        Speak Analysis with Jenna
                      </>
                    )}
                  </button>
                </div>

                {/* Extracted Text (OCR) with Untrusted Fence */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Extracted Text (OCR)
                    </h3>
                    <span className="text-[10px] text-amber-400/90 font-mono">
                      [Untrusted Context]
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 space-y-1 max-h-36 overflow-y-auto">
                    {analysisResult.extracted_text.length > 0 ? (
                      analysisResult.extracted_text.map((line, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <span className="text-slate-600 select-none">{idx + 1}</span>
                          <span>{line}</span>
                        </div>
                      ))
                    ) : (
                      <span className="text-slate-500 italic">No text found.</span>
                    )}
                  </div>
                </div>

                {/* Detected UI Elements */}
                {analysisResult.detected_elements.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Detected Elements ({analysisResult.detected_elements.length})
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                      {analysisResult.detected_elements.map((elem, idx) => (
                        <div
                          key={idx}
                          className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-0.5"
                        >
                          <div className="text-emerald-400 font-medium">
                            {elem.label || 'element'}
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono">
                            {Math.round(elem.confidence * 100)}% conf
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 space-y-2 text-slate-500">
                <CheckCircle2 className="w-8 h-8 mx-auto text-slate-700" />
                <p className="text-xs">No analysis yet. Upload media and click Analyze.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
