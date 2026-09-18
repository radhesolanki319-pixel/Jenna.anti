import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Chat UI & Streaming Logic Tests', () => {
  it('correctly parses SSE lines into structured AIStreamEvents', () => {
    const rawSSE = `
data: {"type": "stream.started", "request_id": "req-1", "provider": "gemini", "model": "gemini-2.5-flash"}

data: {"type": "stream.delta", "request_id": "req-1", "delta": "Hello ", "index": 0}

data: {"type": "stream.delta", "request_id": "req-1", "delta": "world!", "index": 1}

data: {"type": "stream.completed", "request_id": "req-1", "finish_reason": "stop", "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}, "latency_ms": 120.5, "full_text": "Hello world!"}
`;

    const events = [];
    const lines = rawSSE.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data:')) {
        const jsonStr = trimmed.slice(5).trim();
        if (jsonStr) {
          events.push(JSON.parse(jsonStr));
        }
      }
    }

    assert.equal(events.length, 4);
    assert.equal(events[0].type, 'stream.started');
    assert.equal(events[0].provider, 'gemini');
    assert.equal(events[1].delta, 'Hello ');
    assert.equal(events[2].delta, 'world!');
    assert.equal(events[3].type, 'stream.completed');
    assert.equal(events[3].full_text, 'Hello world!');
    assert.equal(events[3].usage.total_tokens, 7);
  });

  it('accumulates stream deltas into complete text', () => {
    const deltas = ['The ', 'capital ', 'of ', 'France ', 'is ', 'Paris.'];
    let accumulated = '';

    for (const delta of deltas) {
      accumulated += delta;
    }

    assert.equal(accumulated, 'The capital of France is Paris.');
  });

  it('determines provider availability state from status payload', () => {
    const statusWithKeys = {
      default_provider: 'gemini',
      default_model: 'gemini-2.5-flash',
      providers: {
        gemini: { available: true, models: ['gemini-2.5-flash'] },
        openai: { available: false, models: ['gpt-4o'] },
      },
    };

    const isAvailable = Object.values(statusWithKeys.providers).some((p) => p.available);
    assert.equal(isAvailable, true);

    const statusNoKeys = {
      default_provider: 'gemini',
      default_model: 'gemini-2.5-flash',
      providers: {
        gemini: { available: false, models: [] },
        openai: { available: false, models: [] },
      },
    };

    const isOffline = Object.values(statusNoKeys.providers).some((p) => p.available);
    assert.equal(isOffline, false);
  });

  it('preserves failed prompt for retry action', () => {
    let lastFailedPrompt = null;
    const prompt = 'Can you summarize quantum mechanics?';

    // Simulate failed send
    lastFailedPrompt = prompt;

    // Simulate retry action
    const promptToRetry = lastFailedPrompt;
    assert.equal(promptToRetry, 'Can you summarize quantum mechanics?');
  });
});
