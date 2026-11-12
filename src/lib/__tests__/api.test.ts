import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  fetchCurrentUser,
  getApiAuthToken,
  resolveApiBaseUrl,
  setApiAuthToken,
} from '../api';

describe('API base URL resolution', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiAuthToken(null);
  });

  it('uses the desktop launcher port from the page query', () => {
    expect(resolveApiBaseUrl('?api_port=43127')).toBe('http://127.0.0.1:43127');
  });

  it('prefers an explicitly configured API URL', () => {
    expect(resolveApiBaseUrl('?api_port=43127', 'https://api.example.test/')).toBe(
      'https://api.example.test',
    );
  });

  it('falls back to the development API URL for invalid ports', () => {
    expect(resolveApiBaseUrl('?api_port=70000')).toBe('http://localhost:8000');
    expect(resolveApiBaseUrl('')).toBe('http://localhost:8000');
  });

  it('attaches the in-memory bearer token to authenticated requests', async () => {
    const user = {
      id: 8,
      username: 'petro-user',
      email: 'petro@example.com',
      full_name: null,
      role: 'user',
      is_active: true,
    };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer test-token');
      return {
        ok: true,
        status: 200,
        json: async () => user,
      } as Response;
    });
    vi.stubGlobal('fetch', fetchMock);
    setApiAuthToken('test-token');

    await expect(fetchCurrentUser()).resolves.toEqual(user);
    expect(getApiAuthToken()).toBe('test-token');
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
