import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchMe, login as apiLogin, register as apiRegister } from '@/api/auth'
import { TOKEN_KEY } from '@/api/http'
import type { LoginInput, RegisterInput, UserPublic } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserPublic | null>(null)

  const isAuthenticated = computed(() => token.value !== null)

  function setToken(value: string | null): void {
    token.value = value
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function loadMe(): Promise<UserPublic | null> {
    if (!token.value) {
      user.value = null
      return null
    }
    const me = await fetchMe()
    user.value = me
    return me
  }

  async function login(payload: LoginInput): Promise<void> {
    const result = await apiLogin(payload)
    setToken(result.accessToken)
    try {
      await loadMe()
    } catch (err) {
      logout()
      throw err
    }
  }

  async function register(payload: RegisterInput): Promise<void> {
    await apiRegister(payload)
    await login({ username: payload.username, password: payload.password })
  }

  function logout(): void {
    setToken(null)
    user.value = null
  }

  return { token, user, isAuthenticated, login, register, logout, loadMe, setToken }
})
