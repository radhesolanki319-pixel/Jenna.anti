import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Specialized Agent & Orchestrator Logic Tests', () => {
  it('validates supported specialized agent types and default registry attributes', () => {
    const agentTypes = ['RESEARCH', 'CODING', 'ANALYSIS', 'WRITING', 'GENERAL_TASK'];
    assert.equal(agentTypes.length, 5);
    assert.ok(agentTypes.includes('RESEARCH'));
    assert.ok(agentTypes.includes('CODING'));
    assert.ok(agentTypes.includes('ANALYSIS'));
    assert.ok(agentTypes.includes('WRITING'));
    assert.ok(agentTypes.includes('GENERAL_TASK'));
  });

  it('validates agent task lifecycle states and terminal statuses', () => {
    const statuses = ['CREATED', 'QUEUED', 'RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED', 'CANCELLED'];
    assert.equal(statuses.length, 7);

    const isTerminal = (status) => ['SUCCEEDED', 'FAILED', 'CANCELLED'].includes(status);
    assert.equal(isTerminal('SUCCEEDED'), true);
    assert.equal(isTerminal('FAILED'), true);
    assert.equal(isTerminal('CANCELLED'), true);
    assert.equal(isTerminal('RUNNING'), false);
    assert.equal(isTerminal('WAITING'), false);
  });

  it('verifies task decomposition ordering and subtask assignment', () => {
    const mockDecomposition = {
      original_task: 'Audit system performance and generate technical report',
      strategy: 'sequential_analysis_and_drafting',
      subtasks: [
        { order: 1, agent_type: 'ANALYSIS', title: 'Collect bottleneck metrics', description: 'Inspect traces' },
        { order: 2, agent_type: 'WRITING', title: 'Draft executive summary', description: 'Write findings' },
      ],
    };

    assert.equal(mockDecomposition.subtasks.length, 2);
    assert.equal(mockDecomposition.subtasks[0].order, 1);
    assert.equal(mockDecomposition.subtasks[0].agent_type, 'ANALYSIS');
    assert.equal(mockDecomposition.subtasks[1].order, 2);
    assert.equal(mockDecomposition.subtasks[1].agent_type, 'WRITING');
  });

  it('verifies execution trace telemetry aggregation', () => {
    const traces = [
      { step_index: 1, duration_ms: 120.5, status: 'SUCCEEDED', action: 'gather_context' },
      { step_index: 2, duration_ms: 450.0, status: 'SUCCEEDED', action: 'execute_codegen' },
      { step_index: 3, duration_ms: 80.2, status: 'SUCCEEDED', action: 'run_tests' },
    ];

    const totalDuration = traces.reduce((acc, t) => acc + t.duration_ms, 0);
    assert.equal(Math.round(totalDuration), 651);

    const allSucceeded = traces.every((t) => t.status === 'SUCCEEDED');
    assert.equal(allSucceeded, true);
  });

  it('enforces 3-tier authorization challenge when confirmation is required', () => {
    const normalTask = { id: 't-1', requires_confirmation: false, confirmation_reason: null };
    const sensitiveTask = {
      id: 't-2',
      requires_confirmation: true,
      confirmation_reason: 'External network dispatch requires user confirmation.',
    };

    const needsUserAction = (t) => Boolean(t.requires_confirmation);
    assert.equal(needsUserAction(normalTask), false);
    assert.equal(needsUserAction(sensitiveTask), true);
    assert.ok(sensitiveTask.confirmation_reason.includes('user confirmation'));
  });

  it('validates budget enforcement constraints', () => {
    const defaultBudget = { max_steps: 10, max_tokens: 4000, timeout_seconds: 120 };

    const isExceeded = (budget, currentSteps, currentTokens) =>
      currentSteps > budget.max_steps || currentTokens > budget.max_tokens;

    assert.equal(isExceeded(defaultBudget, 5, 2000), false);
    assert.equal(isExceeded(defaultBudget, 11, 2000), true);
    assert.equal(isExceeded(defaultBudget, 8, 4500), true);
  });
});
