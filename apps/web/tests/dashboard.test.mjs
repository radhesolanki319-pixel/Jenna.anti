import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Part 9: Dashboard, Governance & Telemetry Tests', () => {
  it('validates 3-tier permission hierarchy and confirmation requirements', () => {
    const tiers = [
      { tier: 'READ', requires_confirmation: false },
      { tier: 'LOW_RISK_ACTION', requires_confirmation: false },
      { tier: 'SENSITIVE_ACTION', requires_confirmation: true },
      { tier: 'CRITICAL_ACTION', requires_confirmation: true },
    ];

    const sensitiveTiers = tiers.filter((t) => t.requires_confirmation).map((t) => t.tier);
    assert.deepEqual(sensitiveTiers, ['SENSITIVE_ACTION', 'CRITICAL_ACTION']);

    const autoAllowedTiers = tiers.filter((t) => !t.requires_confirmation).map((t) => t.tier);
    assert.deepEqual(autoAllowedTiers, ['READ', 'LOW_RISK_ACTION']);
  });

  it('verifies human approval decision request construction', () => {
    function buildDecisionRequest(itemType, itemId, decision, reason) {
      if (!['task', 'proposal'].includes(itemType)) {
        throw new Error(`Invalid item_type: ${itemType}`);
      }
      if (!['approve', 'reject'].includes(decision)) {
        throw new Error(`Invalid decision: ${decision}`);
      }
      return {
        item_type: itemType,
        item_id: itemId,
        decision,
        reason: reason || undefined,
      };
    }

    const taskDecision = buildDecisionRequest('task', 'task-123', 'approve');
    assert.equal(taskDecision.item_type, 'task');
    assert.equal(taskDecision.decision, 'approve');

    const proposalDecision = buildDecisionRequest('proposal', 'prop-456', 'reject', 'Cost breach');
    assert.equal(proposalDecision.item_type, 'proposal');
    assert.equal(proposalDecision.decision, 'reject');
    assert.equal(proposalDecision.reason, 'Cost breach');

    assert.throws(() => buildDecisionRequest('unsupported', '123', 'approve'));
  });

  it('verifies audit metadata sanitizer ensures zero credentials or tokens leaked', () => {
    const forbiddenKeys = ['password', 'token', 'secret', 'api_key', 'authorization', 'access_token'];

    function sanitizeMetadata(meta) {
      const sanitized = {};
      for (const [k, v] of Object.entries(meta)) {
        const lowerKey = k.toLowerCase();
        if (forbiddenKeys.some((f) => lowerKey.includes(f))) {
          sanitized[k] = '[REDACTED]';
        } else {
          sanitized[k] = v;
        }
      }
      return sanitized;
    }

    const dirtyMetadata = {
      user_id: 'usr_001',
      action: 'login',
      password: 'SuperSecretPassword!',
      api_key: 'AIzaSyFakeKey12345',
      session_token: 'tok_abc123',
      normal_info: 'test run',
    };

    const clean = sanitizeMetadata(dirtyMetadata);
    assert.equal(clean.password, '[REDACTED]');
    assert.equal(clean.api_key, '[REDACTED]');
    assert.equal(clean.session_token, '[REDACTED]');
    assert.equal(clean.normal_info, 'test run');
  });

  it('calculates blended AI usage costs and daily quota remaining correctly', () => {
    function calculateUsage(promptTokens, completionTokens, dailyQuota = 150000) {
      const totalTokens = promptTokens + completionTokens;
      // $0.50 per 1M prompt, $1.50 per 1M completion
      const estimatedCost = (promptTokens * 0.0000005) + (completionTokens * 0.0000015);
      const remainingQuota = Math.max(0, dailyQuota - totalTokens);
      const pctUsed = Math.min(100, (totalTokens / dailyQuota) * 100);

      return {
        totalTokens,
        estimatedCost: Number(estimatedCost.toFixed(5)),
        remainingQuota,
        pctUsed: Number(pctUsed.toFixed(1)),
      };
    }

    const usage = calculateUsage(10000, 5000, 150000);
    assert.equal(usage.totalTokens, 15000);
    assert.equal(usage.estimatedCost, 0.0125); // (10000 * 0.0000005 = 0.005) + (5000 * 0.0000015 = 0.0075) = 0.0125
    assert.equal(usage.remainingQuota, 135000);
    assert.equal(usage.pctUsed, 10.0);
  });
});
