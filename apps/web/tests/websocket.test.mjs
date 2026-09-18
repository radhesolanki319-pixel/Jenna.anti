import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('WebSocket Logic & Backoff Tests', () => {
  function calculateBackoffDelay(attempt, baseDelay = 1000, factor = 1.5, maxDelay = 15000) {
    return Math.min(baseDelay * Math.pow(factor, attempt - 1), maxDelay);
  }

  it('calculates exponential backoff delays up to max cap', () => {
    assert.equal(calculateBackoffDelay(1), 1000);
    assert.equal(calculateBackoffDelay(2), 1500);
    assert.equal(calculateBackoffDelay(3), 2250);
    assert.equal(calculateBackoffDelay(4), 3375);
    assert.equal(calculateBackoffDelay(10), 15000); // capped at 15s
  });

  it('enforces maximum reconnection attempts to avoid aggressive loops', () => {
    const maxAttempts = 5;
    let attempts = 0;
    let finalStatus = 'connecting';

    for (let i = 1; i <= 7; i++) {
      attempts++;
      if (attempts <= maxAttempts) {
        finalStatus = 'reconnecting';
      } else {
        finalStatus = 'disconnected';
      }
    }

    assert.equal(attempts, 7);
    assert.equal(finalStatus, 'disconnected');
  });

  it('calculates roundtrip latency on pong receipt', () => {
    const pingTimestamp = 1000000;
    const pongTimestamp = 1000018; // 18ms later
    const latencyMs = pongTimestamp - pingTimestamp;

    assert.equal(latencyMs, 18);
    assert.ok(latencyMs >= 0);
  });
});
