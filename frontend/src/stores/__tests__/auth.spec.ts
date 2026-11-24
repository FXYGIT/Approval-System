import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as authApi from '@/api/auth'
import { TOKEN_KEY } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  fetchMe: vi.fn(),
}))

const mocked = vi.mocked(authApi)

const me = { id: 'u1', username: 'alice', displayName: 'Alice', createdAt: '2026-01-01T00:00:00Z' }
const tokenResponse = { accessToken: 'token-1', tokenType: 'Bearer', expiresIn: 3600 }

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('login stores token and loads current user', async () => {
    mocked.login.mockResolvedValue(tokenResponse)
    mocked.fetchMe.mockResolvedValue(me)

    const store = useAuthStore()
    await store.login({ username: 'alice', password: 'secret123' })

    expect(store.token).toBe('token-1')
    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.displayName).toBe('Alice')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('token-1')
  })

  it('login rolls back token when loading user fails', async () => {
    mocked.login.mockResolvedValue(tokenResponse)
    mocked.fetchMe.mockRejectedValue(new Error('boom'))

    const store = useAuthStore()
    await expect(store.login({ username: 'alice', password: 'secret123' })).rejects.toThrow('boom')
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('logout clears token and user', async () => {
    mocked.login.mockResolvedValue(tokenResponse)
    mocked.fetchMe.mockResolvedValue(me)

    const store = useAuthStore()
    await store.login({ username: 'alice', password: 'secret123' })
    store.logout()

    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('register calls register then login to obtain a token', async () => {
    mocked.register.mockResolvedValue(me)
    mocked.login.mockResolvedValue(tokenResponse)
    mocked.fetchMe.mockResolvedValue(me)

    const store = useAuthStore()
    await store.register({ username: 'alice', password: 'secret123', displayName: 'Alice' })

    expect(mocked.register).toHaveBeenCalledWith({
      username: 'alice',
      password: 'secret123',
      displayName: 'Alice',
    })
    expect(mocked.login).toHaveBeenCalledWith({ username: 'alice', password: 'secret123' })
    expect(store.isAuthenticated).toBe(true)
  })
})
