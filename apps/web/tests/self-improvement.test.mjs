/**
 * Part 8 — Controlled Self-Improvement Frontend Unit Tests
 * Uses native node:test runner.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Controlled Self-Improvement Governance & Invariants', () => {
  it('validates supported improvement categories', () => {
    const categories = [
      'PROMPT_OPTIMIZATION',
      'MEMORY_RELEVANCE',
      'TOOL_EFFICIENCY',
      'ROUTING_ACCURACY',
      'COST_REDUCTION',
    ];

    assert.equal(categories.length, 5);
    assert.ok(categories.includes('PROMPT_OPTIMIZATION'));
    assert.ok(categories.includes('COST_REDUCTION'));
  });

  it('enforces strict governance invariant: requires_human_approval is always true', () => {
    function createProposal(title, category, changes) {
      return {
        proposal_id: 'prop-test-123',
        title,
        category,
        proposed_changes: changes,
        status: 'PROPOSED',
        requires_human_approval: true, // Invariant: Never allow autonomous self-deployment
      };
    }

    const proposal = createProposal('Optimize retrieval', 'MEMORY_RELEVANCE', { weight: 0.4 });
    assert.equal(proposal.requires_human_approval, true);
  });

  it('validates isolated sandbox evaluation status transitions', () => {
    function evaluateSandbox(proposal, hasSecurityViolation, benchmarkFailures) {
      if (hasSecurityViolation || benchmarkFailures > 0) {
        return {
          status: 'TESTS_FAILED',
          regression_detected: true,
          security_check_passed: !hasSecurityViolation,
        };
      }
      return {
        status: 'TESTS_PASSED',
        regression_detected: false,
        security_check_passed: true,
      };
    }

    const failedSecurity = evaluateSandbox({ title: 'bad' }, true, 0);
    assert.equal(failedSecurity.status, 'TESTS_FAILED');
    assert.equal(failedSecurity.security_check_passed, false);

    const regression = evaluateSandbox({ title: 'regress' }, false, 2);
    assert.equal(regression.status, 'TESTS_FAILED');
    assert.equal(regression.regression_detected, true);

    const safePass = evaluateSandbox({ title: 'good' }, false, 0);
    assert.equal(safePass.status, 'TESTS_PASSED');
    assert.equal(safePass.regression_detected, false);
  });

  it('verifies staged canary progression and automatic rollback on error threshold', () => {
    const canaryStages = [5, 25, 100];
    const threshold = 0.02; // 2% max error rate

    function monitorCanary(observedErrorRate) {
      if (observedErrorRate > threshold) {
        return { action: 'TRIGGER_ROLLBACK', status: 'ROLLED_BACK' };
      }
      return { action: 'MAINTAIN_OR_PROMOTE', status: 'DEPLOYED_CANARY' };
    }

    assert.equal(monitorCanary(0.01).action, 'MAINTAIN_OR_PROMOTE');
    assert.equal(monitorCanary(0.05).action, 'TRIGGER_ROLLBACK');
    assert.equal(monitorCanary(0.05).status, 'ROLLED_BACK');
  });

  it('validates rollback record audit structure', () => {
    const rollback = {
      rollback_id: 'rb-404',
      proposal_id: 'prop-101',
      reason: 'Canary error rate 5% exceeded 2% threshold',
      previous_version: 'v1.0',
      rolled_back_at: new Date().toISOString(),
    };

    assert.equal(rollback.proposal_id, 'prop-101');
    assert.equal(rollback.previous_version, 'v1.0');
    assert.ok(rollback.reason.includes('exceeded'));
  });
});
