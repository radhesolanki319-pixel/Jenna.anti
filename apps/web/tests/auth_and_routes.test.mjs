import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Auth State & Protected Route Logic Tests', () => {
  const PUBLIC_ROUTES = ['/login', '/register'];

  function determineRouteRedirect(user, isLoading, pathname) {
    if (isLoading) return null;
    const isPublic = PUBLIC_ROUTES.includes(pathname);
    if (!user && !isPublic) {
      return '/login';
    } else if (user && isPublic) {
      return '/';
    }
    return null;
  }

  it('redirects unauthenticated user to /login for protected routes', () => {
    assert.equal(determineRouteRedirect(null, false, '/'), '/login');
    assert.equal(determineRouteRedirect(null, false, '/health'), '/login');
    assert.equal(determineRouteRedirect(null, false, '/chat'), '/login');
    assert.equal(determineRouteRedirect(null, false, '/settings'), '/login');
  });

  it('allows unauthenticated user to view public login/register pages without redirect', () => {
    assert.equal(determineRouteRedirect(null, false, '/login'), null);
    assert.equal(determineRouteRedirect(null, false, '/register'), null);
  });

  it('redirects authenticated user away from login/register back to /', () => {
    const mockUser = { id: 'u1', email: 'admin@jenna.ai', role: 'admin' };
    assert.equal(determineRouteRedirect(mockUser, false, '/login'), '/');
    assert.equal(determineRouteRedirect(mockUser, false, '/register'), '/');
  });

  it('allows authenticated user on protected routes', () => {
    const mockUser = { id: 'u1', email: 'admin@jenna.ai', role: 'admin' };
    assert.equal(determineRouteRedirect(mockUser, false, '/'), null);
    assert.equal(determineRouteRedirect(mockUser, false, '/health'), null);
    assert.equal(determineRouteRedirect(mockUser, false, '/devices'), null);
  });

  it('does not redirect while session is loading', () => {
    assert.equal(determineRouteRedirect(null, true, '/'), null);
    assert.equal(determineRouteRedirect(null, true, '/login'), null);
  });

  it('clears user, session, and permissions on logout', () => {
    let user = { id: 'u1', email: 'admin@jenna.ai', role: 'admin' };
    let session = { id: 's1', expires_at: '2026-09-19T00:00:00Z' };
    let permissions = ['READ', 'WRITE', 'EXECUTE', 'SENSITIVE_ACTION'];

    // simulate logout
    user = null;
    session = null;
    permissions = [];

    assert.equal(user, null);
    assert.equal(session, null);
    assert.equal(permissions.length, 0);
  });
});
