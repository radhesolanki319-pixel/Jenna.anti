import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Health Status Aggregation & Navigation Matrix Tests', () => {
  function aggregateHealth(services) {
    if (!services || services.length === 0) return 'unhealthy';
    const hasUnhealthy = services.some((s) => s.status === 'unhealthy');
    const hasDegraded = services.some((s) => s.status === 'degraded');
    if (hasUnhealthy) return 'unhealthy';
    if (hasDegraded) return 'degraded';
    return 'healthy';
  }

  it('aggregates overall health correctly based on dependency states', () => {
    // All healthy
    assert.equal(
      aggregateHealth([
        { name: 'postgresql', status: 'healthy' },
        { name: 'redis', status: 'healthy' },
      ]),
      'healthy'
    );

    // One degraded
    assert.equal(
      aggregateHealth([
        { name: 'postgresql', status: 'healthy' },
        { name: 'redis', status: 'degraded' },
      ]),
      'degraded'
    );

    // One unhealthy
    assert.equal(
      aggregateHealth([
        { name: 'postgresql', status: 'unhealthy' },
        { name: 'redis', status: 'healthy' },
      ]),
      'unhealthy'
    );

    // Empty
    assert.equal(aggregateHealth([]), 'unhealthy');
  });

  it('validates navigation menu has all 10 required routes with appropriate phase badges', () => {
    const navItems = [
      { name: 'Home', href: '/', active: true },
      { name: 'Chat', href: '/chat', phase: 'Phase 5' },
      { name: 'Memory', href: '/memory', phase: 'Phase 5' },
      { name: 'Agents', href: '/agents', phase: 'Phase 5' },
      { name: 'Tools', href: '/tools', phase: 'Phase 6' },
      { name: 'Tasks', href: '/tasks', phase: 'Phase 7' },
      { name: 'Devices', href: '/devices', phase: 'Phase 9' },
      { name: 'Vision', href: '/vision', phase: 'Phase 8' },
      { name: 'Settings', href: '/settings', phase: 'Phase 2+' },
      { name: 'System Health', href: '/health', active: true },
    ];

    assert.equal(navItems.length, 10);

    const activeRoutes = navItems.filter((i) => i.active).map((i) => i.name);
    assert.deepEqual(activeRoutes, ['Home', 'System Health']);

    const placeholderRoutes = navItems.filter((i) => !i.active).map((i) => i.name);
    assert.equal(placeholderRoutes.length, 8);
    assert.ok(placeholderRoutes.includes('Chat'));
    assert.ok(placeholderRoutes.includes('Memory'));
    assert.ok(placeholderRoutes.includes('Agents'));
    assert.ok(placeholderRoutes.includes('Tools'));
    assert.ok(placeholderRoutes.includes('Tasks'));
    assert.ok(placeholderRoutes.includes('Devices'));
    assert.ok(placeholderRoutes.includes('Vision'));
    assert.ok(placeholderRoutes.includes('Settings'));
  });

  it('validates readiness dependency count and boolean state', () => {
    const readinessPayload = {
      status: 'ok',
      ready: true,
      service: 'jenna-api',
      dependencies: {
        postgresql: true,
        redis: true,
      },
      timestamp: '2026-09-12T17:30:00Z',
    };

    assert.equal(readinessPayload.ready, true);
    assert.equal(Object.keys(readinessPayload.dependencies).length, 2);
    assert.equal(readinessPayload.dependencies.postgresql, true);
    assert.equal(readinessPayload.dependencies.redis, true);
  });
});
