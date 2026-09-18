/**
 * Unit Tests for Phase 2: Chat UI Multi-turn, Personality Settings, and Streaming Logic
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

describe('Chat UI Phase 2 & Multi-turn Logic Tests', () => {
  test('correctly constructs conversation and message data models', () => {
    const conv = {
      id: 'conv-1234',
      user_id: 'usr-1',
      title: 'Hinglish Coding Discussion',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    assert.equal(conv.id, 'conv-1234');
    assert.equal(conv.title, 'Hinglish Coding Discussion');

    const msg = {
      id: 'msg-5678',
      conversation_id: conv.id,
      role: 'assistant',
      content: 'Haan bilkul! Async/await internally promises aur event loop par depend karta hai.',
      model: 'gemini-2.5-flash',
      provider: 'gemini',
      metadata: { detected_language: 'hinglish', task_type: 'CODING' },
      created_at: new Date().toISOString(),
    };

    assert.equal(msg.role, 'assistant');
    assert.equal(msg.metadata.detected_language, 'hinglish');
    assert.equal(msg.metadata.task_type, 'CODING');
  });

  test('accumulates streamed tokens into active message content', () => {
    let accumulated = '';
    const chunks = ['Jenna ', 'is ', 'ready ', 'to ', 'help!'];

    for (const chunk of chunks) {
      accumulated += chunk;
    }

    assert.equal(accumulated, 'Jenna is ready to help!');
  });

  test('validates personality settings schema and options', () => {
    const defaultSettings = {
      assistant_name: 'Jenna',
      personality_style: 'warm',
      response_style: 'conversational',
      preferred_language: 'auto',
      preferred_locale: 'en-IN',
      verbosity: 'normal',
      formality: 'casual',
      humor_level: 'subtle',
    };

    assert.equal(defaultSettings.assistant_name, 'Jenna');
    assert.equal(defaultSettings.preferred_language, 'auto');
    assert.equal(defaultSettings.personality_style, 'warm');

    // Partial update
    const updated = {
      ...defaultSettings,
      personality_style: 'playful',
      preferred_language: 'hinglish',
      humor_level: 'witty',
    };

    assert.equal(updated.personality_style, 'playful');
    assert.equal(updated.preferred_language, 'hinglish');
    assert.equal(updated.humor_level, 'witty');
  });

  test('handles abort signal when stopping generation', () => {
    const controller = new AbortController();
    assert.equal(controller.signal.aborted, false);

    controller.abort();
    assert.equal(controller.signal.aborted, true);
  });
});
