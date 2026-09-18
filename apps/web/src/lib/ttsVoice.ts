// ─── Jenna Natural Warm Female Voice Engine (Web Speech API) ─────────────

export interface JennaSpeechOptions {
  pitch?: number;
  rate?: number;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: any) => void;
}

/**
 * Finds the most natural, warm human female voice available on the device/browser.
 * Specifically avoids robotic, metallic, or generic default voices.
 */
export function getJennaFemaleVoice(): SpeechSynthesisVoice | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  // 1. Top Tier Natural Female Voices (Smooth, Human-like, Warm)
  const prioritizedFemaleVoices = [
    'Google UK English Female',
    'Google US English Female',
    'Microsoft Zira',
    'Samantha',
    'Victoria',
    'Karen',
    'Moira',
    'Fiona',
    'Tessa',
    'Google हिन्दी',
    'Lekha',
    'Swara',
    'Neerja',
  ];

  for (const name of prioritizedFemaleVoices) {
    const match = voices.find((v) =>
      v.name.toLowerCase().includes(name.toLowerCase())
    );
    if (match) return match;
  }

  // 2. Fallback: Search for any voice with female indicators
  const femaleVoice = voices.find((v) => {
    const n = v.name.toLowerCase();
    return (
      n.includes('female') ||
      n.includes('woman') ||
      n.includes('girl') ||
      n.includes('natural')
    );
  });
  if (femaleVoice) return femaleVoice;

  // 3. Fallback: English voice with warm pitch
  const englishVoice = voices.find(
    (v) => v.lang.startsWith('en') || v.lang.startsWith('hi')
  );
  return englishVoice || voices[0];
}

/**
 * Speak text using Jenna's natural warm female voice.
 */
export function speakJennaVoice(
  text: string,
  options: JennaSpeechOptions = {}
): SpeechSynthesisUtterance | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;

  // Clean text from markdown code blocks, URLs, and asterisks for smooth natural speech
  const cleanText = text
    .replace(/```[\s\S]*?```/g, 'Here is the code.')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/#+\s+/g, '')
    .replace(/https?:\/\/\S+/g, 'link')
    .slice(0, 800) // Keep readable length for natural speech
    .trim();

  if (!cleanText) return null;

  window.speechSynthesis.cancel(); // Stop previous speech

  const utterance = new SpeechSynthesisUtterance(cleanText);
  const voice = getJennaFemaleVoice();
  if (voice) {
    utterance.voice = voice;
  }

  // Natural warm inflection settings (tested to sound warm & friendly, NOT robotic)
  utterance.pitch = options.pitch ?? 1.08;
  utterance.rate = options.rate ?? 0.98;

  if (options.onStart) utterance.onstart = options.onStart;
  if (options.onEnd) utterance.onend = options.onEnd;
  if (options.onError) utterance.onerror = options.onError;

  window.speechSynthesis.speak(utterance);
  return utterance;
}

/**
 * Stop any current speech synthesis.
 */
export function stopJennaVoice() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
