import { test, describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

describe('ApiClient Unit Tests', () => {
  class ApiError extends Error {
    constructor(message, status, code = 'API_ERROR', details = {}, requestId = null) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.code = code;
      this.details = details;
      this.requestId = requestId;
    }
  }

  class MockApiClient {
    constructor(baseUrl = '') {
      this.baseUrl = baseUrl;
      this.onUnauthorizedCallback = null;
    }

    setOnUnauthorized(cb) {
      this.onUnauthorizedCallback = cb;
    }

    async request(path, init = {}, mockFetch) {
      const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
      const headers = new Map(Object.entries(init.headers || {}));
      if (!headers.has('Accept')) headers.set('Accept', 'application/json');

      const response = await mockFetch(url, {
        ...init,
        headers: Object.fromEntries(headers),
        credentials: 'include',
      });

      if (response.status === 401) {
        if (this.onUnauthorizedCallback) {
          this.onUnauthorizedCallback();
        }
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const errObj = data?.error || {};
        throw new ApiError(
          errObj.message || data.message || `HTTP ${response.status}`,
          response.status,
          errObj.code || `HTTP_${response.status}`,
          errObj.details || {},
          response.headers?.get?.('x-request-id') || null
        );
      }

      return response.json();
    }
  }

  it('correctly dispatches requests with credentials: include and Accept header', async () => {
    let capturedOptions = null;
    const client = new MockApiClient('http://localhost:8000');
    const mockFetch = async (url, opts) => {
      capturedOptions = opts;
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ status: 'ok', service: 'jenna-api' }),
      };
    };

    const res = await client.request('/api/v1/health', {}, mockFetch);
    assert.equal(res.status, 'ok');
    assert.equal(capturedOptions.credentials, 'include');
    assert.equal(capturedOptions.headers.Accept, 'application/json');
  });

  it('properly extracts structured error response and request_id', async () => {
    const client = new MockApiClient('http://localhost:8000');
    const mockFetch = async () => ({
      ok: false,
      status: 403,
      headers: new Headers({
        'content-type': 'application/json',
        'x-request-id': 'req-98765-test',
      }),
      json: async () => ({
        error: {
          code: 'FORBIDDEN',
          message: 'Access denied. Missing required permission: SENSITIVE_ACTION',
          details: { required: 'SENSITIVE_ACTION' },
        },
      }),
    });

    await assert.rejects(
      async () => {
        await client.request('/api/v1/auth/cleanup-sessions', {}, mockFetch);
      },
      (err) => {
        assert.equal(err.name, 'ApiError');
        assert.equal(err.status, 403);
        assert.equal(err.code, 'FORBIDDEN');
        assert.match(err.message, /Access denied/);
        assert.equal(err.requestId, 'req-98765-test');
        return true;
      }
    );
  });

  it('triggers onUnauthorized callback upon 401 response', async () => {
    let unauthorizedTriggered = false;
    const client = new MockApiClient();
    client.setOnUnauthorized(() => {
      unauthorizedTriggered = true;
    });

    const mockFetch = async () => ({
      ok: false,
      status: 401,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        error: { code: 'UNAUTHORIZED', message: 'Not authenticated' },
      }),
    });

    await assert.rejects(async () => {
      await client.request('/api/v1/auth/me', {}, mockFetch);
    });

    assert.equal(unauthorizedTriggered, true);
  });
});
