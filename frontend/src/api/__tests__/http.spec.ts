import { AxiosError } from 'axios'
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'

import http, { ApiError, TOKEN_KEY, request, setUnauthorizedHandler } from '@/api/http'

function mockResponse(data: unknown, status: number, config: InternalAxiosRequestConfig): AxiosResponse {
  return { data, status, statusText: String(status), headers: {}, config } as AxiosResponse
}

// axios 1.x only runs `settle` inside the built-in adapters; a custom test adapter
// must reject non-2xx responses itself to reach the error interceptor.
function rejectWithStatus(data: unknown, status: number, config: InternalAxiosRequestConfig): never {
  const response = mockResponse(data, status, config)
  const code = status >= 500 ? AxiosError.ERR_BAD_RESPONSE : AxiosError.ERR_BAD_REQUEST
  throw new AxiosError(`Request failed with status code ${status}`, code, config, undefined, response)
}

afterEach(() => {
  localStorage.clear()
  setUnauthorizedHandler(() => {})
})

describe('http interceptors', () => {
  it('injects Authorization header from stored token', async () => {
    localStorage.setItem(TOKEN_KEY, 'token-abc')
    let capturedHeaders: Record<string, unknown> = {}

    http.defaults.adapter = (async (config) => {
      capturedHeaders = config.headers as Record<string, unknown>
      return mockResponse({ ok: true }, 200, config)
    }) as typeof http.defaults.adapter

    await request.get('/test')

    expect(capturedHeaders.Authorization).toBe('Bearer token-abc')
  })

  it('omits Authorization header when no token stored', async () => {
    let capturedHeaders: Record<string, unknown> = {}

    http.defaults.adapter = (async (config) => {
      capturedHeaders = config.headers as Record<string, unknown>
      return mockResponse({ ok: true }, 200, config)
    }) as typeof http.defaults.adapter

    await request.get('/test')

    expect(capturedHeaders.Authorization).toBeUndefined()
  })

  it('triggers unauthorized handler and throws ApiError on 401', async () => {
    localStorage.setItem(TOKEN_KEY, 'token-abc')
    const handler = vi.fn()
    setUnauthorizedHandler(handler)

    http.defaults.adapter = (async (config) =>
      rejectWithStatus({ error: { code: 'INVALID_TOKEN', message: '登录已过期' } }, 401, config)) as typeof http.defaults.adapter

    await expect(request.get('/test')).rejects.toMatchObject({
      status: 401,
      code: 'INVALID_TOKEN',
      message: '登录已过期',
    } as Partial<ApiError>)
    expect(handler).toHaveBeenCalledOnce()
  })

  it('falls back to a generic message when error body is missing', async () => {
    http.defaults.adapter = (async (config) =>
      rejectWithStatus({}, 500, config)) as typeof http.defaults.adapter

    await expect(request.get('/test')).rejects.toMatchObject({
      status: 500,
      message: '服务器异常，请稍后重试',
    })
  })
})
